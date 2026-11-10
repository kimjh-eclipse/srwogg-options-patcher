"""One ZIP: twelve-option patcher, sixth-battle documentation and optional HD."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;VERSION='v20261110';DIST=WORK/('release_'+VERSION)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))
meta=report('build_metadata.json')
readme='''슈퍼로봇대전 OG외전12옵션 패처 v20261110 — 설명 표시 수정

정신기·특수능력·강화파츠·도감 설명이 열혈 설명 등으로 잘못 표시되던 문제를 수정했습니다.
기존 적용 ISO를 새 패처에서 검사하고 기존 옵션을 유지한 채 다시 적용하세요.
설명 수정만을 위해 새 게임을 다시 시작할 필요는 없습니다. PCSX2를 새로 부팅하고 일반 세이브를 사용하세요.

기존 기능
시빌워7부작의 각 전장에 아군2·3·4턴6기씩, 총18기의 일반병 증원을 추가했습니다. 일반병은 레벨52, 반란 지휘부는 레벨54입니다.
초기 적32기(이름 있는 파일럿 포함)는 유지하며 전함의 그 시점 위치 주변에 출현합니다.
전함 두 척이면 각3기, 한 척이면6기, 전함이 없으면 인질 수송기를 기준으로 합니다.
화별 편성과 기체 명단은 시빌워_편성과증원.md를 보세요.

최종전 바로 전7부작의 정치적 갈등·인질 구출·잠입·재합류를 유지합니다.
사전 정치 인터미션5곳, 각 전장 전후 교신과23개 교전 상대 조합의 자동 상호 대사를 포함합니다.
현재 시빌워 관련 대화창385개이며, 기존 추가6개 전장의225개 발언도 유지합니다.
설득 명령을 누르지 않아도 관련 인물들이 처음 교전하면 한 번 표시됩니다.
공격 순서와 관계없습니다. 필요한 인물을 출격시키지 않으면 그 조합의 대사는 나오지 않습니다.
같은 인물의 후속 교전은 해당 화의 상황에 맞게 이어집니다.

진행 순서
원본34화 → 추가35~39화 → 원본35화(표시40화) → 베오울프41화
→ 시빌워42~48화 → 원본36화(표시49화·최종전).
기존12번 옵션 하나로 추가13개 전장을 선택합니다. 선택 항목은12개를 유지합니다.
실제 플레이 검증 범위는 아래 확인 범위를 참고하세요.

시빌워
- 각 전장 초기 적32기, 중립 인질 수송기1기, 선택 출격12기. 기존 맵 재사용.
- 42/43/44화는 중계기2/2/3개,45화는 아치볼드·이글렛,46화는 빈델·웬드로,47화는 중계기2개,48화는 반란 지휘부4기 제압으로 승리.
- 아군 전멸 또는 인질 수송기 격파 시 패배. 나머지 적 전멸은 필요하지 않습니다.
- 레피나의 정규 경비대는 인질 때문에 대립하고, 반란조4인은 정치 세력과 결탁합니다.
- 라미아와 추가 잠입조는42화 이후 임시 분리되어47화에 복귀합니다.45·46화는 레피나 측 경비대만 출격합니다.
- 정규 경비대는44화 종료 후 지휘권을 회복하고45·46화에 직접 반격합니다.47화부터 양 함대가 공동 작전하며 반란조는48화 종료 후 감시 조건으로 복귀합니다.
- 기존 기체·파일럿의 개조·장비·EXP·PP·격추수를 삭제하지 않습니다.
- 레몬은 액셀렌과 구출대에 남습니다. 두 사람의 자매 인연을 이어갑니다.
- 자세한 명단과 대사 전문은 시빌워7부작_대사와편성.md를 보세요.

베오울프 전장
넓은 아인스트 맵에서 초기 적32기 중 일반 아인스트30기가 베오울프 생존 중 계속 보충됩니다.
베오울프 격파 시 증원이 멈추고 승리합니다. 레지세이아와 베오울프는 재생성하지 않습니다.
기존 국지전5편의32기 편성,25인 합류·밸런스와 보상 설정을 유지합니다.

적용 방법
1. ZIP을 풀고 patcher 폴더의 EXE와 BIN을 같은 폴더에 둡니다.
2. PCSX2를 완전히 종료합니다.
3. 패처 실행 → ISO 선택 → 검사 → 옵션 선택 → 패치 적용 순서로 진행합니다.
4. 완료 후 완전히 새로 부팅하고 일반 세이브를 불러옵니다.
5.12번은34화 종료 이벤트 이전부터 켜고 모든 추가 전장을 마칠 때까지 유지하세요.
6.1번 추가25인 시나리오는 새 게임부터 같은 설정을 유지하세요.
7.이미 지난 합류·보상·전장 삽입 이벤트는 소급 실행되지 않습니다.

라그나로크는 숙련도0에서도 직접 연결되는 경로를 검사했습니다. 추가 전장 선택 시49화, 해제 시36화입니다.

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
- v20261107.2부터 .8까지 이전 각4096개 조합을 지원합니다.12번을 켜면 추가13편을 모두 포함합니다.
- 첫 적용 전 변경 구간을 .v20261110.oggbak에 보관합니다. 전체 ISO 사본은 아닙니다.
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
for source,dest in [('help_text_details.md','설명표시_수정내역.md'),('civil_formations.md','시빌워_편성과증원.md'),('civil_war_details.md','시빌워7부작_대사와편성.md'),('intermission_six_details.md','추가전장_전후대사.md'),('beowulf_stage_details.md','베오울프전_변경내역.md'),('regional_five_details.md','국지전5편_시나리오.md'),('huckebein_r_details.md','휴케바인R_변경내역.md'),('followup_story_details.md','후속시나리오_대사.md'),('support_overhaul_details.md','지원장비_후반정비.md'),('party_preservation_details.md','편성보존_수정내역.md'),('spirit_balance_details.md','정신기_조정내역.md'),('story_consistency_details.md','본편연결_수정내역.md')]:
 (DIST/dest).write_text((HERE/source).read_text(encoding='utf8'),encoding='utf8')
addon=WORK.parent/'work_ogs/dist/SRWOGS_Beowulf_MkIII_HD_Addon_v20261106.zip';hd=[]
with zipfile.ZipFile(addon) as z:
 for name in z.namelist():
  if not name.endswith('.png'):continue
  dest=DIST/'textures/SLPS-25836/replacements/beowulf_mk3'/Path(name).name;dest.parent.mkdir(parents=True,exist_ok=True);b=z.read(name);assert b[:8]==b'\x89PNG\r\n\x1a\n';dest.write_bytes(b);hd.append(dict(file=dest.relative_to(DIST).as_posix(),sha256=sha(dest)))
assert len(hd)==27
validation=dict(passed=True,experimental=False,live_playthrough=False,playtesting_owner='user',full_iso_profile_exercise_run=False,profile_selftest=report('selftest.json'),previous_base_read_only_verification=report('source_verification.json'),canonical_verification=report('canonical_verification.json'),option_composition=report('followup_options_validation.json'),regional_options=report('regional_options_validation.json'),original_resources_preservation=report('preservation_validation.json'),beowulf=json.loads((WORK/'beowulf_stage_validation.json').read_text(encoding='utf8')),regional_density=json.loads((WORK/'regional_density_validation.json').read_text(encoding='utf8')),official_base=meta['upstream_base'])
validation['intermission']=json.loads((WORK/'intermission_six_validation.json').read_text(encoding='utf8'));assert validation['intermission']['passed']
validation['civil_war']=json.loads((WORK/'civil_war_validation.json').read_text(encoding='utf8'));assert validation['civil_war']['passed']
validation['civil_war_Beowulf_bridge']=json.loads((WORK/'civil_war_beowulf_bridge_validation.json').read_text(encoding='utf8'));assert validation['civil_war_Beowulf_bridge']['passed']
validation['civil_war_failures']=json.loads((WORK/'civil_war_failure_validation.json').read_text(encoding='utf8'));assert validation['civil_war_failures']['passed']
validation['civil_war_party']=json.loads((WORK/'civil_war_party_validation.json').read_text(encoding='utf8'));assert validation['civil_war_party']['passed']
validation['civil_war_resources']=json.loads((WORK/'civil_war_resource_validation.json').read_text(encoding='utf8'));assert validation['civil_war_resources']['passed']
validation['prior_Beowulf_native_checks_scope']='Original sixth battle unchanged; current byte preservation and composition checked separately'
validation['civil_reinforcements']=json.loads((WORK/'civil_reinforcements_validation.json').read_text(encoding='utf8'));assert validation['civil_reinforcements']['passed']
validation['civil_reinforcements_resources']=json.loads((WORK/'civil_reinforcements_resource_validation.json').read_text(encoding='utf8'));assert validation['civil_reinforcements_resources']['passed']
validation['civil_guard']=json.loads((WORK/'civil_guard_validation.json').read_text(encoding='utf8'));assert validation['civil_guard']['passed']
validation['civil_guard_waves']=json.loads((WORK/'civil_guard_waves_validation.json').read_text(encoding='utf8'));assert validation['civil_guard_waves']['passed']
validation['help_text_restore']=json.loads((WORK/'help_text_validation.json').read_text(encoding='utf8'));assert validation['help_text_restore']['passed']
validation['help_text_option_profiles']=report('help_text_profiles_validation.json');assert validation['help_text_option_profiles']['passed']
validation['ragnarok_access']=json.loads((WORK/'ragnarok_access_validation.json').read_text(encoding='utf8'));assert validation['ragnarok_access']['passed']
validation['sp_and_upgrade_prices']=report('sp_prices_validation.json')
for k in ['profile_selftest','previous_base_read_only_verification','canonical_verification','option_composition','regional_options','original_resources_preservation','beowulf','regional_density','sp_and_upgrade_prices']:assert validation[k]['passed']
assert validation['profile_selftest']['checkboxes']==12 and validation['profile_selftest']['profiles']==4096;assert validation['canonical_verification']['sha256']==meta['canonical_iso_sha256'];assert validation['option_composition']['pack_sha256']==meta['pack_sha256']
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
info={k:v for k,v in meta.items() if k not in ['proof','shutdown_requested']};info.update(experimental=False,prerelease=False,live_playthrough=False,help_text_explanation_records=4568,additional_battles=13,civil_war_battles=7,civil_war_mob_level=52,civil_war_rebel_ace_level=54,civil_reinforcement_turns=[2,3,4],civil_reinforcements_per_wave=6,ragnarok_zero_mastery_access_verified=True,beowulf_endless_minions=30,optional_HD_files=hd,executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'))
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf8')
zip_path=WORK/('SRWOGG_Options_kr_'+VERSION+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DIST.rglob('*')):
  if p.is_file():z.write(p,'SRWOGG_Options_kr_'+VERSION+'/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None and all(not n.lower().endswith(('.iso','.oggbak','.p2s','.ps2')) for n in z.namelist())
summary=dict(passed=True,zip=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),canonical_sha256=meta['canonical_iso_sha256'],options=12,verified_profiles=4096,additional_battles=13,experimental=False,live_playthrough=False,optional_HD_files=27,extra_full_ISOs_created=0)
(HERE/'release_completion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False,indent=2))
