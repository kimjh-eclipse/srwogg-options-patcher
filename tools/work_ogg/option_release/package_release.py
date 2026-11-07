"""One ZIP: twelve-option patcher, sixth-battle documentation and optional HD."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;VERSION='v20261107.5';DIST=WORK/('release_'+VERSION)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))
meta=report('build_metadata.json')
readme='''슈퍼로봇대전 OG외전12옵션 패처 v20261107.5 — 베오울프 결전 시험판

기존12번 옵션 하나에 국지전5편과 베오울프전1편을 함께 묶었습니다.
선택 항목은12개이며 베오울프 전용 체크박스는 추가하지 않습니다.
최신 안정판은 v20261107.1이며, 이번 배포는 실플레이 확인 전의 시험판입니다.

진행 순서
원본34화 → 추가35~39화 → 원본35화(표시40화)
→ 베오울프전41화「푸른 늑대의 잔향」→ 원본36화(표시42화·최종전).

베오울프 전장
- 넓고 장애물이 적은 아인스트 공간, 선택 출격12기, 초기 적32기.
- 아이젠10·녹헨8·리토6·게미유트6·레지세이아1·베오울프1.
- 일반 아인스트30기는 베오울프가 살아 있는 동안 격파된 개체만 다시 보충합니다.
- 베오울프 격파 시 증원이 멈추고 승리합니다. 남은 적 전멸은 필요하지 않습니다.
- 베오울프와 레지세이아는 재생성하지 않습니다.
- OGs에서 제작한 전용 기체·무장6종·초상화·컷인 자료를 별도로 이식했습니다.
- 베오울프 기본HP135000, 무장공격력3300/3200/4500/5300/6300/4800.
- 기존국지전5편의 각32기 편성,25인 합류·밸런스와 기존 보상 설정은 유지합니다.

적용 방법
1. ZIP을 풀고 patcher 폴더의 EXE와 BIN을 같은 폴더에 둡니다.
2. PCSX2를 완전히 종료합니다.
3. 패처 실행 → ISO 선택 → 검사 → 옵션 선택 → 패치 적용 순서로 진행합니다.
4. 완료 후 완전히 새로 부팅하고 일반 세이브를 불러옵니다.
5.12번은34화 종료 이벤트 이전부터 선택하고 추가 전장을 모두 마칠 때까지 유지하세요.
6. 이미 지난 합류·보상·전장 삽입 이벤트는 소급 실행되지 않습니다.
7. 추가25인 시나리오는 새 게임부터 같은 설정을 유지하세요.

선택 기능
'''
for x in meta['options']:readme+=str(x['bit']+1)+'. '+x['name']+'\n   '+x['description']+'\n'
readme+='''
베오울프 HD 추가 자료(선택)
ZIP의 textures 폴더를 PCSX2의 텍스처 검색 폴더에 합쳐 넣고 Load Textures를 켜세요.
대상은 SLPS-25836/replacements/beowulf_mk3/*.png 입니다.
OGs 제작본의 PNG27개만 담았습니다. 전체 HD팩은 포함하지 않습니다.
이미 다른 HD팩을 사용하면 동일 이름의 텍스처 중복을 확인해 주세요.
ISO 적용과 HD텍스처 설치는 별개입니다. 미설치 시 이식한 기본 게임 이미지를 사용합니다.

원복과 이전 버전
- 기본 옵션은 모두 꺼짐입니다. 이전 지원 적용본의 선택값을 인식합니다.
- v20261107.2/.3/.4의 각4096개 조합을 지원합니다.12번을 켜면 새 베오울프전도 포함됩니다.
- 첫 적용 전 변경 구간을 .v20261107.5.oggbak에 보관합니다. 전체 ISO 사본은 아닙니다.
- [처음 상태 복원]은 최초 입력 ISO 상태로 돌아갑니다. 세이브의 보유품은 삭제하지 않습니다.
- 새 전장에 들어간 상태에서12번을 끄지 마세요.

공식 한글패치
z3oo3z/PS2-SRWOGG-KPatch의 v1.4.3s를 먼저 적용하세요.
공식 릴리즈: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG
직접 다운로드: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z
제작자 저장소: https://github.com/z3oo3z/PS2-SRWOGG-KPatch
일본판 원본MD5: cb7dc4485f46f220c46095c966a3aad0
공식 한글판MD5: a5254cd5d4deabc57e03a3dcbb6a88d7

확인 범위
패처4096조합과 기존 기능 선택을 점검했습니다.
베오울프전 반복 증원100회·동시 격파7기와 보스 격파 승리는 맵 생성 부분을 시험용 상태로
대체하여 확인했고, 실제 게임의 등록·조건·기체 준비 생성 함수를 별도로 점검했습니다.
NPC 재생성·퇴장·충돌·AI·연출·장기 보상·메모리카드 실플레이 확인은 사용자가 진행합니다.
ISO4096회 반복 적용이나 PCSX2 전편 검증을 완료했다고 주장하지 않습니다.
게임ISO·BIOS·원본 대사 덤프·메모리 덤프·세이브는 포함하지 않습니다.
'''
(DIST/'읽어주세요.txt').write_text(readme,encoding='utf-8-sig')
for source,dest in [('beowulf_stage_details.md','베오울프전_변경내역.md'),('regional_five_details.md','국지전5편_시나리오.md'),('huckebein_r_details.md','휴케바인R_변경내역.md'),('followup_story_details.md','후속시나리오_대사.md'),('support_overhaul_details.md','지원장비_후반정비.md'),('party_preservation_details.md','편성보존_수정내역.md'),('spirit_balance_details.md','정신기_조정내역.md'),('story_consistency_details.md','본편연결_수정내역.md')]:
 (DIST/dest).write_text((HERE/source).read_text(encoding='utf8'),encoding='utf8')
addon=WORK.parent/'work_ogs/dist/SRWOGS_Beowulf_MkIII_HD_Addon_v20261106.zip';hd=[]
with zipfile.ZipFile(addon) as z:
 for name in z.namelist():
  if not name.endswith('.png'):continue
  dest=DIST/'textures/SLPS-25836/replacements/beowulf_mk3'/Path(name).name;dest.parent.mkdir(parents=True,exist_ok=True);b=z.read(name);assert b[:8]==b'\x89PNG\r\n\x1a\n';dest.write_bytes(b);hd.append(dict(file=dest.relative_to(DIST).as_posix(),sha256=sha(dest)))
assert len(hd)==27
validation=dict(passed=True,experimental=True,live_playthrough=False,playtesting_owner='user',full_iso_profile_exercise_run=False,profile_selftest=report('selftest.json'),previous_base_read_only_verification=report('source_verification.json'),canonical_verification=report('canonical_verification.json'),option_composition=report('followup_options_validation.json'),regional_options=report('regional_options_validation.json'),original_resources_preservation=report('preservation_validation.json'),beowulf=json.loads((WORK/'beowulf_stage_validation.json').read_text(encoding='utf8')),regional_density=json.loads((WORK/'regional_density_validation.json').read_text(encoding='utf8')),official_base=meta['upstream_base'])
validation['sp_and_upgrade_prices']=report('sp_prices_validation.json')
for k in ['profile_selftest','previous_base_read_only_verification','canonical_verification','option_composition','regional_options','original_resources_preservation','beowulf','regional_density','sp_and_upgrade_prices']:assert validation[k]['passed']
assert validation['profile_selftest']['checkboxes']==12 and validation['profile_selftest']['profiles']==4096;assert validation['canonical_verification']['sha256']==meta['canonical_iso_sha256'];assert validation['option_composition']['pack_sha256']==meta['pack_sha256']
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
info={k:v for k,v in meta.items() if k not in ['proof','shutdown_requested']};info.update(experimental=True,prerelease=True,live_playthrough=False,additional_battles=6,beowulf_endless_minions=30,optional_HD_files=hd,executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'))
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf8')
zip_path=WORK/('SRWOGG_Options_kr_'+VERSION+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DIST.rglob('*')):
  if p.is_file():z.write(p,'SRWOGG_Options_kr_'+VERSION+'/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None and all(not n.lower().endswith(('.iso','.oggbak','.p2s','.ps2')) for n in z.namelist())
summary=dict(passed=True,zip=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),canonical_sha256=meta['canonical_iso_sha256'],options=12,verified_profiles=4096,additional_battles=6,experimental=True,live_playthrough=False,optional_HD_files=27,extra_full_ISOs_created=0)
(HERE/'release_completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False,indent=2))
