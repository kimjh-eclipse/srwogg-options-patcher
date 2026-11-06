"""Apply the user's cumulative reward/balance request to the canonical ISO only."""
from campaign_native_tuning import native_plan
from campaign_bonus_scripts import hidden_plan,enemy_upgrade_plan,TARGET,ROOT,OUT
from campaign_weapon_tuning import weapon_plan
from validate_campaign_tuning import resources,initializer_checks,hostile_checks,reward_checks,grants_checks,spawn_checks,weapon_checks,script_text_checks
from apply_balance_25 import packed,read,hashlib,json
from pathlib import Path
import argparse,os

STATE=ROOT/'current_target.json'
JOURNAL=ROOT/'campaign_tuning_journal.json'
PREPARED=ROOT/'campaign_tuning_prepared.json'
VALIDATION=ROOT/'campaign_tuning_validation.json'

def prepare():
 state=json.loads(STATE.read_text(encoding='utf8'));target=Path(state['canonical_iso'])
 assert target==TARGET and state['story_25_applied'] and not state.get('campaign_tuning_applied')
 native,native_notes=native_plan(target);hidden,hidden_notes=hidden_plan(target)
 weapons,weapon_notes=weapon_plan(target);upgrades,upgrade_notes=enemy_upgrade_plan(target)
 edits=sorted(native+hidden+weapons+upgrades)
 for a,b in zip(edits,edits[1:]):assert a[0]+len(a[1])<=b[0],('overlapping edits',a[3],b[3])
 assert all(len(a)==len(b) for off,a,b,label in edits)
 report=dict(target=str(target),source_sha256=state['current_sha256'],applied=False,live_playthrough=False,
             native=native_notes,hidden=hidden_notes,weapons=weapon_notes,enemy_upgrade_tables=upgrade_notes,
             enemy_upgrade_rows=len(upgrades),edited_regions=len(edits),changed_region_bytes=sum(len(a) for off,a,b,label in edits),
             PP_multiplier=2,funds_multiplier=[6,5],enemy_stat_add=5,enemy_upgrade_add=2,small_enemy_base_HP_add_percent=10)
 PREPARED.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 return target,edits,report

def validate(target,edits,report):
 rams=resources(target,edits)
 result=dict(passed=False,live_playthrough=False)
 result['initializers_equivalent']=initializer_checks(rams)
 result['hostile_stats_and_HP']=hostile_checks(rams)
 result['battle_rewards']=reward_checks(rams)
 result['grants']=grants_checks(report['hidden'])
 result['native_new_text_and_history']=script_text_checks(report['hidden'])
 print('Reward, hidden-item, hostile-stat and text checks passed. Checking all spawn difficulties...',flush=True)
 result['enemy_upgrades']=spawn_checks(rams)
 result['weapons']=weapon_checks(edits,report['weapons'])
 result.update(passed=True,enemy_rows_patched=report['enemy_upgrade_rows'],original_25_ally_spawns_preserved=True)
 VALIDATION.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 return result

def notes(report,digest):
 lines=['OG외전 — 보상·밸런스 추가 적용 내역','대상: '+report['target'],'SHA-256: '+digest,'',
  '실행: PCSX2에서 ISO를 완전히 재부팅한 뒤 게임 내 일반 세이브로 불러오세요.',
  '3화 지급은 3화 이벤트가 지나기 전의 저장 또는 새 게임에서 받을 수 있습니다.',
  '기존 1화 전원 배치판에서 이어지는 세이브는 앞선 분산 합류판 안내대로 새 게임이 필요합니다.','',
  '3화 추가 지급 — 각 1개, 한 번만 지급',
  '시시오 블레이드 / 부스트 해머 / 강철의 혼 / 용자의 인 / 고성능 전자두뇌 / 메가 제네레이터 / 부스터 / 메가 부스터','',
  '숨겨진 보상 조건 해제',
  '- 6화 클리어: 고성능 전자두뇌. 특정 건물에 이동할 필요 없이 지급.',
  '- 13화 클리어: 미롱가. 지상·우주 양쪽 루트에서 지급. 숙련도와 발시오네 격추 조건 해제.',
  '- 25화 클리어: 시시오 블레이드·용자의 인. 레벨 합계 조건 해제.',
  '- 30화 클리어: 부스트 해머·강철의 혼. 레벨·격추수 조건 해제.',
  '3화 추가 지급과 원래 시점의 자동 획득은 별도입니다. 나중에 같은 무장·파츠를 한 개 더 받습니다.','',
  '전투 보상',
  '- 기존 보너스와 분배를 계산한 뒤 PP ×2, 자금 ×1.2. 자금 소수점은 버립니다.',
  '- 훈련·행운·에이스·트윈·MAP·복수 파일럿 분배와 최소 PP 처리를 유지합니다.','',
  'OGs 공통 밸런스 이식',
  '- 적 파일럿의 격투·사격·기량·방어·명중·회피 +5. 현재 적대 관계를 기준으로 적용.',
  '- 적 기체·무장 기본 개조 +2단계. 세 난이도 모두 적용, 15단계 상한 유지.',
  '- 기본 HP가 1~19,999인 적의 기본 HP +10%. 개조와 난이도 가산은 기존 방식 유지.',
  '- 다이젠가·아우센자이터·알트아이젠 리제 등의 공통 무장 조정과 그룬가스트·지간스쿠드 소모량 조정.',
  '- 외전 고유의 무장 강화분을 유지하며 OGs에서 바꾼 공격력 증감량을 적용.',
  '- 무장 개조비 1~4번 비용표 20% 할인. 가장 저렴한 0번 비용표는 기존 가격.',
  '- 앞서 조정한 추가 25편성의 기체·파일럿·독립 무장과 화별 합류는 유지.','',
  '공통 무장 상세 (기본 공격력 / EN / 필요 기력)']
 for w in report['weapons']['weapons']:
  lines.append(f"{w['name']}: 공격력 {w['power_before']}→{w['power_after']}, EN {w['en_before']}→{w['en_after']}, 기력 {w['morale_before']}→{w['morale_after']}")
 lines+=['','검증',
  '실제 OGG 코드로 보상 계산 44가지, 적 능력치 72가지, HP 168가지와 실제 HP 조회 8가지, 출격 생성 72가지, 무장 조회 432가지를 검사했습니다.',
  '초기화 코드를 줄인 두 구간은 원래와 최종 레지스터·FPR·메모리 쓰기가 같음을 확인했습니다.',
  '실제 지급 명령으로 8종 각 1개와 재지급 방지, 미롱가 중복 방지를 확인했습니다.',
  'ISO 전체 역변환 SHA-256으로 지정한 영역 외 모든 바이트가 적용 전과 같음을 확인했습니다.',
  'PCSX2에서 전체 게임을 진행한 실플레이 검증은 아직 하지 않았습니다.',
  '상세 검증: campaign_tuning_validation.json / 되돌리기용 기록: campaign_tuning_journal.json']
 (ROOT/'OG외전_보상_밸런스_적용내역.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')

