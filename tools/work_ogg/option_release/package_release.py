from pathlib import Path
import json,hashlib,zipfile

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
DIST=WORK/'release_v20261106.4'
meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))

readme='''슈퍼로봇대전 OG외전 한글판 옵션 패처 v20261106.4 — 본편 연결 대사 수정

사용 방법
1. ZIP을 압축 해제합니다. patcher 폴더의 EXE와 BIN은 같은 폴더에 두세요.
2. PCSX2를 완전히 종료하고 OGG_Options_Patcher.exe를 실행합니다.
3. [ISO 선택]으로 패치할 파일을 고르고 [검사]를 누릅니다.
4. 원하는 옵션을 선택한 뒤 [패치 적용]을 누릅니다.
5. 완료 문구를 확인하고 PCSX2에서 게임을 완전히 새로 부팅합니다.
   이전 상태 저장(세이브 스테이트)을 불러오면 이전 코드가 실행될 수 있습니다.

대상
- 베이스: z3oo3z/PS2-SRWOGG-KPatch v1.4.3s 공식 릴리즈.
  https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG
- 일본판 원본 MD5 cb7dc4485f46f220c46095c966a3aad0에 공식 한글 패치를 적용한 뒤 사용하세요.
- 공식 한글 패치 결과 MD5: a5254cd5d4deabc57e03a3dcbb6a88d7.
- 기존 v20261106 적용본도 지원하며 새 베이스로 업데이트합니다.
- 원본 OG외전 한글판 SRWOGS_EX_K.ISO 또는 이 패처가 지원하는 적용본.
- 파일 크기: 4,666,294,272바이트.
- 기준 원본 SHA-256:
  e819f1e524513bc7e273b004ba02e3977dd4fff365a5887b4eb1c8a9fc9d1e04
- 현재 SRWOGS_EX_K_TEST.ISO도 인식하며 [검사] 시 7개 옵션이 선택됩니다.
- 다른 개조판이나 지원되지 않는 변경이 있는 ISO는 쓰기 전에 거부합니다.
- Python이나 xdelta 설치 없이 Windows의 .NET Framework로 실행됩니다.

선택 옵션 (7개, 실행 직후 기본값은 모두 해제)
1. 25편성 분산 합류·추가 시나리오
   3화부터 전이 관련 대화, 4~31화에 25편성이 분산 합류합니다.
   죽기 직전 차원이동 설정과 레몬·액셀렌의 자매 인연을 포함합니다.
   추가 기체·파일럿 능력치, 독립 무장, 초기 개조 및 단계별 무장 해금도 포함합니다.
   앞서 제외한 전함·쿠엘보·아기라·세프타긴은 추가 편성에 포함하지 않습니다.
2. 숨겨진 요소 자동 습득
   6화: 고성능 전자두뇌 / 13화: 미롱가(양쪽 루트 지원)
   25화: 시시오 블레이드·용자의 인 / 30화: 부스트 해머·강철의 혼.
   해당 화의 보상 처리를 진행하면 조건 없이 얻습니다.
3. 3화 추가 보급 8종
   시시오 블레이드, 부스트 해머, 강철의 혼, 용자의 인,
   고성능 전자두뇌, 메가 제너레이터, 부스터, 메가 부스터 각 1개.
   한 번만 지급하며, 이후 자연 획득 보상은 별도입니다.
   25편성 시나리오를 해제해도 이 보급 옵션은 독립적으로 작동합니다.
4. 전투 보상: PP 2배·자금 +20%
   기존 보너스·분배 후 최종 전투 보상에 적용하며 자금 소수점은 버립니다.
5. 적 강화
   적대 판정 파일럿의 전투 능력치 +5.
   적 편성의 기체·무장 개조 +2(최대 15단계).
   기본 HP가 1~19,999인 적은 기본 HP의 10%를 추가합니다.
6. 공통 무장 밸런스
   OGs에서 정한 공통 무장 27종의 조정을 옮깁니다.
   외전 고유 강화분과 추가 25편성의 독립 무장 밸런스를 유지합니다.
7. 무장 개조비 할인
   OGs의 최종 비용표를 적용합니다. 비용 0·1등급과 3·4등급이 각각 같습니다.
   10단계 누적: 0/1등급 88,000, 2등급 105,600, 3/4등급 176,000.
   공격력 개조 상승량은 유지됩니다. 옵션을 해제하면 외전 원래 비용표입니다.

시나리오 대사 수정 (1번 옵션 선택 시)
- 13개 화의 대사 31개를 다듬고 최종전 반응 대사 3개를 추가했습니다.
- 28화의 빈델 장면은 피오나 귀환과 라미아 구출 작전 설명 뒤로 옮겼습니다.
- 35화의 추가 인물 반응은 라울·미즈호의 데스피니스 구조 뒤로 옮겼습니다.
- 36화는 비안·잉그램·레몬의 최종전 반응을 추가하고 원작 마지막 대사로 마칩니다.
- 레몬과 액셀렌의 선택한 자매 관계, 합류 화수, 기체·파일럿 밸런스를 유지합니다.
- 이번 변경은 기존 추가 시나리오 옵션에 포함되며 별도 체크 항목은 없습니다.

공통 적용
- 추가한 린의 휴케바인을 원래 휴케바인과 별도 그룹으로 분리했습니다.
  본편의 원래 기체 이탈 처리가 추가 기체와 탑승 파일럿까지 비활성화하던 문제를 수정합니다.
- 정비 전·후 형태에 모두 적용합니다. 능력치·정신기·개조·무장은 유지합니다.
- 이전 버전에서 이미 영향을 받은 경우, 28화 시작 이벤트에서 기존 추가 기체만 재활성화합니다.
  경험치·PP·개조값을 초기화하지 않고, 없는 기체는 새로 지급하지 않습니다.
  이 복구는 추가 시나리오 옵션을 꺼도 적용됩니다. 이미 지난 28화 이벤트는 재실행되지 않습니다.
- 시나리오 해제 시 사용하는 보급·복구 스크립트가 상위 파일 범위에 포함되도록 수정했습니다.
- 정신기 SP 1 옵션을 제거했습니다. 기존 파일럿은 원래 소모량을, 추가 파일럿 13명은 역할별 조정 소모량을 사용합니다.
- 이전 8옵션 256조합과 v20261106.1·v20261106.2·v20261106.3의 7옵션 각 128조합도 인식합니다.
- 추가 25명 중 13명의 구성·비용·습득 레벨을 조정했습니다. SP 최대치는 유지합니다.
- 울즈·안사즈의 각성은 SP60·Lv38, 스리사즈는 돌격형 구성입니다.
- 템페스트의 사랑은 SP65·Lv38이며 비어 있던 트윈 정신기 4개를 보완했습니다.
- 정찰 SP1은 원작의 정상 비용이므로 유지합니다.
- 기존 작업의 지형명·도움말·추가 전투 자막 등 한글 표시 수정을 포함합니다.
- 비활성 추가 기체 데이터와 기능 실행에 공통으로 필요한 자원은 남습니다.
- 7개 옵션을 모두 해제해도 수정 전 원본과 완전히 같은 파일은 아닙니다.
  패처 최초 사용 전의 정확한 파일로 돌아가려면 [처음 상태 복원]을 사용하세요.

원복과 옵션 변경
- 첫 적용 때 ISO 옆에 .v20261106.4.oggbak 복원 기록을 만듭니다.
  이전 버전의 .oggbak과는 별도로 관리합니다. 기존 기록은 덮어쓰지 않습니다.
  전체 ISO 복사본이 아니라 변경 구간만 저장하는 작은 파일입니다.
- [처음 상태 복원]은 해당 기록을 만든 첫 적용 직전의 파일로 복원합니다.
  처음 입력한 것이 현재 시험 ISO라면 그 시험 ISO 상태로 돌아갑니다.
- .oggbak은 삭제하거나 다른 ISO의 기록으로 교체하지 마세요.
- 이후 옵션 변경은 체크를 바꿔 [패치 적용]하면 됩니다.
- 패치 데이터와 복원 기록을 검증하고, 쓰기 실패 시 변경 전 상태로 되돌립니다.

세이브 관련
- 25편성 시나리오는 새 게임에서 시작하고 진행 중에는 같은 설정을 유지하세요.
- 옵션을 해제해도 이미 세이브에 합류한 인물·기체나 받은 물품은 삭제되지 않습니다.
- 3화 보급과 각 화 숨김 보상은 해당 이벤트 이전 세이브부터 진행해야 합니다.
  이미 지난 이벤트가 소급해서 실행되지는 않습니다.
- 전투 보상·적 능력치·공통 무장·원래 SP 소모량은 새 부팅 뒤 적용됩니다.
  배치 때 저장되는 적 개조 단계는 해당 맵 진입 전부터 진행해 주세요.

검증 범위
- 128가지 조합을 생성하고 실제 시험 ISO에 전환·읽기 검증했습니다.
- 복원 기록을 이용해 시험 ISO를 원래 SHA-256으로 복원했습니다.
- 실제 게임의 R5900 루틴으로 보급 중복 방지, 대화 문자열·로그,
  보상 계산 및 적 능력치·HP를 검사했습니다.
- 패처 화면도 렌더링 확인했습니다. 편성 보존은 실제 게임 루틴과 통제된 입력으로 검사했습니다.
  맵 유닛 조회는 부재 조건으로 대체했으며, 재로드는 영구 저장 데이터의 VM 복원입니다.
  실제 메모리카드 저장·로드나 PCSX2 전편 실기 플레이는 미검증입니다.
- 배포 ZIP에는 게임 ISO·전체 ISO 백업·제작자의 원본 한글 패치 파일이 포함되지 않습니다.
'''
(DIST/'읽어주세요.txt').write_text(readme,encoding='utf-8-sig')
(DIST/'본편연결_수정내역.md').write_text((HERE/'story_consistency_details.md').read_text(encoding='utf-8'),encoding='utf-8')
(DIST/'편성보존_수정내역.md').write_text((HERE/'party_preservation_details.md').read_text(encoding='utf-8'),encoding='utf-8')
(DIST/'정신기_조정내역.md').write_text((HERE/'spirit_balance_details.md').read_text(encoding='utf-8'),encoding='utf-8')
validation={
 'passed':True,'live_playthrough':False,
 'profile_selftest':report('selftest.json'),
 'previous_base_read_only_verification':report('source_verification.json'),
 'real_iso_transitions':report('iso_transition_validation.json'),
 'native_option_behavior':report('native_options_validation.json'),
 'ui_render_verified':True,
 'party_preservation':json.loads((WORK/'party_25_validation.json').read_text(encoding='utf-8')),
 'story_consistency':json.loads((WORK/'story_consistency_validation.json').read_text(encoding='utf-8')),
 'canonical_revision':{k:v for k,v in json.loads((WORK/'story_consistency_journal.json').read_text(encoding='utf-8')).items() if k!='edits'},
 'canonical_verification':report('canonical_verification.json'),
 'official_base':meta['upstream_base'],
 'upstream_rebase':{k:v for k,v in json.loads((WORK/'upstream_rebase_journal.json').read_text(encoding='utf-8')).items() if k not in ['edits','semantic_strings']}}
