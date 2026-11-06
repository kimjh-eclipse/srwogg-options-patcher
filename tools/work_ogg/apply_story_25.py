"""Prepare/validate, then journal and update the single authorized OGG ISO."""
from story_scripts_25 import *
from story_master_25 import rebuild_master
from story_native_hooks import patches
from compare_ogs_units import getmaster
from apply_balance_25 import packed
import argparse,os

STATE=ROOT/'current_target.json'
JOURNAL=ROOT/'story_25_journal.json'
PREPARED=ROOT/'story_25_prepared.json'
PREP_DIR=OUT/'story_prepared'

def prepare():
 state=json.loads(STATE.read_text(encoding='utf8'));target=Path(state['canonical_iso'])
 assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO' and state['balance_25_applied']
 assert not state.get('story_25_applied'),'Story already installed; do not run a historical builder again'
 story=json.loads((ROOT/'story_plan_25_v1.json').read_text(encoding='utf8'))
 bal=json.loads((ROOT/'balance_plan_25_v1.json').read_text(encoding='utf8'))
 cast={r['pilot_name']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast'] if r['pilot_name'] not in ['아기라','세프타킨']}
 assert len(cast)==25 and set(cast)==set(ARRIVALS)==set(JOINS)
 grade={u['name']:u['initial_upgrade_grade'] for u in bal['units']}
 reference=getmaster(target);edits=[];masters={};meta={};chapters=[];PREP_DIR.mkdir(exist_ok=True)
 with target.open('rb') as f:
  for ar in ['SHARED.BIN','IM.BIN']:
   e=json.loads((OUT/(ar+'.3.json')).read_text())['entries'][0];old=read(f,e['offset'],e['size']);new,note=rebuild_master(old,cast,reference)
   edits.append((e['offset'],old,new,ar+' pilot balance and phased weapons'));masters[ar]=new;meta[ar]=note
   (PREP_DIR/(ar+'.master')).write_bytes(new)
  ua,ue=loadarc(f,13);la,le=loadarc(f,14)
  unitdata={ks[0]:read(f,p,n) for ks,p,n in ue};logodata={ks[0]:read(f,p,n) for ks,p,n in le}
  for key,b in unitdata.items():
   if len(b)!=44+u32(b,40)*336:continue
   for i in range(u32(b,40)):
    assert all(u32(b,44+i*336+k)<0x80000000 for k in [0x50,0x54,0x58]),('stock EXP uses sentinel',key,i)
  # Durable unused Diff flag bytes 60..63 (480..511); local register 15 is unused.
  for key,b in logodata.items():
   if b[:4]!=b'LOGO':continue
   for r in records(b):
    assert not (r[2]==0x100c1 and r[3]>=60),('reserved flag collision',key)
    assert 0x800f not in r,('temporary register collision',key)
  speakers=resolve_speakers(reference,cast,list(unitdata.values()))
  b=unitdata[2001];templates={u32(b,44+i*336):b[44+i*336:44+(i+1)*336] for i in range(u32(b,40)) if u32(b,44+i*336) in [v['new_key'] for v in cast.values()]}
  assert len(templates)==25
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);tiledata={k:read(f,p,n) for ks,p,n in mt for k in ks}
  tiles={}
  for ks,p,n in mi:
   raw=read(f,p,n);mk=u32(raw,12)
   if mk in tiledata:
    for k in ks:tiles[k]=tiledata[mk]
  active=sorted({r['arrival'] for r in story['characters']}|{r['playable'] for r in story['characters']}|set(FOLLOWUPS))
  assert len(active)<=32 and not (set(active)&set(range(10,15))) and not (set(active)&{16,17,18})
  cursor=0x1b080000;limit=0x1b594000;spans={13:0,14:0}
  def relocate(slot,key,blob,label):
   nonlocal cursor
   cursor=(cursor+2047)&~2047;assert cursor+len(blob)<=limit
   old=read(f,cursor,len(blob));assert not any(old),('allocation is not empty',hex(cursor))
   a=ua if slot==13 else la;e=next(x for x in a['entries'] if key in x['keys']);dp=a['directory']+8+e['index']*8
   edits.append((cursor,old,blob,label));edits.append((dp,read(f,dp,8),struct.pack('<II',cursor-a['directory'],len(blob)),label+' directory'))
   spans[slot]=max(spans[slot],cursor+len(blob)-a['directory']);at=cursor;cursor+=len(blob);return at
  for num,ch in enumerate(active):
   key=CHAPTER_KEYS[ch];old=logodata[key];arr=[r['name'] for r in story['characters'] if r['arrival']==ch];joins=[r['name'] for r in story['characters'] if r['playable']==ch]
   lines=[]
   for name in arr:lines.extend(ARRIVALS[name])
   for name in joins:lines.extend(JOINS[name])
   lines.extend(FOLLOWUPS.get(ch,[]))
   flag=(60+num//8,num%8);group=None;unotes=[]
   if joins:
    occupied={u32(unitdata[key],44+i*336+4) for i in range(u32(unitdata[key],40))}
    group=next(x for x in range(32,128) if x not in occupied)
    ub,unotes=join_units(unitdata[key],joins,templates,cast,{**grade,'chapter':ch},group,tiles)
    up=relocate(13,key,ub,f'chapter {ch} allied recruitment');(PREP_DIR/f'{key}.untd').write_bytes(ub)
   point=find_point(old,ch);new,notes=rebuild_logo(old,point,lines,speakers,flag,group)
   lp=relocate(14,key,new,f'chapter {ch} original Korean story');(PREP_DIR/f'{key}.logo').write_bytes(new)
   chapters.append(dict(chapter=ch,key=key,arrivals=arr,recruits=unotes,logo_offset=lp,logo_size=len(new),**notes))
  # The first-chapter gallery is retired: reconnect the untouched original payloads.
  with SOURCE.open('rb') as source:
   for slot,a in [(13,ua),(14,la)]:
    e=next(x for x in a['entries'] if 2001 in x['keys']);dp=a['directory']+8+e['index']*8;original_entry=read(source,dp,8)
    off,n=struct.unpack('<II',original_entry);assert read(f,a['directory']+off,n)==read(source,a['directory']+off,n)
    edits.append((dp,read(f,dp,8),original_entry,f'chapter 1 restore original {slot}'))
  for slot,a in [(13,ua),(14,la)]:
   dp=0x11a94800+8+slot*8+4
   span=max(u32(read(f,dp,4)),spans[slot]);edits.append((dp,read(f,dp,4),struct.pack('<I',span),f'MAP archive {slot} span'))
  elf=next(e for e in inventory(f) if e['name'].startswith('SLPS_'))
  eb=read(f,elf['offset'],elf['size']);assert u32(eb,u32(eb,28)+4)==0x180
  for va,new,label in patches((OUT/'terrain_fresh_ram.bin').read_bytes()):
   pos=elf['offset']+0x180+va-0x100000;old=read(f,pos,len(new));snap=(OUT/'terrain_fresh_ram.bin').read_bytes()[va:va+len(new)]
   assert old==snap,('executable differs from tested native code',hex(va));edits.append((pos,old,new,label))
 edits=[e for e in edits if e[1]!=e[2]];edits.sort()
 for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0],('overlapping edits',x[3],y[3])
 assert all(len(a)==len(b) for o,a,b,label in edits)
 report=dict(target=str(target),source_sha256=state['current_sha256'],applied=False,live_playthrough_verified=False,
             lineups=25,chapters=chapters,master_changes=meta,spirit_cost_one_preserved=True,
             chapter_one_original=True,speakers=speakers,allocation_end=cursor,allocation_limit=limit,
             modified_bytes=sum(len(a) for o,a,b,l in edits),edited_regions=len(edits))
 PREPARED.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 return target,edits,report

