"""Publish only authoring source and release documentation, never native dumps."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent;WORK=HERE.parent;REPO=WORK.parent/'srwogg-options-patcher'
def main():
 version='v20261107.8';dist=WORK/('release_'+version);completion=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert completion['passed'];meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))
 shutil.copy2(HERE/'OggOptionsPatcher.cs',REPO/'src/OggOptionsPatcher.cs')
 for p in HERE.iterdir():
  if p.name in ['build_options.py','validate_options.py','validate_followup_options.py','package_release.py','publish_release.py','finish_local.py','sync_repo.py','audit_release.py'] or p.suffix=='.md':shutil.copy2(p,REPO/'tools/work_ogg/option_release'/p.name)
 for n in ['civil_guard_content.py','prepare_civil_guard.py','validate_civil_guard.py','validate_civil_guard_waves.py','apply_civil_guard.py','validate_ragnarok_access.py','civil_reinforcement_policy.py','prepare_civil_reinforcements.py','validate_civil_reinforcements.py','validate_civil_reinforcement_resources.py','apply_civil_reinforcements.py','civil_war_audit.py','civil_war_content.py','civil_war_policy.py','prepare_civil_war.py','validate_civil_war.py','validate_civil_war_beowulf_bridge.py','validate_civil_war_failures.py','validate_civil_war_party.py','validate_civil_war_resources.py','apply_civil_war.py','CIVIL_WAR_CAST_PLAN_DRAFT.json','CIVIL_WAR_MASTER_DRAFT.txt','CIVIL_WAR_POLITICAL_PROLOGUE_DRAFT.txt','CIVIL_WAR_BATTLE_PERSUASION_DRAFT.txt','intermission_six_content.py','intermission_six_policy.py','prepare_intermission_six.py','validate_intermission_six.py','apply_intermission_six.py','inspect_iso.py','beowulf_source_image.py','inspect_beowulf_import.py','audit_beowulf_resources.py','beowulf_stage_content.py','beowulf_stage_policy.py','prepare_beowulf_stage.py','validate_beowulf_stage.py','apply_beowulf_stage.py']:shutil.copy2(WORK/n,REPO/'tools/work_ogg'/n)
 for src,dst in [('시빌워_편성과증원.md','civil-formations-v20261107.8.md'),('시빌워7부작_대사와편성.md','civil-war-v20261107.8.md'),('추가전장_전후대사.md','intermission-six-v20261107.8.md'),('베오울프전_변경내역.md','beowulf-stage-v20261107.8.md'),('국지전5편_시나리오.md','regional-five-v20261107.8.md'),('PATCH_INFO.json','patch-info-v20261107.8.json'),('검증결과.json','validation-v20261107.8.json'),('읽어주세요.txt','사용안내.txt')]:shutil.copy2(dist/src,REPO/'docs'/dst)
 info=dict(version=version,file='OGG_options.bin',sha256=meta['pack_sha256'],bytes=meta['pack_size'],options=12,profiles=4096,prerelease=False,distribution='zip-only',release_zip_sha256=completion['zip_sha256']);(REPO/'patch-data.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 p=REPO/'README.md';old=p.read_text(encoding='utf8');rest=old[old.index('## 베이스 한글패치'):].replace('v20261107.4','v20261107.8').replace('v20261107.5','v20261107.8').replace('v20261107.6','v20261107.8').replace('v20261107.7','v20261107.8')
 rest=rest.replace('v20261107.2와 v20261107.3 적용본은','v20261107.2·.3·.4 적용본은').replace('| 34화 이후 국지전5편 |. 추가35~39화 각32기 뒤 본편40~41화 |','| 추가 전장13편·시빌워·베오울프 |. 국지전5편·베오울프·시빌워7부작 |').replace('표시40·41화','표시40·49화')
 rest=rest.replace('| 추가 전장6편·베오울프 |. 국지전5편+최종전 직전 무한 증원 결전 |','| 추가 전장13편·시빌워·베오울프 |. 국지전5편·베오울프·시빌워7부작 |').replace('표시40·42화입니다.','표시40·49화입니다.').replace('v20261107.2·.3·.4·.5 적용본은','v20261107.2·.3·.4·.5·.6 적용본은')
 section=rest.index('## 확인 범위와 소스');rest=rest[:section]+'''## 확인 범위와 소스

패처4096조합과 이전 적용본 인식을 점검합니다. 새 전장의 native 등록·조건 처리와 기존 베오울프 준비 생성192조건과 기존 시빌워320조건 및 경비대 확장834검사·교전69경우·준비생성230조건·증원168경우을 확인했습니다. 원래 기체·파일럿·무장·초상화·연출 자원, 추가25인 육성과 기존5개 전장을 보존합니다.

반복 증원100회·동시 격파7기·보스 격파 후 중지와 승리 판정은 맵 생성 부분을 시험용 상태로 대체하여 점검했습니다. 실제 NPC 재생성·퇴장·충돌·AI·연출·장기 보상·메모리카드 로드는 PCSX2 플레이 확인이 필요합니다. 사용자가 플레이 테스트를 진행합니다. [검증 결과](docs/validation-v20261107.8.json)를 제공합니다.

`src`는 Windows패처, `tools/work_ogg`는 제작·분석·검증 소스입니다. 게임에서 추출한 로컬 입력과 OGs 제작본의 베오울프 자료는 저장소에 포함하지 않아 모든 제작을 이 저장소만으로 재현하지는 못합니다. 역사적 빌더를 현재 ISO에 재실행하지 마세요. [제작 도구 안내](tools/README.md)를 참고하세요.

게임ISO·BIOS·메모리 덤프·세이브·전체 ISO백업은 배포하지 않습니다.
'''
 intro='''# OG외전 한글판 옵션 패처

공식 한글패치 기반 Windows 추가 패처입니다. **v20261107.8는 최종전 직전 시빌워7부작을 포함한 추가 전장13편**입니다.

[**패처·설명서·선택 HD자료 ZIP 다운로드**](https://github.com/kimjh-eclipse/srwogg-options-patcher/releases/download/v20261107.8/SRWOGG_Options_kr_v20261107.8.zip)

## 이번 배포: 시빌워 후방 증원

각 화의 아군2·3·4턴에 일반병6기씩, 총18기가 증원됩니다. 초기 적32기(이름 있는 파일럿 포함)를 두고 화당 최대50기입니다. 일반병은 레벨52입니다.45·46화는 레피나 측 경비대를 직접 조작하는 선제 반격전이고47화는 양 함대의 합동 구출전입니다. 라그나로크는 숙련도0에서도 직접 연결되는 경로를 검사했습니다. 전함 두 척이면 그 시점 위치 주변에3기씩, 한 척이면6기이며 전함이 없으면 인질 수송기를 기준으로 합니다. 중복 증원을 막고 기존 승리 조건과 대사는 유지했습니다. [화별 편성·기체·승리 조건](docs/civil-formations-v20261107.8.md)을 확인하세요.

최종전 직전에 정치적 갈등·인질 구출·잠입·재합류로 이어지는42~48화를 추가했습니다. 기존12번 추가 전장 옵션에 포함합니다. 사전 정치 인터미션5곳, 각 전장 출격 경보·전후 교신과 관련 대화창385개를 넣었습니다.

**상호 설득 대사는 해당 인물끼리 교전할 때 자동으로 한 번 표시**됩니다. 전장별23개 상대 조합이며 공격 순서와 관계없고 설득 명령은 없습니다. 관련 인물을 출격시키지 않으면 그 조합의 대사는 나오지 않습니다. 같은 인물의 후속 교전은 해당 화의 상황에 맞게 이어집니다.

레피나의 정규 경비대는 인질 때문에 테츠야와 대립하고 정치 세력과 결탁한 반란조와 구별됩니다. 라미아·유리아·에키드나·토머스는 잠입했다가 복귀하며, 레몬은 액셀렌과 구출대에 남습니다. 기존50인과 추가25인, 데스피니스를 포함한76인의 편성과 육성 보존을 검사했습니다. [전체 대사와 편성](docs/civil-war-v20261107.8.md)을 제공합니다.

각 전장 초기 적32기·중립 인질 수송기1기·선택 출격12기입니다.42~44화는 중계기2/2/3개,45화는 아치볼드·이글렛,46화는 빈델·웬드로,47화는 중계기2개,48화는 반란 지휘부4기 제압으로 승리합니다. 인질 수송기 격파 또는 아군 전멸 시 패배합니다. 기존 지역 맵을 재사용합니다.

진행: **원본34화 → 국지전35~39화 → 원본35화(표시40화) → 베오울프41화 → 시빌워42~48화 → 원본36화(표시49화·최종전)**.

기존 추가6편의 전후 함내 장면12개와225개 발언도 유지합니다. [기존 전장 대사](docs/intermission-six-v20261107.8.md)를 참고하세요.

## 베오울프 결전

**기존12번 옵션 하나**로 국지전5편·베오울프전1편·시빌워7편을 함께 선택합니다. 체크박스는12개입니다. 추가25인 전체 대사는1번도 함께 켜야 합니다.

원본34화 → 국지전35~39화 → 원본35화(표시40화) → **베오울프전41화「푸른 늑대의 잔향」** → 시빌워42~48화 → 원본36화(표시49화·최종전).

넓고 장애물이 적은 아인스트 공간에12기 선택 출격, 초기 적32기입니다. 아이젠10·녹헨8·리토6·게미유트6·레지세이아1·베오울프1로 구성했습니다. **베오울프 생존 중 일반 아인스트30기는 격파된 개체만 계속 보충됩니다. 베오울프 격파 시 증원 중지와 승리**이며 남은 적 전멸은 필요하지 않습니다. 레지세이아와 베오울프는 재생성하지 않습니다.

사용자가 OGs에서 제작한 기체·전용 무장6종·초상화·컷인15개 자료를 독립 이식했습니다. 기본HP135000, 베오울프 개조8/10단계, 일반 적6/8단계(적 강화OFF/ON)입니다. 기존 음성을 활용합니다. OGs 프로젝트와 ISO는 수정하지 않았습니다. [수치·전장·검증 범위](docs/beowulf-stage-v20261107.8.md)를 제공합니다.

기존5개 국지전의32기 편성·무인 보스10기와 추가25인 합류·밸런스·후속 대사를 유지합니다. 레몬·액셀렌의 인연을 포함한 추가 인물 대사는1번 옵션에 따릅니다. 본편 최종전과 결말을 보존합니다. [기존5편 전체 시나리오](docs/regional-five-v20261107.8.md)를 참고하세요.

**34화 종료 이벤트 이전부터12번을 켜고 모든 추가 전장을 마칠 때까지 유지하세요.** 이미 새 전장에 들어간 상태에서는 해제하지 마세요. 패치 후 완전히 새로 부팅하고 전장 진입 전 일반 세이브를 사용합니다.

선택 HD자료는 ZIP의 `textures/SLPS-25836/replacements/beowulf_mk3`에 PNG27개로 제공합니다. PCSX2의 텍스처 검색 폴더에 합쳐 설치하고 Load Textures를 켜세요. 전체 HD팩은 포함하지 않습니다.

'''
 rest=rest.replace('v20261107.2·.3·.4·.5·.6 적용본은','v20261107.2·.3·.4·.5·.6·.7 적용본은').replace('추가 전장11편','추가 전장13편').replace('시빌워5부작','시빌워7부작').replace('표시40·47화','표시40·49화')
 p.write_text((intro+rest).replace('시험판. ','').replace('시험판',''),encoding='utf8')
 p=REPO/'tools/README.md';s=p.read_text(encoding='utf8');s=s[:s.index('\n## 베오울프 결전과 개별 무한 증원')] if '\n## 베오울프 결전과 개별 무한 증원' in s else s;s+='''
## 베오울프 결전과 개별 무한 증원

`beowulf_source_image.py`는 OGs베오울프 배포 BIN의32번 프로필을 메모리에 겹쳐 읽으며 OGs ISO를 쓰지 않습니다. native body227, animation50참조(8재사용·42복제), cut-in15개·portrait를 별도 키로 가져옵니다. 원본 자원은 바이트 비교로 보존하며 기존face0만 디렉터리 확장 때문에 그대로 옮깁니다. 빈 공간만 사용하고 다른 전체ISO를 만들지 않습니다.

`beowulf_stage_content/policy.py`의2040은 original35→40→civil41,42,43,46,47,44,45→original36 경로입니다. 기존12번 bit11에 묶고 시빌워42~48화를 거쳐 original36 표시 화수는49입니다. 비활성화하면 원래34→35→36입니다. 1번은 새 인물 대사 가드를,5번은 일반6/8·베오울프8/10개조를 독립 제어합니다.

일반 적30기는UTbl1931..1960의독립alias로 기존 아인스트 기체 행을 참조합니다. `0x96`으로 살아 있는 개체 수를 얻고 `0x91`로 정확히0/1을 비교한 뒤 `0xCC`로 해당UNTD행12..41만 재등장시킵니다. `0x7A`는count<=N이므로boss<=1을생존조건으로사용하면안됩니다. 보스1930이없으면재증원하지않고승리합니다. 유한웨이브카운터는없습니다.

`validate_beowulf_stage.py`는 native단위수질의·LOGO등록·텍스트·준비생성과 맵 레코드 시험을 사용합니다. 실제CC맵생성서비스는시험상태로대체하고, NPC퇴장/재생성·충돌·AI·장기보상과 GPU연출을검증했다고주장하지않습니다. 전체원복SHA와4096프로필, 이전4096조합들의인식도검사합니다. legacy항목상한은32768입니다.
'''
 s+='''
## 시빌워 7부작과 자동 교전 대사

`civil_guard_content.py`와 `prepare_civil_guard.py`가 원래 시빌워에 두 경비대 전장을 더합니다. 키2041,2042,2043,2046,2047,2044,2045 순서로 표시42..48화이며 최종전은 원래2034(표시49화)입니다. 기존 bit11을공유합니다. `0x2A`의100A8파일럿 쌍 비교와 inline descriptor/0x3E를사용해 실제교전에만발동하며, 로컬플래그로반복을막습니다. 전역36,0/36,1은원래모든스크립트에서미사용임을확인했습니다.

임시편성은원래분기에서도쓰는0x4A 파일럿활성설정으로처리하고, 적대복제키1961..1992를독립사용합니다. 인질1996·중계기1993..1995와일반alias1997..2024를사용합니다. 원래 Unit/Plot/Weap행과9260개MAP/BATTLEpayload를보존합니다. `validate_civil_war.py`는native1210조건·교전104경우·준비생성320조건을, 별도party검사는75인육성과재합류를확인합니다. MAP행위자·AI·경로·렌더러·실제메모리카드는플레이확인이필요합니다.

정치와설득TXT는작성한팬시나리오입력이며게임대사덤프가아닙니다. 로컬중간자원·추출입력은공개하지않습니다.
'''
 s+='''
## 시빌워 턴별 전함 주변 증원

`civil_reinforcement_policy.py`는 기존 main행을 그대로 두고 native27/scene0 콜백3개를 끝에 추가합니다.2·3·4턴/아군진영의 필터5383e0과8014턴 레지스터를 함께 확인하며, 로컬3,0..2로중복을막습니다. CB는파일럿ID를받습니다. Tetsuya1137/Lefina1209를213f20으로검색하고2268e0으로현재좌표를얻은뒤2198c0에UNTD상대좌표를넘깁니다. 실제위치보정은원래223090입니다. 적의복제파일럿ID는다르므로아군함선으로잘못잡지않습니다. 전함없으면transportpilot1993으로대체합니다.증원용18개alias2025..2042와 초기 일반병 보충용2043..2044를UTbl에추가하며원래Unit/Plot/Weap행을변경하지않습니다.각UNTD63행중초기적은group0의32기이며추가18기는group2/3/4로예약됩니다. 실제맵생성·충돌·AI·렌더링·카드입출력은플레이확인이필요합니다.
'''
 s+='''

경비대 추가전장은45·46화에만 레피나 측 정규 경비대를 활성화하고47화 직전에 구출대·잠입조·데스피니스를 다시 활성화합니다. 일반병Lv52, 반란 지휘부Lv54입니다. 초기32기와 3차수 각6기, 전장별 최대50기입니다. 현재7편의 자원·편성 검증은 civil_guard 계열 검사를 기준으로 하며 앞선5편 검사는 역사적 범위입니다. 라그나로크는 원래 직접 연결되며 숙련도0을 포함한60개 진입 조합을 확인했습니다.
'''
 p.write_text(s,encoding='utf8');print('Repository source and release documents synchronized.',flush=True)
if __name__=='__main__':main()
