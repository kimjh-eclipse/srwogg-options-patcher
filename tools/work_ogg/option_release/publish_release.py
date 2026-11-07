"""Update the existing release labels and ZIP, preserving its tag."""
from pathlib import Path
import os, subprocess, json, urllib.request, urllib.parse, hashlib
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;REPO=WORK.parent/'srwogg-options-patcher'
state_path=HERE/'github_publish_state.json';state=json.loads(state_path.read_text(encoding='utf8'));completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert completion['passed'] and not completion['experimental']
env=os.environ.copy();env.update(GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0')
auth=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=env,timeout=20);credential=dict(line.split('=',1) for line in auth.stdout.splitlines() if '=' in line)
def request(method,path,body=None,raw=False,mime=None,public=False):
 url=path if path.startswith('https://') else 'https://api.github.com'+path;headers={'Accept':'application/vnd.github+json','User-Agent':'OGG-Patch-Release','X-GitHub-Api-Version':'2022-11-28'}
 if not public:headers['Authorization']='Bearer '+credential['password']
 if body is not None and not isinstance(body,bytes):body=json.dumps(body).encode('utf8');mime='application/json'
 if mime:headers['Content-Type']=mime
 with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=60) as response:
  data=response.read();return data if raw else json.loads(data) if data else None
base='/repos/'+state['full_name'];tag='v20261107.8';release=request('GET',base+'/releases/tags/'+tag)
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip();assert request('GET',base+'/commits/main')['sha']==head
name='SRWOGG_Options_kr_'+tag+'.zip';data=Path(completion['zip']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==completion['zip_sha256']
old=next(a for a in release['assets'] if a['name']==name);temporary=name.removesuffix('.zip')+'_replacement.zip';upload_url=release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':temporary})
asset=request('POST',upload_url,data,mime='application/zip');assert asset['state']=='uploaded' and asset['size']==len(data)
assert hashlib.sha256(request('GET',asset['browser_download_url'],raw=True,public=True)).hexdigest()==digest
request('PATCH',base+'/releases/assets/'+str(old['id']),{'name':name+'.previous'});asset=request('PATCH',base+'/releases/assets/'+str(asset['id']),{'name':name});request('DELETE',base+'/releases/assets/'+str(old['id']))
notes=(HERE/'github_release_notes.md').read_text(encoding='utf8')+'\n표기 수정 소스: ['+head[:7]+'](https://github.com/'+state['full_name']+'/commit/'+head+')\n\nZIP SHA-256: `'+digest+'`\n'
request('PATCH',base+'/releases/'+str(release['id']),{'name':'OG외전 12옵션 패처 v20261107.8 · 시빌워7부작·레벨52','body':notes,'prerelease':False,'make_latest':'true'})
public=request('GET',base+'/releases/tags/'+tag,public=True);assert not public['prerelease'] and not public['draft'] and len(public['assets'])==1
asset=public['assets'][0];assert asset['name']==name and hashlib.sha256(request('GET',asset['browser_download_url'],raw=True,public=True)).hexdigest()==digest
assert request('GET',base+'/releases/latest',public=True)['tag_name']==tag
request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 12옵션 패처 · 추가 전장13편·시빌워7부작·레벨52'})
state.update(commit=head,release_draft=False,prerelease=False,latest_stable_release=public['html_url'],public_access_verified=True,passed=True,release_label_revision=True,assets=[dict(name=name,bytes=len(data),sha256=digest,url=asset['browser_download_url'],public_download_verified=True)])
for path in [state_path,WORK/'option_release/github_publish_state.json']:path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Updated release labels and ZIP; public download verified; tag preserved.')
