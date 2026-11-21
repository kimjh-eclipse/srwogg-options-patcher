from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parent/'srwogg-options-patcher';VERSION='v20261121.1';DIST=ROOT/('release_'+VERSION)
meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'));done=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert done['passed']
tools=REPO/'tools/work_ogg/option_civil_dependency';tools.mkdir(exist_ok=True)
for p in HERE.iterdir():
    if p.suffix in ['.py','.md'] and '.generated.' not in p.name:shutil.copy2(p,tools/p.name)
for src,dst in [('시빌워_의존조건.md','civil-dependency-v20261121.1.md'),('지상우주_교차진행.md','linear-route-v20261121.1.md'),('시빌워_편성과증원.md','civil-formations-v20261121.1.md'),('시빌워7부작_대사와편성.md','civil-war-v20261121.1.md'),('검증결과.json','validation-v20261121.1.json')]:shutil.copy2(DIST/src,REPO/'docs'/dst)
shutil.copy2(DIST/'읽어주세요.txt',REPO/'docs/사용안내.txt')
(REPO/'patch-data.json').write_text(json.dumps(dict(version=VERSION,file='OGG_options.bin',sha256=meta['pack_sha256'],bytes=meta['pack_size'],options=13,profiles=8192,format_version=2,prerelease=False,distribution='zip-only',release_zip_sha256=done['zip_sha256'],civil_war_requires_options=[1,12]),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=REPO/'README.md';s=p.read_text(encoding='utf8')
s=s.replace('v20261121은 지상·우주 루트를 교차하여 모두 진행하는 독립 옵션을 추가했습니다.','v20261121.1은 시빌워에 1번 추가 아군 의존 조건을 적용했습니다. 지상·우주 교차 진행도 유지합니다.')
s=s.replace('/download/v20261121/','/download/v20261121.1/').replace('_v20261121.zip','_v20261121.1.zip')
point=s.index('## 지상·우주 루트 교차 진행')
if '## 시빌워 의존 조건' not in s:
    intro='''## 시빌워 의존 조건

**시빌워7편과 정치 사전 장면5개는 1번 추가 아군과 12번 추가 전장을 함께 켜야 진행합니다.** 12번만 켜면 국지전5편·베오울프전1편 후 본편 라그나로크로 이어지며, 시빌워용 임시 편성 분리도 실행하지 않습니다. 패처는 1번을 자동으로 선택하지 않습니다.

1번은 새 게임부터 유지해야 합니다. 뒤늦게 켜도 지나간 합류가 소급되지 않습니다. 12번은 원본34화 종료 이전부터 유지하고, 이미 시빌워에 진입한 상태에서 1·12번을 바꾸지 마세요. 1번 OFF 사용자는 정치 사전 장면 이전의 일반 세이브부터 새 버전을 사용해 주세요. [의존 조건·적용 방법](docs/civil-dependency-v20261121.1.md)을 확인하세요.

'''
    s=s[:point]+intro+s[point:]
start=s.index('| 추가 아군 1번 |') if '| 추가 아군 1번 |' in s else s.index('| 추가 전장 12번 |')
end=s.index('\n\n',start)
s=s[:start]+'''| 추가 아군 1번 | 추가 전장 12번 | 교차 진행 13번 | 전체 화수 |
|---|---|---|---|
| 무관 | 끔 | 끔 | 36 |
| 무관 | 끔 | 켬 | 41 |
| 끔 | 켬 | 끔 | 42 |
| 끔 | 켬 | 켬 | 47 |
| 켬 | 켬 | 끔 | 49 |
| 켬 | 켬 | 켬 | 54 |'''+s[end:]
s=s.replace('12·13번을 함께 켜면 원본 34화','1·12·13번을 함께 켜면 원본 34화')
s=s.replace('기존12번 추가 전장 옵션에 포함합니다.','1·12번을 함께 켜야 진행합니다.')
s=s.replace('**기존12번 옵션 하나**로 국지전5편·베오울프전1편·시빌워7편을 함께 선택합니다.','**12번으로 국지전5편·베오울프전1편을 선택하고, 1번도 켜면 시빌워7편이 추가됩니다.**')
s=s.replace('아래 기존 전장 소개의 화수는 13번 OFF 기준입니다.','아래 시빌워 포함 전장 소개의 화수는 1·12번 ON·13번 OFF 기준입니다.')
s=s.replace('docs/linear-route-v20261121.md','docs/linear-route-v20261121.1.md').replace('docs/validation-v20261121.json','docs/validation-v20261121.1.json')
s=s.replace('docs/civil-formations-v20261121.md','docs/civil-formations-v20261121.1.md').replace('docs/civil-war-v20261121.md','docs/civil-war-v20261121.1.md')
p.write_text(s,encoding='utf8')
p=REPO/'tools/README.md';s=p.read_text(encoding='utf8')
if '## v20261121.1 시빌워 의존 조건' not in s:s+='''

## v20261121.1 시빌워 의존 조건

현재 수정 제작 경로는 `work_ogg/option_civil_dependency`입니다. OGGOPT01 형식2는 일반 옵션 뒤에 require/forbid 비트 조건과 후처리 편집을 기록합니다. C# Compose와 Python Pack은 같은 조건을 적용하며, 형식1의 읽기도 유지합니다. 1번 OFF·12번 ON일 때만 정치 사전 장면5블록(임시 편성 분리 포함)을 native8A로 생략하고, 베오울프 종료 다음 화를 원본 최종전 인덱스34로, 최종화의 기준 표시를42로 바꿉니다. 13번의+5표시는 그대로 적용되어47화가 됩니다. 논리 인덱스·원래 전장 배치·전투 수치는 유지합니다.

기존 v20261121 전체8192프로필을 이전 입력으로 인식하며,6144프로필은 바이트가 같습니다. 모든 옵션을 켠 작업용 ISO도 동일합니다. 공개 소스 빌드는 루트 `build.ps1`에서 최신 릴리즈 BIN을 지정합니다. 로컬 제작/검증에는 이전 릴리즈와 사용자의 비공개 ISO·분석 자료가 필요합니다. 게임 덤프는 포함하지 않습니다. 이전 제작 스크립트를 현재 ISO에 재적용하지 마세요.
'''
p.write_text(s,encoding='utf8')
print('Synchronized dependency source and release guides.',flush=True)
