"""Publish the authorized ZIP-only normal release, then verify public bytes."""
from pathlib import Path
import os,subprocess,json,urllib.request,urllib.parse,hashlib,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parent/'srwogg-options-patcher'
previous_path=ROOT/'option_release/github_publish_state.json';previous=json.loads(previous_path.read_text(encoding='utf8'))
completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));audit=json.loads((HERE/'source_distribution_audit.json').read_text(encoding='utf8'))
assert completion['passed'] and audit['passed'] and completion['options']==13 and completion['verified_profiles']==8192
assert json.loads((ROOT/'linear_route_journal.json').read_text(encoding='utf8'))['after_sha256']==completion['canonical_sha256']
env=os.environ.copy();env.update(GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=env,timeout=20)
credential=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
def request(method,path,body=None,raw=False,mime=None,public=False):
    url=path if path.startswith('https://') else 'https://api.github.com'+path
    headers={'Accept':'application/vnd.github+json','User-Agent':'OGG-Patch-Release','X-GitHub-Api-Version':'2022-11-28'}
    if not public:headers['Authorization']='Bearer '+credential['password']
    if body is not None and not isinstance(body,bytes):body=json.dumps(body).encode('utf8');mime='application/json'
    if mime:headers['Content-Type']=mime
    with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=60) as response:
        b=response.read();return b if raw else json.loads(b) if b else None
base='/repos/'+previous['full_name'];tag='v20261121.1';assert request('GET',base)['private'] is False
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip()
assert request('GET',base+'/commits/main')['sha']==head
for args in [['tag','-a',tag,'-m','Require added cast for civil-war campaign'],['push','origin',tag]]:
    r=subprocess.run(['git',*args],cwd=REPO,env=env,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
notes=(HERE/'github_release_notes.md').read_text(encoding='utf8')+'\nZIP SHA-256: `'+completion['zip_sha256']+'`\n'
release=request('POST',base+'/releases',{'tag_name':tag,'target_commitish':head,'name':'OG외전 13옵션 패처 v20261121.1 · 시빌워 의존 조건','body':notes,'draft':True,'prerelease':False})
state={k:previous[k] for k in ['owner','name','full_name','html_url','clone_url']};state.update(commit=head,private=False,release_id=release['id'],release_draft=True,prerelease=False,zip_only_distribution=True)
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
name='SRWOGG_Options_kr_'+tag+'.zip';data=Path(completion['zip']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==completion['zip_sha256']
asset=request('POST',release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':name}),data,mime='application/zip');assert asset['state']=='uploaded' and asset['size']==len(data)
if asset.get('digest'):assert asset['digest']=='sha256:'+digest
print('Uploaded ZIP.',flush=True)
request('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'make_latest':'true'})
public=request('GET',base+'/releases/tags/'+tag,public=True);assert not public['draft'] and not public['prerelease'] and len(public['assets'])==1
asset=public['assets'][0];assert asset['name']==name
for attempt in range(3):
    try:
        assert hashlib.sha256(request('GET',asset['browser_download_url'],raw=True,public=True)).hexdigest()==digest
        break
    except Exception:
        if attempt==2:raise
        time.sleep(2)
assert request('GET',base+'/releases/latest',public=True)['tag_name']==tag
old=request('GET',base+'/releases/tags/v20261121');notice='> 시빌워의 추가 아군 의존 조건을 적용한 [최신 v20261121.1]('+public['html_url']+')이 배포되었습니다.\n\n'
request('PATCH',base+'/releases/'+str(old['id']),{'body':notice+old['body']})
request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 13옵션 패처 · 지상·우주 교차 진행·추가25편성·추가 전장13편'})
state.update(passed=True,release_draft=False,release_url=public['html_url'],latest_stable_release=public['html_url'],public_access_verified=True,assets=[dict(name=name,bytes=len(data),sha256=digest,url=asset['browser_download_url'],public_download_verified=True)])
for p in [HERE/'github_publish_state.json',previous_path]:p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(state,ensure_ascii=False,indent=2),flush=True)
