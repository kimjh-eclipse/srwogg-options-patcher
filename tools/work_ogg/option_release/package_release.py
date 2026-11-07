"""Package the experimental twelve-option build without game images."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;DIST=WORK/'release_v20261107.2';VERSION='v20261107.2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))
meta=report('build_metadata.json')
readme="""슈퍼로봇대전 OG외전 12옵션 패처 v20261107.2 — 국지전 5편 시험판

PCSX2 실제 전투 진행 확인 전의 시험판입니다. 최신 안정판은 v20261107.1입니다.
새 12번 옵션: 34화 → 추가35~39화 → 본래35화(표시40화) → 본래36화(표시41화·최종전).
각 전장은 보유 기체12기 선택 출격, 적16기. 기존 전장·기체·무기를 재사용합니다.
새 인물·기체·물품은 중복 지급하지 않습니다. 추가25인 대사는 기존1번 옵션에 따릅니다.
레몬·액셀렌의 자매 인연은 마지막 지역전에서 이어집니다.

사용 방법
1. ZIP을 압축 해제하고 patcher 폴더의 EXE와 BIN을 같은 폴더에 둡니다.
2. PCSX2를 완전히 종료합니다. ISO 선택 → 검사 → 옵션 선택 → 패치 적용 순서로 진행합니다.
3. 완료 뒤 PCSX2를 완전히 새로 부팅하고 일반 세이브를 불러옵니다.
4. 국지전은 34화 종료 이벤트 이전부터 12번을 선택하고, 다섯 작전 동안 유지하세요.
   이미 본래35화로 넘어간 세이브에는 소급 삽입되지 않습니다.
5. 추가25인 합류 시나리오(1번)는 기존 안내대로 새 게임부터 같은 설정을 유지하세요.

원복과 기존 적용본
- 12개 옵션의 기본값은 모두 꺼짐입니다.
- v20261107.1의 2,048개 조합을 포함한 지원 적용본의 선택값을 유지합니다.
  이전11옵션 입력에서는 새12번만 꺼짐으로 인식합니다. 옛 SP1은 다시 노출하지 않습니다.
- 첫 적용 전 변경 구간만 .v20261107.2.oggbak에 보관합니다. 전체 ISO 복사본이 아닙니다.
- [처음 상태 복원]은 최초 입력 상태로 되돌립니다. 받은 기체나 물품을 세이브에서 삭제하지는 않습니다.
- 국지전을 끄면 원래34→35→36 진행과 화수 표시로 돌아갑니다. 원작 최종전 종료 처리를 보존합니다.
- 기존 옵션 설명의35·36화는 원본 화수입니다. 새12번 선택 시 해당 장면은 표시40·41화입니다.

베이스 한글패치
공식 v1.4.3s를 먼저 적용하세요. 원본 한글패치 파일은 이 ZIP에 포함하지 않습니다.
공식 릴리즈: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG
직접 다운로드: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z
제작자 저장소: https://github.com/z3oo3z/PS2-SRWOGG-KPatch
일본판 원본 MD5: cb7dc4485f46f220c46095c966a3aad0
공식 패치 결과 MD5: a5254cd5d4deabc57e03a3dcbb6a88d7
공식 패치 결과 SHA-256: e819f1e524513bc7e273b004ba02e3977dd4fff365a5887b4eb1c8a9fc9d1e04

선택 옵션
"""
for option in meta['options']:readme+=str(option['bit']+1)+'. '+option['name']+'\n   '+option['description']+'\n'
readme+="""
확인 범위
- 게임 처리 함수를 이용한 문자열·이력·제목·화수·승패 분기·다음 화 이동 점검.
- 병력 수를 입력한 시험에서 출격 전 오판 방지, 아군 전멸 및 적 생존/전멸 분기를 점검했습니다.
- C# 패처의4,096조합 자체검사와 메모리 내 기존 기능 조합 검사를 진행했습니다.
- ISO에4,096번 반복 적용하지 않았습니다. PCSX2 플레이 테스트는 사용자가 진행합니다.
- 화면상 출격·전투·결과 창·메모리카드 로드·전편 플레이를 검증했다고 주장하지 않습니다.
- 게임 ISO·BIOS·원본 대사 덤프·메모리 덤프·세이브는 포함하지 않습니다.
- 자세한 추가 설정, 장소, 적 편성, 모든 작성 대사는 국지전5편_시나리오.md에 있습니다.
"""
(DIST/'읽어주세요.txt').write_text(readme,encoding='utf-8-sig')
for source,dest in [('regional_five_details.md','국지전5편_시나리오.md'),('huckebein_r_details.md','휴케바인R_변경내역.md'),('followup_story_details.md','후속시나리오_대사.md'),('support_overhaul_details.md','지원장비_후반정비.md'),('party_preservation_details.md','편성보존_수정내역.md'),('spirit_balance_details.md','정신기_조정내역.md'),('story_consistency_details.md','본편연결_수정내역.md')]:
 (DIST/dest).write_text((HERE/source).read_text(encoding='utf8'),encoding='utf8')
validation=dict(passed=True,experimental=True,live_playthrough=False,playtesting_owner='user',full_iso_profile_exercise_run=False,profile_selftest=report('selftest.json'),previous_base_read_only_verification=report('source_verification.json'),canonical_verification=report('canonical_verification.json'),option_composition=report('followup_options_validation.json'),regional_options=report('regional_options_validation.json'),original_resources_preservation=report('preservation_validation.json'),regional_native=json.loads((WORK/'regional_five_validation.json').read_text(encoding='utf8')),official_base=meta['upstream_base'])
for key in ['profile_selftest','previous_base_read_only_verification','canonical_verification','option_composition','regional_options','regional_native','original_resources_preservation']:assert validation[key]['passed']
assert validation['profile_selftest']['profiles']==4096 and validation['profile_selftest']['checkboxes']==12
assert validation['canonical_verification']['sha256']==meta['canonical_iso_sha256']
assert validation['option_composition']['pack_sha256']==meta['pack_sha256']
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
info={k:v for k,v in meta.items() if k not in ['proof','shutdown_requested']};info.update(experimental=True,prerelease=True,live_playthrough=False,executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'))
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf8')
zip_path=WORK/('SRWOGG_Options_kr_'+VERSION+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DIST.rglob('*')):
  if p.is_file():z.write(p,'SRWOGG_Options_kr_'+VERSION+'/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None and all(not n.lower().endswith(('.iso','.oggbak')) for n in z.namelist())
summary=dict(passed=True,zip=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),canonical_sha256=meta['canonical_iso_sha256'],options=12,verified_profiles=4096,experimental=True,live_playthrough=False,extra_full_ISOs_created=0)
(HERE/'release_completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False,indent=2))