def apply(target,edits,report,validation):
 assert validation['passed'] and not JOURNAL.exists()
 state=json.loads(STATE.read_text(encoding='utf8'));expected=report['source_sha256']
 assert state['current_sha256']==expected
 with target.open('r+b') as f:
  print('Verifying canonical ISO hash...',flush=True);assert hashlib.file_digest(f,'sha256').hexdigest()==expected
  for o,a,b,l in edits:assert read(f,o,len(a))==a
  journal={**report,'validation':validation,'encoding':'zlib+base64','edits':[dict(offset=o,size=len(a),label=l,before_zlib_base64=packed(a),after_zlib_base64=packed(b)) for o,a,b,l in edits]}
  JOURNAL.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for o,a,b,l in edits:f.seek(o);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());print('Verifying every edit and all other image bytes...',flush=True)
   digest=hashlib.sha256();inverse=hashlib.sha256();pos=0;f.seek(0)
   for o,a,b,l in edits:
    while pos<o:
     raw=f.read(min(4<<20,o-pos));assert raw;digest.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;digest.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(4<<20):digest.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==expected
  except BaseException:
   for o,a,b,l in edits:f.seek(o);f.write(a)
   f.flush();os.fsync(f.fileno());raise
 journal.update(applied=True,target_sha256=digest.hexdigest(),all_other_image_bytes_preserved=True)
 JOURNAL.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
 report.update(applied=True,target_sha256=digest.hexdigest());PREPARED.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 state.update(current_sha256=digest.hexdigest(),story_25_applied=True,first_chapter_showcase=False,
              balance_stage='chapter-based recruitment, initial upgrades, phased weapons and pilot balance',last_edit_journal=str(JOURNAL))
 STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 p=ROOT/'AGENTS.md';t=p.read_text(encoding='utf8').replace(expected,digest.hexdigest())
 t=t.replace('The canonical test ISO contains the selected 25 chapter-one lineups','The canonical test ISO contains 25 additional lineups recruited progressively from chapter 4')
 t=t.replace('Chapter recruitment/upgrade grants/unlocks remain pending story implementation.','Chapter recruitment, upgrade grants and repaired-weapon unlocks are applied; see story_25_journal.json.')
 t+='\n- The chapter-one gallery is removed. New dialogue starts in chapter 3; all 25 recruits join by chapter 31. Pilot base stats are normalized, starting EXP matches owned pilots, and Rin/Wodan finishers unlock in chapters 15/19. Begin a new game; old gallery saves/states are not a supported starting point. Native offline checks passed; a live PCSX2 playthrough remains unverified.\n';p.write_text(t,encoding='utf8')
 for name in ['story_plan_25_v1.json','balance_plan_25_v1.json']:
  p=ROOT/name;d=json.loads(p.read_text(encoding='utf8'));d.update(status='화별 추가 대화·합류·초기 개조·무장 해금·파일럿 조정 적용. 새 게임 권장. 실기 전체 진행 검증 미완료.',applied_iso=str(target),applied_sha256=digest.hexdigest(),story_journal=str(JOURNAL),deferred=[]);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 write_notes(report,digest.hexdigest())
 return digest.hexdigest()