def apply(target,edits,report,validation):
 assert validation['passed'] and not JOURNAL.exists()
 state=json.loads(STATE.read_text(encoding='utf8'));expected=report['source_sha256'];assert state['current_sha256']==expected
 import psutil
 assert not any('pcsx2' in p.name().lower() for p in psutil.process_iter()),'PCSX2 must be closed before writing'
 with target.open('r+b') as f:
  print('Verifying canonical ISO hash...',flush=True);assert hashlib.file_digest(f,'sha256').hexdigest()==expected
  for off,a,b,label in edits:assert read(f,off,len(a))==a,(label,hex(off))
  journal={**report,'validation':validation,'encoding':'zlib+base64','edits':[dict(offset=off,size=len(a),label=label,before_zlib_base64=packed(a),after_zlib_base64=packed(b)) for off,a,b,label in edits]}
  JOURNAL.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for off,a,b,label in edits:f.seek(off);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());print('Verifying every edit and all other image bytes...',flush=True)
   digest=hashlib.sha256();inverse=hashlib.sha256();pos=0;f.seek(0)
   for off,a,b,label in edits:
    while pos<off:
     raw=f.read(min(4<<20,off-pos));assert raw;digest.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;digest.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(4<<20):digest.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==expected
  except BaseException:
   for off,a,b,label in edits:f.seek(off);f.write(a)
   f.flush();os.fsync(f.fileno());raise
 digest=digest.hexdigest();journal.update(applied=True,target_sha256=digest,all_other_image_bytes_preserved=True)
 JOURNAL.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
 report.update(applied=True,target_sha256=digest);PREPARED.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 state.update(current_sha256=digest,campaign_tuning_applied=True,hidden_six_guaranteed=True,chapter_three_eight_supplies=True,battle_PP_multiplier=2,battle_funds_multiplier=1.2,enemy_strength={'pilot_stats':5,'upgrades':2,'small_base_HP_percent':10},common_weapon_tuning=True,weapon_upgrade_discount=True,last_edit_journal=str(JOURNAL))
 STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 p=ROOT/'AGENTS.md';t=p.read_text(encoding='utf8').replace(expected,digest)
 t+='\n- Campaign tuning is applied: chapter 3 grants eight requested supplies once; six hidden rewards are guaranteed at their natural chapters (Mironga on either chapter-13 route); final battle PP x2 / money x1.2; hostile pilot stats +5, base HP below 20000 +10%, enemy UNTD body/weapons +2 capped at 15; common OGs weapon adjustments and non-cheapest weapon cost tiers -20%. Additional 25-unit balance/story preserved. See campaign_tuning_journal.json and campaign_tuning_validation.json. Cold boot required; gifts do not retroactively replay past events.\n'
 p.write_text(t,encoding='utf8')
 p=ROOT/'OG외전_25편성_적용내역.txt'
 if p.exists():
  t=p.read_text(encoding='utf-8-sig').replace(expected,digest);t+='\n추가 보상·밸런스 적용: OG외전_보상_밸런스_적용내역.txt 참고\n';p.write_text(t,encoding='utf-8-sig')
 notes(report,digest)
 return digest

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 target,edits,report=prepare();validation=validate(target,edits,report)
 print(json.dumps(dict(prepared=True,regions=len(edits),bytes=report['changed_region_bytes'],enemy_rows=report['enemy_upgrade_rows'],common_weapons=len(report['weapons']['weapons']),validation_passed=validation['passed']),ensure_ascii=False,indent=2),flush=True)
 if args.apply:print('APPLIED',apply(target,edits,report,validation),flush=True)
 else:print('Prepared only. ISO untouched.',flush=True)

if __name__=='__main__':main()
