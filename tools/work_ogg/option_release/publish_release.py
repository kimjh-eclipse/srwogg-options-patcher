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

base='/repos/'+previous['full_name'];tag='v20261107'
repo=request('GET',base);assert repo['private'] is False
head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout.strip()
assert request('GET',base+'/commits/main')['sha']==head
notes='합류 이후 관계를 이어가는 **후속 장면 5개·대사 73개**를 기존 1번 시나리오 옵션에 추가했습니다. 10개 옵션·1,024가지 조합과 모두 꺼짐 기본값을 유지합니다.\n\n## 추가 장면\n\n| 화 | 내용 |\n| --- | --- |\n| 25 | 잉그램과 SRX팀의 신뢰 회복 조건, 오우카가 돌봄을 받는 법 |\n| 29 | 비안·류네의 서로 다른 시간, 라미아의 자율성과 레몬·액셀렌의 자매 인연 |\n| 31 | 빈델·웬드로의 조건부 공투와 책임 |\n| 32 | 알티스의 죽음 뒤 이동 중 통신, 돌아온 사람이 약속할 수 없는 것 |\n| 36 | 증언·조사와 다음 만남을 남기는 작별 |\n\n공투를 즉각적인 용서로 연결하지 않습니다. 이쪽 액셀렌을 죽은 동생의 대체품으로 삼지 않으면서 레몬과의 자매 인연을 이어갑니다. 원작의 죽음과 마지막 대사는 유지합니다. 이번 변경은 대사 보강으로, 합류 일정·기체·파일럿 능력치·무장·보상은 바뀌지 않습니다. 29화 관계 장면과 9번 정비 안내는 독립 동작합니다.\n\n[장면별 대사와 적용 안내](https://github.com/kimjh-eclipse/srwogg-options-patcher/blob/v20261107/docs/followup-story-v20261107.md)를 ZIP에도 넣었습니다.\n\n## 새 10번 옵션: 3화 기체·무장 조기 입수\n\n빌트팔켄 타입 L·아슈세이버 각각 1기, 그라비톤 런처·G 임팩트 스테이크 각각 1개를 지급합니다. 파일럿 추가나 강제 탑승은 없으며 원래 기체 성능·기본 무장을 사용합니다. 시나리오 및 기존 8종 보급과 독립 동작하고 반복 지급을 방지합니다. 이미 보유한 동일 기체를 복제하거나 육성·개조를 초기화하지 않습니다. 해당 3화 이벤트 이전 세이브부터 진행하세요.\n\n## 공식 한글패치 다운로드\n\n먼저 아래 공식 한글패치를 적용한 뒤 추가 패처를 사용하세요.\n\n- [공식 한글패치 v1.4.3s 다운로드 페이지](https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG)\n- [공식 패치 OGGv1.4.3sta.7z 직접 다운로드](https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z)\n- [제작자 저장소·적용 안내](https://github.com/z3oo3z/PS2-SRWOGG-KPatch)\n\n## 사용·확인 범위\n\n`SRWOGG_Options_kr_v20261107.zip`을 풀고 `patcher` 폴더의 EXE·BIN을 함께 사용하세요. PCSX2 종료 → ISO 선택 → 검사 → 옵션 선택 → 패치 적용 후 새로 부팅하세요. 복원 기록은 `.v20261107.oggbak`입니다. 해당 이벤트 이전 일반 세이브부터 진행해야 하며, 지난 이벤트는 소급 재생되지 않습니다. 기존 v20261106.5의 지원 장비·정비 선택도 유지하여 인식합니다.\n\n새 대사 문자열·이력의 실제 게임 루틴 조회 146건, 이력 항목 2,267개, 새 장면 1회 실행·반복·영구 저장 데이터 복원 후 중복 방지를 확인했습니다. 1,024개 조합을 메모리에서 합성하여 새 장면 선택·해제 5,120건과 기존 옵션 보존을 확인했습니다. 패처 자체 검사, 이전 버전 프로필 인식, 원본과 현재 시험 ISO의 읽기 전용 검사도 통과했습니다.\n\n이번 버전에서는 1,024개 조합을 ISO에 반복 쓰는 검사를 하지 않았습니다. **PCSX2 플레이 테스트는 사용자가 진행합니다.** 저장 데이터 복원은 VM 검사이며 실제 메모리카드 I/O나 전편 플레이 검증이 아닙니다. 게임 ISO·BIOS·RAM 덤프·세이브와 제작자 원본 한글패치는 첨부하지 않습니다.\n'+'\nZIP SHA-256: `'+completion['zip_sha256']+'`\n'
(HERE/'github_release_notes.md').write_text(notes,encoding='utf-8')
for args in [['tag','-a',tag,'-m','Expand post-recruitment character follow-up scenes'],['push','origin',tag]]:
 r=subprocess.run(['git',*args],cwd=REPO,env=env,capture_output=True,text=True,timeout=90);assert r.returncode==0,r.stderr
release=request('POST',base+'/releases',{'tag_name':tag,'target_commitish':head,'name':'OG외전 10옵션 패처 v20261107 · 후속 시나리오·초반 장비','body':notes,'draft':True,'prerelease':False})
state={'owner':previous['owner'],'name':previous['name'],'full_name':previous['full_name'],'html_url':repo['html_url'],'clone_url':repo['clone_url'],'private':False,'visibility':'public','commit':head,'release_id':release['id'],'release_url':release['html_url'],'tag':tag,'release_draft':True}
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
assets=[('SRWOGG_Options_kr_v20261107.zip',Path(completion['zip']),'application/zip'),('README-ko.txt',WORK/'release_v20261107/읽어주세요.txt','text/plain; charset=utf-8'),('validation-v20261107.json',WORK/'release_v20261107/검증결과.json','application/json')]
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
old=request('GET',base+'/releases/tags/v20261106.5')
notice='현재 최신 버전은 [v20261107](https://github.com/'+previous['full_name']+'/releases/tag/'+tag+')입니다. 합류 이후 관계 장면 5개·대사 73개를 보강했습니다.\n\n---\n\n'
request('PATCH',base+'/releases/'+str(old['id']),{'name':'[이전 버전] OG외전 9옵션 패처 v20261106.5','body':notice+(old['body'] or '')})
request('PATCH',base,{'description':'OG외전 공식 한글패치 기반 10옵션 Windows 패처 · 시나리오·밸런스 제작 및 검증 소스'})
assert request('GET',base+'/releases/latest',public=True)['tag_name']==tag
state.update(release_draft=False,release_url=public['html_url'],assets=uploaded,public_access_verified=True,passed=True)
(HERE/'github_publish_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
previous_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(state,ensure_ascii=False,indent=2),flush=True)
