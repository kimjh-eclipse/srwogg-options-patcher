from pathlib import Path
import os,subprocess,json,urllib.request,urllib.parse,hashlib
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
REPO=WORK.parent/'srwogg-options-patcher'
previous_path=WORK/'option_release/github_publish_state.json'
previous=json.loads(previous_path.read_text(encoding='utf-8'))
completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf-8'))
env=os.environ.copy();env.update(GCM_INTERACTIVE='Never',GIT_TERMINAL_PROMPT='0')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=env,timeout=20)
credential=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
headers={'Authorization':'Bearer '+credential['password'],'Accept':'application/vnd.github+json','User-Agent':'OGG-Patch-Release','X-GitHub-Api-Version':'2022-11-28'}
def request(method,path,body=None,raw=False,extra=None,public=False):
 url=path if path.startswith('https://') else 'https://api.github.com'+path;h=dict(headers)
 if public:h.pop('Authorization')
 if extra:h.update(extra)
 data=body
 if body is not None and not isinstance(body,bytes):data=json.dumps(body).encode('utf-8');h['Content-Type']='application/json'
 req=urllib.request.Request(url,data=data,headers=h,method=method)
 with urllib.request.urlopen(req,timeout=60) as response:return response.read() if raw else json.load(response)

base='/repos/'+previous['full_name'];tag='v20261107.1'
repo=request('GET',base);assert repo['private'] is False
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip()
assert request('GET',base+'/commits/main')['sha']==head
notes='휴케바인 **Mk-Ⅲ 타입 R의 3화 조기 입수**를 추가하고, 기본 장착 무장 **공격력 +200**을 별도 옵션으로 넣었습니다. 이어서 기존 추가 시나리오의 대사 17개를 다듬었습니다.\n\n## 휴케바인 R\n\n- 10번 조기 입수: 3화에서 기체만 1기를 지급합니다. 파일럿 추가·강제 탑승은 없습니다. 기존 빌트팔켄 L·아슈세이버 각 1기와 환장 무장 2종 지급도 유지합니다.\n- 새 11번 옵션: 타입 R의 기본 장착 무장 5종 공격력 +200. 발칸포 1,200→1,400, 멀티트레이스미사일 2,800→3,000, 팡 슬래셔 3,700→3,900, 그라비톤 라이플 4,300→4,500, 로슈세이버 3,000→3,200.\n- 원래 공유 무장을 전역 수정하지 않고 타입 R용 데이터를 사용합니다. 다른 기체의 기존 무장·기체 능력치·사거리·EN·탄수·연출·개조비·개조 상승량은 유지합니다.\n\n[상세 변경과 세이브 안내](https://github.com/kimjh-eclipse/srwogg-options-patcher/blob/v20261107.1/docs/huckebein-R-v20261107.1.md)\n\n## 대사 다듬기\n\n25·29·31·32·36화의 기존 추가 대사 17개를 수정했습니다. 잉그램과 SRX팀의 경계심은 지키면서 설명조 표현을 줄이고, 오우카 일행이 폴카의 슬픔을 받아들이는 대화와 종전 뒤의 약속을 자연스럽게 연결했습니다. 레몬·액셀렌의 자매 인연, 원작의 사건 순서·결말, 합류 일정·플래그·대사 이력은 유지합니다.\n\n[현재 추가 대사와 수정 범위](https://github.com/kimjh-eclipse/srwogg-options-patcher/blob/v20261107.1/docs/followup-story-v20261107.1.md)\n\n## 사용과 확인 범위\n\n총 **11개 옵션·2,048개 조합**, 기본값은 모두 꺼짐입니다. 이전 v20261107의 1,024개 적용 조합도 선택값을 유지하며 인식하고 새 무장 +200은 꺼짐으로 표시합니다. `SRWOGG_Options_kr_v20261107.1.zip`의 EXE·BIN을 함께 사용하세요. PCSX2를 완전히 종료하고 적용한 뒤 새로 부팅하세요.\n\n타입 R 조기 지급은 3화 이벤트 이전 일반 세이브부터 진행해야 합니다. 이전 버전에서 그 지급 이벤트를 이미 봤다면 추가 기체가 소급 지급되지는 않습니다. 복원 기록은 `.v20261107.1.oggbak`입니다.\n\n기체만 지급, 기존 보유 기체 보존, 반복 및 저장 데이터 복원 후 중복 방지, 실제 게임 공격력 조회와 옵션 조합을 확인했습니다. 수정 대사는 문자열·이력 조회 34건을 추가 확인했습니다. PCSX2 플레이 테스트는 사용자가 진행합니다. 이번 버전에 전체 ISO를 2,048번 반복 적용하는 검사는 하지 않았습니다. 게임 ISO·BIOS·메모리 덤프·세이브와 원본 한글패치는 첨부하지 않습니다.\n\n## 공식 한글패치 다운로드\n\n공식 v1.4.3s를 먼저 적용한 뒤 추가 패처를 사용하세요.\n\n- [공식 한글패치 릴리즈](https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG)\n- [OGGv1.4.3sta.7z 직접 다운로드](https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z)\n- [제작자 저장소·적용 안내](https://github.com/z3oo3z/PS2-SRWOGG-KPatch)\n'+'\nZIP SHA-256: `'+completion['zip_sha256']+'`\n'
(HERE/'github_release_notes.md').write_text(notes,encoding='utf-8')
for args in [['tag','-a',tag,'-m','Add early Huckebein R and optional weapon power; refine dialogue'],['push','origin',tag]]:
 r=subprocess.run(['git',*args],cwd=REPO,env=env,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
release=request('POST',base+'/releases',{'tag_name':tag,'target_commitish':head,'name':'OG외전 11옵션 패처 v20261107.1 · 휴케바인 R·대사 다듬기','body':notes,'draft':True,'prerelease':False})
state={'owner':previous['owner'],'name':previous['name'],'full_name':previous['full_name'],'html_url':repo['html_url'],'clone_url':repo['clone_url'],'private':False,'visibility':'public','commit':head,'release_id':release['id'],'release_url':release['html_url'],'tag':tag,'release_draft':True}
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
assets=[('SRWOGG_Options_kr_v20261107.1.zip',Path(completion['zip']),'application/zip'),('README-ko.txt',WORK/'release_v20261107.1/읽어주세요.txt','text/plain; charset=utf-8'),('validation-v20261107.1.json',WORK/'release_v20261107.1/검증결과.json','application/json')]
checksum=HERE/'release_asset_SHA256SUMS.txt';checksum.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p,t in assets),encoding='ascii')
assets.append(('SHA256SUMS.txt',checksum,'text/plain'));uploaded=[]
for name,path,mime in assets:
 data=path.read_bytes();url=release['upload_url'].split('{')[0]+'?'+urllib.parse.urlencode({'name':name})
 asset=request('POST',url,data,extra={'Content-Type':mime});assert asset['state']=='uploaded' and asset['size']==len(data)
 downloaded=request('GET',base+'/releases/assets/'+str(asset['id']),raw=True,extra={'Accept':'application/octet-stream'})
 digest=hashlib.sha256(data).hexdigest();assert hashlib.sha256(downloaded).hexdigest()==digest
 uploaded.append({'name':name,'bytes':len(data),'sha256':digest,'download_verified':True})
 print('Uploaded and verified:',name,flush=True)
