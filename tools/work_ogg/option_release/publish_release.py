"""Publish the authorized experimental release, preserving the latest stable."""
from pathlib import Path
import os,subprocess,json,urllib.request,urllib.parse,urllib.error,hashlib
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;REPO=WORK.parent/'srwogg-options-patcher'
previous_path=WORK/'option_release/github_publish_state.json';previous=json.loads(previous_path.read_text(encoding='utf8'));completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert completion['passed'] and completion['experimental']
env=os.environ.copy();env.update(GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=env,timeout=20);credential=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
headers={'Authorization':'Bearer '+credential['password'],'Accept':'application/vnd.github+json','User-Agent':'OGG-Patch-Release','X-GitHub-Api-Version':'2022-11-28'}
def request(method,path,body=None,raw=False,extra=None,public=False):
 url=path if path.startswith('https://') else 'https://api.github.com'+path;h=dict(headers)
 if public:h.pop('Authorization')
 if extra:h.update(extra)
 data=body
 if body is not None and not isinstance(body,bytes):data=json.dumps(body).encode('utf8');h['Content-Type']='application/json'
 req=urllib.request.Request(url,data=data,headers=h,method=method)
 with urllib.request.urlopen(req,timeout=60) as response:return response.read() if raw else json.load(response)
base='/repos/'+previous['full_name'];tag='v20261107.3';repo=request('GET',base);assert repo['private'] is False;stable=request('GET',base+'/releases/latest',public=True)
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip();assert request('GET',base+'/commits/main')['sha']==head
notes=(HERE/'github_release_notes.md').read_text(encoding='utf8')+'\nZIP SHA-256: `'+completion['zip_sha256']+'`\n'
for args in [['tag','-a',tag,'-m','Add ten unmanned regional bosses and repair deployment terrain'],['push','origin',tag]]:
 r=subprocess.run(['git',*args],cwd=REPO,env=env,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
release=request('POST',base+'/releases',{'tag_name':tag,'target_commitish':head,'name':'OG외전 12옵션 패처 v20261107.3 · 무인 보스10기 시험판','body':notes,'draft':True,'prerelease':True})
state={k:previous[k] for k in ['owner','name','full_name','html_url','clone_url']};state.update(private=False,visibility='public',commit=head,release_id=release['id'],release_url=release['html_url'],release_draft=True,prerelease=True,zip_only_distribution=True,latest_stable_release=stable['html_url']);(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
files=[(Path(completion['zip']),'SRWOGG_Options_kr_v20261107.3.zip','application/zip')]
uploaded=[]  # The complete ZIP contains the executable, data and checksums.
for path,name,mime in files:
 data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();url=release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':name});asset=request('POST',url,data,extra={'Content-Type':mime});assert asset['state']=='uploaded' and asset['size']==len(data)
 if asset.get('digest'):assert asset['digest']=='sha256:'+digest
 uploaded.append(dict(name=name,bytes=len(data),sha256=digest));print('Uploaded:',name,flush=True)
release=request('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'make_latest':'false'});public=request('GET',base+'/releases/tags/'+tag,public=True);assert public['prerelease'] and not public['draft'] and len(public['assets'])==1
for asset in uploaded:
 remote=next(a for a in public['assets'] if a['name']==asset['name']);asset['url']=remote['browser_download_url'];downloaded=request('GET',asset['url'],raw=True,public=True);assert hashlib.sha256(downloaded).hexdigest()==asset['sha256'];asset['public_download_verified']=True;print('Verified public download:',asset['name'],flush=True)
assert request('GET',base+'/releases/latest',public=True)['tag_name']==stable['tag_name'];request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 옵션 패처 · 12옵션 무인 보스10기 시험판 / 11옵션 안정판'})
state.update(release_draft=False,release_url=public['html_url'],assets=uploaded,public_access_verified=True,passed=True);(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');previous_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(state,ensure_ascii=False,indent=2),flush=True)