def write_notes(report,digest):
 story=json.loads((ROOT/'story_plan_25_v1.json').read_text(encoding='utf8'))
 grades={r['name']:r['initial_upgrade'] for c in report['chapters'] for r in c['recruits']}
 lines=['OG외전 25편성 분산 합류 — 현재 ISO 적용 내역',
        '대상: '+report['target'],'SHA-256: '+digest,'',
        'PCSX2에서 ISO를 완전히 새로 부팅한 뒤 새 게임으로 시작하세요.',
        '1화 전원 배치 시험판의 세이브/스테이트는 이번 분산 합류판의 시작점으로 지원하지 않습니다.',
        '원본 ISO와 메모리 카드/저장 파일은 수정하지 않았습니다. 추가 전체 ISO를 만들지 않았습니다.','',
        '적용 내용',
        '- 1화의 추가 25기 배치를 해제하고 기존 아군 배치로 복구.',
        '- 3화부터 전이 대화 시작. 4~31화에 25편성 분산 합류.',
        '- 22개 화에 한국어 대화 상자 '+str(sum(len(c['messages']) for c in report['chapters']))+'개 추가.',
        '- 죽기 직전 다른 세계에서 전이되었다는 공통 설정. 원래 생존 인물의 위기는 창작 분기.',
        '- 레몬의 죽은 여동생과 지금의 액셀렌을 구별하면서 새 자매의 관계를 선택하는 후속 대화.',
        '- 합류 화에 따라 기체·고정 무장을 0/2/3/4단으로 초기 개조. 이후 플레이어 개조 유지.',
        '- 합류 시 경험치를 보유 파일럿 평균에 맞춤. 기존 인물의 레벨·능력치는 유지.',
        '- 린 블랙홀 캐논 15화, 워단 최종 참함도 19화 해금. 정비 중에는 기력 255로 사용 제한.',
        '- 추가 25명의 기본 능력치와 성장형을 원래 아군 범위로 조정. 이글렛의 0 능력치 보완.',
        '- 기존 기체 밸런스, SP1, 전투 한글 자막, 지형명과 커서 도움말 한글화 유지.','',
        '등장 화에서는 기존 인물 초상과 통신 대화로 전이를 묘사하고, 조작 가능 화에 실제 아군 기체를 배치합니다.',
        '합류 장면은 해당 화의 기존 증원 대화에 연결했습니다. 원래 적 배치·승패 조건은 유지합니다.',
        '합류는 별도 격추/설득 조건 없이 해당 이벤트 진행 시 자동입니다.',
        '10~14화의 두 분기와 16~18화의 독립 부대 시나리오는 원래 구성을 유지합니다.','',
        '인물 / 기체 / 첫 대화 / 조작 가능 / 초기 개조']
 for r in sorted(story['characters'],key=lambda r:(r['playable'],r['roster_no'])):
  lines.append(f"{r['name']} / {r['robot']} / {r['arrival']}화 / {r['playable']}화 / {grades[r['name']]}단")
 lines+=['','검증',
         '오프라인으로 실제 게임의 기체·파일럿 조회, UNTD 등록, 경험치, 개조, 무장 해금, 중복 합류 방지와 문자열/대화 이력을 검사했습니다.',
         'ISO 전체의 역변환 SHA-256으로 지정한 영역 외의 바이트가 이전 파일과 같음을 확인했습니다.',
         'PCSX2에서 전체 36화를 진행하거나 실제 지도 이동/애니메이션을 재생한 검증은 아직 하지 않았습니다.',
         '상세 검사: story_25_validation.json / 되돌리기용 변경 기록: story_25_journal.json']
 (ROOT/'OG외전_25편성_적용내역.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
 dialogue=['OG외전 25편성 — 실제 추가 대사','']
 for c in report['chapters']:
  dialogue.append(f"【{c['chapter']}화】")
  for msg in c['messages']:dialogue.extend([msg['text'].replace('　',' ').replace('@','\n'),''])
 (ROOT/'OG외전_25편성_적용대사.txt').write_text('\n'.join(dialogue),encoding='utf-8-sig')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 target,edits,report=prepare()
 from validate_story_25 import validate
 validation=validate(report)
 summary={k:v for k,v in validation.items() if k!='recruitment'}
 summary['recruits']=len(validation['recruitment']['recruits']);summary['duplicate_event_checks']=validation['recruitment']['second_invocations_skipped'];summary['weapon_upgrade_checks']=validation['recruitment']['weapon_upgrade_checks']
 print(json.dumps(dict(chapters=len(report['chapters']),messages=sum(len(c['messages']) for c in report['chapters']),modified_bytes=report['modified_bytes'],validation=summary),ensure_ascii=False,indent=2),flush=True)
 if args.apply:print('APPLIED',apply(target,edits,report,validation),flush=True)
 else:print('Prepared only. ISO untouched.',flush=True)

if __name__=='__main__':main()