release=request('PATCH',base+'/releases/'+str(release['id']),{'draft':False,'make_latest':'true'})
public=request('GET',base+'/releases/tags/'+tag,public=True);assert not public['draft'] and len(public['assets'])==4
for asset in uploaded:
 remote=next(a for a in public['assets'] if a['name']==asset['name']);asset['url']=remote['browser_download_url']
 downloaded=request('GET',asset['url'],raw=True,public=True)
 assert hashlib.sha256(downloaded).hexdigest()==asset['sha256'];asset['public_download_verified']=True
old=request('GET',base+'/releases/tags/v20261107')
notice='현재 최신 버전은 [v20261107.1](https://github.com/'+previous['full_name']+'/releases/tag/'+tag+')입니다. 휴케바인 R 조기 입수·무장 +200과 대사 다듬기를 추가했습니다.\n\n---\n\n'
request('PATCH',base+'/releases/'+str(old['id']),{'name':'[이전 버전] OG외전 10옵션 패처 v20261107','body':notice+(old['body'] or '')})
request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 11옵션 Windows 패처 · 시나리오·밸런스 제작 및 검증 소스'})
assert request('GET',base+'/releases/latest',public=True)['tag_name']==tag
state.update(release_draft=False,release_url=public['html_url'],assets=uploaded,public_access_verified=True,passed=True)
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
previous_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(state,ensure_ascii=False,indent=2),flush=True)
