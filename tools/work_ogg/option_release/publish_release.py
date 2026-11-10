"""Publish the authorized description fix as a ZIP-only normal release."""
from pathlib import Path
import os,subprocess,json,urllib.request,urllib.parse,hashlib
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;REPO=WORK.parent/'srwogg-options-patcher'
previous_path=WORK/'option_release/github_publish_state.json';previous=json.loads(previous_path.read_text(encoding='utf8'));completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert completion['passed'] and not completion['experimental']
env=os.environ.copy();env.update(GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=env,timeout=20);credential=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
def request(method,path,body=None,raw=False,mime=None,public=False):
 url=path if path.startswith('https://') else 'https://api.github.com'+path;h={'Accept':'application/vnd.github+json','User-Agent':'OGG-Patch-Release','X-GitHub-Api-Version':'2022-11-28'}
 if not public:h['Authorization']='Bearer '+credential['password']
 if body is not None and not isinstance(body,bytes):body=json.dumps(body).encode('utf8');mime='application/json'
 if mime:h['Content-Type']=mime
 with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=h,method=method),timeout=60) as response:
  b=response.read();return b if raw else json.loads(b) if b else None
base='/repos/'+previous['full_name'];tag='v20261110';assert request('GET',base)['private'] is False
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip();assert request('GET',base+'/commits/main')['sha']==head
for args in [['tag','-a',tag,'-m','Restore typed explanation references for menu and encyclopedia help'],['push','origin',tag]]:
 r=subprocess.run(['git',*args],cwd=REPO,env=env,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
notes=(HERE/'github_release_notes.md').read_text(encoding='utf8')+'\nZIP SHA-256: `'+completion['zip_sha256']+'`\n'
release=request('POST',base+'/releases',{'tag_name':tag,'target_commitish':head,'name':'OG외전 12옵션 패처 v20261110 · 설명 표시 오류 수정','body':notes,'draft':True,'prerelease':False})
state={k:previous[k] for k in ['owner','name','full_name','html_url','clone_url']};state.update(commit=head,private=False,visibility='public',release_id=release['id'],release_url=release['html_url'],release_draft=True,prerelease=False,zip_only_distribution=True)
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
name='SRWOGG_Options_kr_'+tag+'.zip';b=Path(completion['zip']).read_bytes();digest=hashlib.sha256(b).hexdigest();assert digest==completion['zip_sha256'];url=release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':name});asset=request('POST',url,b,mime='application/zip');assert asset['state']=='uploaded' and asset['size']==len(b)
if asset.get('digest'):assert asset['digest']=='sha256:'+digest
print('Uploaded ZIP.',flush=True)
request('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'make_latest':'true'})
public=request('GET',base+'/releases/tags/'+tag,public=True);assert not public['draft'] and not public['prerelease'] and len(public['assets'])==1;asset=public['assets'][0];assert asset['name']==name
assert hashlib.sha256(request('GET',asset['browser_download_url'],raw=True,public=True)).hexdigest()==digest
assert request('GET',base+'/releases/latest',public=True)['tag_name']==tag
old=request('GET',base+'/releases/tags/v20261107.8');notice='> 설명 표시 문제를 수정한 [v20261110]('+public['html_url']+')이 배포되었습니다. 정신기·특수능력·강화파츠·도감 설명 문제는 최신 버전으로 업데이트해 주세요.\n\n';request('PATCH',base+'/releases/'+str(old['id']),{'body':notice+old['body']})
request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 12옵션 패처 · 설명 표시 수정·추가25편성·추가 전장13편'})
state.update(passed=True,release_draft=False,latest_stable_release=public['html_url'],public_access_verified=True,assets=[dict(name=name,bytes=len(b),sha256=digest,url=asset['browser_download_url'],public_download_verified=True)])
for path in [HERE/'github_publish_state.json',previous_path]:path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(state,ensure_ascii=False,indent=2),flush=True)