assert all(validation[k]['passed'] for k in ['profile_selftest','previous_base_read_only_verification','real_iso_transitions','native_option_behavior'])
assert validation['party_preservation']['passed'] and validation['story_consistency']['passed']
assert validation['real_iso_transitions']['canonical_sha256_after']==meta['canonical_iso_sha256']
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
info={k:v for k,v in meta.items() if k not in ['proof','shutdown_requested']}
info.update(executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'),canonical_iso_preserved_during_option_tests=True,canonical_revision_applied=True,source_iso_preserved=True,live_playthrough=False)
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf-8')
zip_path=WORK/'SRWOGG_Options_kr_v20261106.4.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DIST.rglob('*')):
  if p.is_file():z.write(p,'SRWOGG_Options_kr_v20261106.4/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert all(not n.lower().endswith(('.iso','.oggbak')) for n in z.namelist())
 for p in sorted(DIST.rglob('*')):
  if p.is_file():assert hashlib.sha256(z.read('SRWOGG_Options_kr_v20261106.4/'+p.relative_to(DIST).as_posix())).hexdigest()==sha(p)
summary={'passed':True,'zip':str(zip_path),'zip_bytes':zip_path.stat().st_size,'zip_sha256':sha(zip_path),'canonical_sha256':meta['canonical_iso_sha256'],'options':7,'verified_profiles':128,'extra_full_ISOs_created':0}
(HERE/'release_completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
