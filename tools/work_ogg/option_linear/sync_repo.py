from pathlib import Path
import shutil,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parent/'srwogg-options-patcher';DIST=ROOT/'release_v20261121'
completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'));assert completion['passed']
shutil.copy2(HERE/'OggOptionsPatcher.cs',REPO/'src/OggOptionsPatcher.cs')
tools=REPO/'tools/work_ogg/option_linear';tools.mkdir(exist_ok=True)
for p in HERE.iterdir():
    if p.suffix in ['.py','.md'] and '.generated.' not in p.name and p.name not in ['restore_authoring_iteration.py','prepare_cafe.py']:shutil.copy2(p,tools/p.name)
for name in ['restore_authoring_iteration.py','prepare_cafe.py']:
    if (tools/name).exists():(tools/name).unlink()
for name in ['linear_route_policy.py','prepare_linear_route.py','apply_linear_route.py']:shutil.copy2(ROOT/name,REPO/'tools/work_ogg'/name)
for src,dst in [('지상우주_교차진행.md','linear-route-v20261121.md'),('시빌워_편성과증원.md','civil-formations-v20261121.md'),('시빌워7부작_대사와편성.md','civil-war-v20261121.md'),('추가전장_전후대사.md','intermission-six-v20261121.md'),('베오울프전_변경내역.md','beowulf-stage-v20261121.md'),('국지전5편_시나리오.md','regional-five-v20261121.md'),('설명표시_수정내역.md','help-text-fix-v20261121.md'),('PATCH_INFO.json','patch-info-v20261121.json'),('검증결과.json','validation-v20261121.json'),('읽어주세요.txt','사용안내.txt')]:shutil.copy2(DIST/src,REPO/'docs'/dst)
(REPO/'patch-data.json').write_text(json.dumps(dict(version='v20261121',file='OGG_options.bin',sha256=meta['pack_sha256'],bytes=meta['pack_size'],options=13,profiles=8192,prerelease=False,distribution='zip-only',release_zip_sha256=completion['zip_sha256']),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=REPO/'README.md';old=p.read_text(encoding='utf8');lines=old.splitlines();lines[2]='공식 한글패치 기반 Windows **13옵션 패처**입니다. v20261121은 지상·우주 루트를 교차하여 모두 진행하는 독립 옵션을 추가했습니다. 기존 추가 25편성과 추가 전장 13편, 설명 오류 수정을 유지합니다.'
s='\n'.join(lines)+'\n';s=s.replace('/v20261110/','/v20261121/').replace('_v20261110.zip','_v20261121.zip').replace('/tag/v20261110','/tag/v20261121').replace('-v20261110.md','-v20261121.md').replace('validation-v20261110.json','validation-v20261121.json')
if '## 지상·우주 루트 교차 진행' in s:
    a=s.index('## 지상·우주 루트 교차 진행');b=s.index('## v20261110 설명 표시 수정');s=s[:a]+s[b:]
point=s.index('## v20261110 설명 표시 수정')
intro='''## 지상·우주 루트 교차 진행

**13번을 켜면 지상 10화 → 우주 10화 → 지상 11화 → 우주 11화 → … → 양쪽 14화 → 원본 15화 순서로 진행**합니다. 끄면 원래 분기를 유지합니다. 부대 전환 시 육성·PP·격추수·개조·장비를 보존하고 공통 보급 이벤트의 중복 지급을 막습니다. 미선택 부대용 자동 EXP·격추수·PP 보정은 교차 진행에서 제외하여 실제 전투 성장과 겹치지 않게 했습니다.

| 추가 전장 12번 | 교차 진행 13번 | 전체 화수 |
|---|---|---|
| 끔 | 끔 | 36 |
| 끔 | 켬 | 41 |
| 켬 | 끔 | 49 |
| 켬 | 켬 | 54 |

**13번은 원본 9화 종료 전부터 최종전까지 유지하세요.** 이미 지나간 이벤트는 소급 실행하지 않습니다. PCSX2를 종료하고 기존 ISO 검사 → 원하는 기존 옵션 유지 → 13번 선택 → 적용 후 새로 부팅하여 일반 세이브를 사용합니다. 1번 추가 25편성의 새 게임 조건은 기존과 같습니다.

원본 15화 이후의 표시 화수는 +5입니다. 12·13번을 함께 켜면 원본 34화는 표시 39화, 국지전 40~44화, 원본 35화는 45화, 베오울프전 46화, 시빌워 47~53화, 라그나로크 54화입니다. 12번은 원본 34화 종료 전부터 유지합니다. 일부 기체 정비는 원본 30화/표시 35화부터입니다.

아래 기존 전장 소개의 화수는 13번 OFF 기준입니다. [교차 순서와 화수 대응표](docs/linear-route-v20261121.md)를 확인하세요.

8,192개 패처 조합과 이전 공개 버전 선택 인식, 게임 내부 분기 이동·편성 활성·보상 중복 방지·화수 조회·정비 시점을 검사했습니다. 원래 대사·전장 배치·설명 연결·전투 수치를 보존합니다. 실제 PCSX2 전편 플레이·AI·화면·메모리카드 입출력을 완료했다고 주장하지 않습니다. [현재 검증 결과](docs/validation-v20261121.json)를 제공합니다.

'''
s=s[:point]+intro+s[point:]
s=s.replace('체크박스는12개입니다.','체크박스는13개이며 새13번은 별도의 교차 진행 옵션입니다.').replace('패처4096조합과 이전 적용본 인식','패처8192조합과 이전 적용본 인식')
(REPO/'README.md').write_text(s,encoding='utf8')
tool_readme=REPO/'tools/README.md';tool_text=tool_readme.read_text(encoding='utf8')
if '## v20261121 교차 진행 제작 도구' in tool_text:tool_text=tool_text[:tool_text.index('## v20261121 교차 진행 제작 도구')].rstrip()+'\n'
tool_readme.write_text(tool_text,encoding='utf8')
with tool_readme.open('a',encoding='utf8') as out:out.write('''

## v20261121 교차 진행 제작 도구

현재 제작 경로는 `work_ogg/option_linear`입니다. 공개 패처는 루트 `build.ps1`에서 릴리즈 BIN을 지정하여 빌드할 수 있습니다. 13옵션/8192프로필이며 과거 버전 입력에서는 기존12비트만 가져와 새13번을 자동으로 켜지 않습니다.

`linear_route_policy.py`는 원래 시나리오 인덱스를 유지합니다. 양쪽10..14화를2009,2051,2010,2052,2011,2053,2012,2054,2013,2055 순서로 연결합니다. native91은 음수 skip을 받지 않으므로 전진 skip으로 추가한 함수 끝부분을 실행하고 원래 return/next-stage로 끝냅니다. 복사된 명령에 대한 기존 옵션의 변경도 함께 옮깁니다. 74개 사용 가능 상태 목표 외에 육성이나 소유를 새로 쓰는 명령은 추가하지 않습니다.

같은11/13/14화 보급은 미사용이던 전역40,0..2로 중복을 막고, 미롱가의 원래57,3 획득 비트로 우주 보충을 반복하지 않습니다. Stag의 모든 유효 행에서0이던11번 바이트를 표시 화수의 더하기 값으로 사용합니다. 표시 getter만 이 값을 더하며 논리적 인덱스는 유지합니다. 기존 후반 정비 threshold29는13번에서34가 됩니다. 각 원래26/3E/25와 대사 ID·이력, 전장 UNTD와 원래 전투 마스터 표를 비교합니다.

로컬 작성에는 비공개 원본 입력·과거 릴리즈 BIN·RAM 검사 자료·준비 파일이 필요합니다. 전체 게임 덤프는 포함하지 않습니다. 준비/빌더/적용은 적용 전 상태에 대해 작성한 역사적 작업이며 적용된 ISO에서 다시 실행하지 마세요. 정상 사용은 릴리즈 EXE+BIN 또는 공개 C# 빌드입니다. 실제 PCSX2 지도·AI·렌더링·메모리카드 플레이 테스트는 사용자 담당입니다.
''')
print('Synchronized current source, thirteen-option metadata and release guides.',flush=True)
