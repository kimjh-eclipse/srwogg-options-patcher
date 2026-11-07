"""Build a twelve-option patch without ever creating another full ISO."""
from pathlib import Path
import sys,struct,json,hashlib,zlib,base64,bisect,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import Master,u16
from spirit_policy_25 import POLICY,apply_to_row
from support_overhaul_policy import SUPPORT_FLAG,MAINTENANCE_FLAG,SUPPORT_NATIVE
from party_policy_25 import edits_for_master,native_recovery,NATIVE_RECOVERY
from inspect_iso import ROOT,OUT,SOURCE,read,u32,inventory,lice
from audit_story_layout import TARGET,loadarc
from story_scripts_25 import records,rebuild_logo,command,NONE
from campaign_bonus_scripts import insert_commands,EARLY
from early_equipment_policy import FLAG as EARLY_FLAG,script as early_script
import numpy as np
sys.path.insert(0,str(ROOT/'upstream_base'))
from source_image import source_image,DATA as BASE_INFO,CHANGES as BASE_CHANGES

HERE=Path(__file__).resolve().parent
VERSION='v20261107.8'
DIST=ROOT/('release_'+VERSION)
OLD_PACK=ROOT/'release_v20261106/patcher/OGG_options.bin'
PREVIOUS_PACK=ROOT/'release_v20261106.5/patcher/OGG_options.bin'
PREVIOUS_BEOWULF_PACK=ROOT/'release_v20261107.5/patcher/OGG_options.bin'
PREVIOUS_INTERMISSION_PACK=ROOT/'release_v20261107.6/patcher/OGG_options.bin'
PREVIOUS_CIVIL_WAR_PACK=ROOT/'release_v20261107.7/patcher/OGG_options.bin'
PREVIOUS_DENSITY_PACK=ROOT/'release_v20261107.4/patcher/OGG_options.bin'
PREVIOUS_BOSSES_PACK=ROOT/'release_v20261107.3/patcher/OGG_options.bin'
PREVIOUS_REGIONAL_PACK=ROOT/'release_v20261107.2/patcher/OGG_options.bin'
PREVIOUS_ELEVEN_PACK=ROOT/'release_v20261107.1/patcher/OGG_options.bin'
PREVIOUS_TEN_PACK=ROOT/'release_v20261107/patcher/OGG_options.bin'
CONSISTENCY_PACK=ROOT/'release_v20261106.4/patcher/OGG_options.bin'
PARTY_PACK=ROOT/'release_v20261106.3/patcher/OGG_options.bin'
SPIRITS_PACK=ROOT/'release_v20261106.2/patcher/OGG_options.bin'
OLDER_PACK=ROOT/'release_v20261106.1/patcher/OGG_options.bin'
PATCHER=DIST/'patcher'
OPTIONS=[
 ('25편성 분산 합류·추가 시나리오','3화 전이 대화, 4~31화 합류. 기체 밸런스·본편 연결·관계 후속 장면 포함'),
 ('숨겨진 요소 자동 습득','6·13·25·30화 보상 조건 해제. 미롱가는 양쪽 루트에서 입수'),
 ('3화 추가 보급 8종','시시오 블레이드·부스트 해머와 강화파츠 6종을 각 1개 지급'),
 ('전투 보상: PP 2배·자금 +20%','기존 보너스와 분배 계산 후 적용. 자금 소수점 버림'),
 ('적 강화','전투 능력치 +5, 기체·무장 개조 +2, 기본 HP 2만 미만 +10%'),
 ('공통 무장 밸런스','OGs 공통 무장 조정 이식. 외전 고유의 강화분 유지'),
 ('무장 개조비 할인','OGs 최종 비용표: 0·1등급 동일, 10단계 88,000 / 105,600 / 176,000'),
 ('4화 수리·보급장치 추가','수리장치·보급장치 각1개. 시나리오 선택과 별개로 한 번 지급'),
 ('30화부터 일부 기체 정비','추가 아군6기의 무장9종 EN·탄수 소폭 개선. 기본 화력 유지'),
 ('3화 기체·무장 조기 입수','빌트팔켄 L·아슈세이버·휴케바인 Mk-3 R 각1기와 무장2종. 파일럿 추가 없음'),
 ('휴케바인 Mk-3 R 무장 +200','기본 장착 무장5종 공격력 +200. 조기 입수와 독립 선택, 다른 기체의 원래 무장 유지'),
 ('추가 전장 13편·시빌워·베오울프','국지전·베오울프·시빌워7편. 일반병Lv52,2·3·4턴마다 전함 주변6기 증원')]

def unpack(e,side):
 if side in e:return bytes.fromhex(e[side])
 return zlib.decompress(base64.b64decode(e[side+'_zlib_base64']))

def rawmaster(f,name):
 e=next(e for e in inventory(f) if e['name']==name+';1');a=lice(f,e['offset'],e['size']);e=a['entries'][3];a=lice(f,e['offset'],e['size']);e=a['entries'][0]
 return e,Master(read(f,e['offset'],e['size']))

def plan():
 # Common includes translations, unused clone resources and verified equivalent
 # initializer helpers. Only reachable feature entry points are optional.
 common=[];features=[[] for _ in OPTIONS];off=[[] for _ in OPTIONS];proof={}
 campaign=json.loads((ROOT/'campaign_tuning_journal.json').read_text(encoding='utf8'))
 story=json.loads((ROOT/'story_25_journal.json').read_text(encoding='utf8'))
 with source_image() as original,TARGET.open('rb') as current:
  ua,ue=loadarc(current,13);la,le=loadarc(current,14)
  maintenance=json.loads((ROOT/'support_overhaul_prepared.json').read_text(encoding='utf-8'));support={s['label']:s for s in maintenance['scripts']};native_support=support['support_native'];common.append((SUPPORT_NATIVE,read(current,SUPPORT_NATIVE,native_support['size'])))
  def locate(entries,key):return next(e for e in entries if key in e[0])
  def dp(a,key):return a['directory']+8+next(e['index'] for e in a['entries'] if key in e['keys'])*8
  def switch(bit,at,zero,one):
   assert len(zero)==len(one)
   if zero!=one:off[bit].append((at,bytes(zero)));features[bit].append((at,bytes(one)))
  def record_switch(bit,bp,base,i,zero,one):switch(bit,bp+u32(base,44)+i*96,struct.pack('<24I',*zero),struct.pack('<24I',*one))
  # Build the independent no-story chapter-three supply script in unused MAP space.
  p3=dp(la,2003);origptr=read(original,p3,8);rel,n=struct.unpack('<II',origptr);vanilla=read(original,la['directory']+rel,n)
  wave=next(i for i,r in enumerate(records(vanilla)) if r[0]==0xca and r[2]==5)
  end=next(i for i in range(wave+1,len(records(vanilla))) if records(vanilla)[i][0]==0x25)
  point=max(i for i in range(wave+1,end) if records(vanilla)[i][0]==0x30)+1
  line=[('카이','보급품을 인계한다. 시시오 블레이드, 부스트 해머와 강화파츠 여섯 종류를 각각 하나씩 지급한다.')]
  new,note=rebuild_logo(vanilla,point,line,{'카이':1090},(63,7))
  ix=next(i for i,r in enumerate(records(new)) if r[0]==0xba and r[2:5]==[0x100c1,63,7])
  new=insert_commands(new,ix,[command(op,key,0) for op,key,name in EARLY])
  new,early_note=early_script(new)
  allocation=0x1b480000;assert not any(read(current,allocation,len(new))) and allocation+len(new)<0x1b594000
  recovery,recovery_ptr=native_recovery(original,la);common.append((NATIVE_RECOVERY,recovery))
  common.append((allocation,new));newptr=struct.pack('<II',allocation-la['directory'],len(new))
  for slot,a in [(13,ua),(14,la)]:
   for chapter in story['chapters']:
    if slot==13 and not chapter['recruits']:continue
    at=dp(a,chapter['key']);zero=read(original,at,8);one=read(current,at,8)
    if slot==14 and chapter['key']==2003:zero=newptr
    if slot==14 and chapter['key']==2026:zero=recovery_ptr
    if slot==14 and chapter['key']==2032:
     regional=json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8'));nb=next(s for s in regional['bridge'] if s['mode']=='native');zero=struct.pack('<II',nb['offset']-la['directory'],nb['size'])
    if slot==14 and chapter['key']==2050:zero=bytes.fromhex(native_support['pointer_hex'])
    switch(0,at,zero,one)
  # Chapter32 gains dialogue only; its UNTD stays native.
  at=dp(la,2030);switch(0,at,read(original,at,8),read(current,at,8))
  # Both chapter-three variants contain a guarded supply block. Disabling the
  # option compares a 0/1 flag to 2, so the whole block remains unreachable.
  _,p,n=locate(le,2003)
  for base,blob in [(p,read(current,p,n)),(allocation,new)]:
   rows=records(blob);ix=next(i for i,r in enumerate(rows) if r[0]==0x93 and r[2:5]==[0x100c1,63,7]);cond=rows[ix+1].copy();assert cond[0]==0x91 and cond[4]==0
   disabled=cond.copy();disabled[4]=2;record_switch(2,base,blob,ix+1,disabled,cond)
  for base,blob in [(p,read(current,p,n)),(allocation,new)]:
   rows=records(blob);ix=next(i for i,r in enumerate(rows) if r[0]==0x93 and r[2:5]==[0x100c1,*EARLY_FLAG]);cond=rows[ix+1];disabled=cond.copy();disabled[4]=2;record_switch(9,base,blob,ix+1,disabled,cond)
  # Hidden conditions in original and additional-story payloads are independent
  # of which script directory entry the story checkbox selects.
  for key,grants in [(2005,[(0x60,31,[-1])]),(2023,[(0x64,3513,[-1]),(0x60,32,[-1])]),(2028,[(0x64,3530,[-1]),(0x60,33,[-5,-1])])]:
   at=dp(la,key);rel,n=struct.unpack('<II',read(original,at,8));oldp=la['directory']+rel;old=read(original,oldp,n);rows=records(old)
   for op,item,deltas in grants:
    gi=next(i for i,r in enumerate(rows) if r[0]==op and r[2]==item)
    for delta in deltas:
     zero=rows[gi+delta];assert zero[0] in [0x91,0x2b]
     _,p,n=locate(le,key);cur=read(current,p,n);ri=next(i for i,r in enumerate(records(cur)) if r[0]==op and r[2]==item)
     for bp,blob,index in [(oldp,old,gi+delta),(p,cur,ri+delta)]:record_switch(1,bp,blob,index,zero,command(0x8a))
  # Chapter 13's common scripts retain the stock recovery scene and metadata.
  # Only the successful-result override and idempotent extra grant are optional.
  _,p,n=locate(le,2012);cur=read(current,p,n);r=records(cur)
  rel,size=struct.unpack('<II',read(original,dp(la,2012),8));stock=read(original,la['directory']+rel,size);sr=records(stock)
  record_switch(1,p,cur,872,sr[872],r[872]);record_switch(1,p,cur,898,sr[898],r[898])
  ix=next(i for i,row in enumerate(r) if row[0]==0x5f and row[2]==1410);record_switch(1,p,cur,ix,command(0x8a),r[ix])
  _,p,n=locate(le,2054);cur=read(current,p,n);r=records(cur);ix=next(i for i,row in enumerate(r) if row[0]==0x93 and row[2:5]==[0x100c1,63,6]);disabled=r[ix+1].copy();disabled[4]=2;record_switch(1,p,cur,ix+1,disabled,r[ix+1])
  # Optional hooks share verified-equivalent helpers, which stay common.
  for e in campaign['edits']:
   label=e['label'];bit=None
   if label in ['scale final funds before accumulation','preserve PP accumulator load in common minimum-check delay','double each final PP award in temporary','accumulate scaled PP without changing shared per-pilot amount']:bit=3
   elif label in ['hostile pilot combat stat +5','hostile small-unit HP hook']:bit=4
   elif 'common weapon key' in label:bit=5
   elif label in ['weapon upgrade cost tiers 1-4 minus 20 percent','weapon upgrade cost OGs final tiers 0-4']:bit=6
   if bit is not None:
    before=unpack(e,'before');after=unpack(e,'after')
    if bit==6:after=struct.pack('<80I',*(step*i for step in (1600,1600,1920,3200,3200) for i in range(16)))
    address=e['offset']
    if bit==5:
     # Unit/weapon additions relocate the master tables. Resolve the semantic
     # weapon ID instead of retaining an address from an older master layout.
     archive=label.split()[0];key=int(label.rsplit(' ',1)[1]);entry,master=rawmaster(current,archive);index=u16(master.b,master.tables['WTbl'][0]+12+key*2)
     assert index<master.tables['Weap'][2] and len(after)==36
     address=entry['offset']+master.tables['Weap'][0]+12+index*36
     assert read(current,address,36)==after
    switch(bit,address,before,after)
  # Patch both original and story-specific enemy records. Otherwise changing
  # the story checkbox could silently select an unstrengthened copy.
  seen=set()
  for keys,p,n in ue:
   if not any(2001<=k<=2070 for k in keys):continue
   key=next(k for k in keys if 2001<=k<=2070)
   if key in range(2035,2048):continue
   at=dp(ua,key);rel,size=struct.unpack('<II',read(original,at,8));stock=read(original,ua['directory']+rel,size)
   for bp,blob in [(ua['directory']+rel,stock),(p,read(current,p,n))]:
    for i in range(u32(stock,40)):
     pos=44+i*336
     if u32(stock,pos+8) not in [2,3,4]:continue
     address=bp+pos+0x38
     if address in seen:continue
     seen.add(address);zero=stock[pos+0x38:pos+0x50];values=struct.unpack('<6I',zero);one=struct.pack('<6I',*(min(v+2,15) for v in values));switch(4,address,zero,one)
  # Independent support flag in both reachable chapter4 variants.
  for label in ['support_story','support_native']:
   item=support[label];_,base,size=locate(le,2050) if label=='support_story' else (None,item['offset'],item['size']);blob=read(current,base,size);rs=records(blob);ix=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,*SUPPORT_FLAG]);on=rs[ix+1];disabled=on.copy();disabled[4]=2;record_switch(7,base,blob,ix+1,disabled,on)
  _,base,size=locate(le,2027);blob=read(current,base,size);rs=records(blob);ix=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,*MAINTENANCE_FLAG]);on=rs[ix+1];disabled=on.copy();disabled[4]=2;record_switch(8,base,blob,ix+1,disabled,on)
  for archive in ['SHARED.BIN','IM.BIN']:
   entry,master=rawmaster(current,archive)
   for unit in maintenance['masters'][archive]['units']:
    index=u16(master.b,master.tables['UTbl'][0]+12+unit['key']*2);at=master.tables['Unit'][0]+12+index*100;switch(8,entry['offset']+at,bytes.fromhex(unit['before_unit_hex']),bytes(master.b[at:at+100]))
  r_weapons=json.loads((ROOT/'huckebein_r_weapons_prepared.json').read_text(encoding='utf-8'))
  for ar,item in r_weapons['masters'].items():
   entry,master=rawmaster(current,ar);index=u16(master.b,master.tables['UTbl'][0]+12+1209*2);at=entry['offset']+master.tables['Unit'][0]+12+index*100;switch(10,at,bytes.fromhex(item['before_unit_hex']),bytes.fromhex(item['after_unit_hex']))
   for w in item['weapons']:
    wi=u16(master.b,master.tables['WTbl'][0]+12+w['private_key']*2);at=entry['offset']+master.tables['Weap'][0]+12+wi*36+8;switch(10,at,struct.pack('<H',w['before_power']),struct.pack('<H',w['after_power']))
  # Native SP costs are mandatory, including the additional cloned pilots.
  _,shared=rawmaster(original,'SHARED.BIN')
  cast={r['new_key']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast']}
  for ar in ['SHARED.BIN','IM.BIN']:
   ce,cm=rawmaster(current,ar);_,om=rawmaster(original,ar);clones={u16(cm.b,cm.tables['PTbl'][0]+12+k*2):r for k,r in cast.items()}
   for i,pos,row in cm.rows('Plot'):
    if i<om.tables['Plot'][2]:normal=om.b[om.tables['Plot'][0]+12+i*148:om.tables['Plot'][0]+12+(i+1)*148]
    elif i==u16(cm.b,cm.tables['PTbl'][0]+12+1930*2) or i not in clones:normal=row
    else:
     item=clones[i];key=1091 if item['pilot_name']=='이글렛' else item['pilot'];j=u16(shared.b,shared.tables['PTbl'][0]+12+key*2);normal=shared.b[shared.tables['Plot'][0]+12+j*148:shared.tables['Plot'][0]+12+(j+1)*148]
    for rel in [*range(0x72,0x78),0x7f]:
     val=normal[rel]
     if rel==0x7f and row[0x7e]==0:val=0
     common.append((ce['offset']+pos+rel,bytes([val])))
  for archive in ['SHARED.BIN','IM.BIN']:
   entry,master=rawmaster(current,archive)
   for name in POLICY:
    item=next(r for r in cast.values() if r['pilot_name']==name)
    idx=u16(master.b,master.tables['PTbl'][0]+12+item['new_key']*2);pos=master.tables['Plot'][0]+12+idx*148
    row=bytes(master.b[pos:pos+148]);balanced=apply_to_row(name,row)
    common.append((entry['offset']+pos+0x6c,balanced[0x6c:0x80]))
  for archive in ['SHARED.BIN','IM.BIN']:
   entry,master=rawmaster(current,archive)
   for at,old,replacement,key in edits_for_master(master.b,[r['key'] for ch in json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'))['chapters'] for r in ch['recruits']]):common.append((entry['offset']+at,replacement))
  proof.update(party_preservation=True,native_recovery_script_offset=NATIVE_RECOVERY,native_recovery_script_size=len(recovery),spirit_balanced_pilots=len(POLICY),native_supply_script_offset=allocation,native_supply_script_size=len(new),native_supply_messages=note['messages'],early_equipment_native_messages=early_note['messages'],story_directory_edits=len(features[0]),enemy_record_edits=len([x for x in features[4] if len(x[1])==24]))
  # Independent regional route, plus story dialogue/enemy-grade cross options.
  from regional_five_policy import stage_base
  rp=json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8'))
  for item in rp['bridge']:
   blob=read(current,item['offset'],item['size']);rs=records(blob);ix=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,58,0]);on=rs[ix+1];zero=on.copy();zero[4]=2;record_switch(11,item['offset'],blob,ix+1,zero,on)
   ix=item['route_row'];on=rs[ix];assert on[0]==0xa1 and on[2]==35;zero=on.copy();zero[2]=33;record_switch(11,item['offset'],blob,ix,zero,on)
  for item in rp['scenes']:
   bp=item['logo']['offset'];blob=read(current,bp,item['logo']['size']);rs=records(blob)
   for ix in item['story_gates']:
    on=rs[ix];zero=on.copy();zero[4]=2;record_switch(0,bp,blob,ix,zero,on)
   bp=item['untd']['offset'];blob=read(current,bp,item['untd']['size'])
   for ix in range(u32(blob,40)):
    pos=44+ix*336
    if u32(blob,pos+8)==2:switch(4,bp+pos+0x38,struct.pack('<6I',*([6]*6)),blob[pos+0x38:pos+0x50])
  e,m=rawmaster(current,'SHARED.BIN');sb=stage_base(m)
  _,om=rawmaster(original,'SHARED.BIN');ob=stage_base(om)
  for index in range(35,40):switch(11,e['offset']+sb+index*12,om.b[ob+index*12:ob+(index+1)*12],m.b[sb+index*12:sb+(index+1)*12])
  for index,zero in [(33,35),(34,36)]:switch(11,e['offset']+sb+index*12+6,bytes([zero]),m.b[sb+index*12+6:sb+index*12+7])
  # The sixth battle shares bit11 with the five regional missions.
  bp=json.loads((ROOT/'beowulf_stage_prepared.json').read_text(encoding='utf8'))
  chapter35=dp(la,2033)
  for lists in [features,off]:lists[0]=[(at,b) for at,b in lists[0] if at!=chapter35]
  native,story35=[next(x for x in bp['bridge'] if x['mode']==mode) for mode in ['native','story']]
  switch(0,chapter35,struct.pack('<II',native['offset']-la['directory'],native['size']),struct.pack('<II',story35['offset']-la['directory'],story35['size']))
  for item in bp['bridge']:
   blob=read(current,item['offset'],item['size']);rs=records(blob);ix=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,58,1]);on=rs[ix+1];zero=on.copy();zero[4]=2;record_switch(11,item['offset'],blob,ix+1,zero,on)
   ix=item['route_row'];on=rs[ix];assert on[2]==40;zero=on.copy();zero[2]=34;record_switch(11,item['offset'],blob,ix,zero,on)
  item=bp['logo'];blob=read(current,item['offset'],item['size']);rs=records(blob)
  for ix in bp['story_gates']:
   on=rs[ix];zero=on.copy();zero[4]=2;record_switch(0,item['offset'],blob,ix,zero,on)
  item=bp['untd'];blob=read(current,item['offset'],item['size'])
  for row in bp['spawn']:
   at=item['offset']+44+row['row']*336+0x38;switch(4,at,struct.pack('<6I',*([row['base_grade']]*6)),struct.pack('<6I',*([row['base_grade']+2]*6)))
  switch(11,e['offset']+sb+40*12,om.b[ob+40*12:ob+41*12],m.b[sb+40*12:sb+41*12])
  proof.update(beowulf_stage=True,additional_battles=6,beowulf_minions=30,beowulf_endless_reinforcements=True,beowulf_native_checks=json.loads((ROOT/'beowulf_stage_validation.json').read_text(encoding='utf8'))['checks'])
  ip=json.loads((ROOT/'intermission_six_prepared.json').read_text(encoding='utf8'))
  for scene in ip['scenes']:
   item=scene['logo'];blob=read(current,item['offset'],item['size']);rs=records(blob)
   for ix in scene['old_story_gates']+scene['new_story_gates']:
    on=rs[ix];assert on[0]==0x91;zero=on.copy();zero[4]=2;record_switch(0,item['offset'],blob,ix,zero,on)
  proof.update(intermission_scenes=12,intermission_new_lines=ip['new_lines'],tactical_expansions=6,ship_alerts_before_selection=True)
  gp=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'));cp=gp['effective_civil']
  for scene in cp['bridges']:
   item=scene['logo'];blob=read(current,item['offset'],item['size']);rs=records(blob)
   for ix in scene['old_story_gates']+scene['new_story_gates']:
    on=rs[ix];assert on[0]==0x91;zero=on.copy();zero[4]=2;record_switch(0,item['offset'],blob,ix,zero,on)
   if scene['key']==2040:
    ix=scene['route_row'];on=rs[ix];assert on[0]==0xa1 and on[2]==41;zero=on.copy();zero[2]=34;record_switch(11,item['offset'],blob,ix,zero,on)
  for scene in cp['scenes']:
   item=scene['logo'];blob=read(current,item['offset'],item['size']);rs=records(blob)
   for ix in scene['story_gates']:
    on=rs[ix];zero=on.copy();zero[4]=2;record_switch(0,item['offset'],blob,ix,zero,on)
   item=scene['untd']
   for row in scene['spawn']:
    at=item['offset']+44+row['row']*336+0x38;switch(4,at,struct.pack('<6I',*([row['base_grade']]*6)),struct.pack('<6I',*([row['base_grade']+2]*6)))
   index=scene['key']-2000;switch(11,e['offset']+sb+index*12,om.b[ob+index*12:ob+(index+1)*12],m.b[sb+index*12:sb+(index+1)*12])
  proof.update(civil_war=True,civil_war_battles=7,civil_war_political_scenes=5,civil_war_encounter_pairs=cp['automatic_encounter_pairs'],civil_war_dialogue_boxes=cp['new_dialogue_boxes'],additional_battles=13,final_display_chapter=49)
  proof.update(civil_reinforcements=True,civil_reinforcement_turns=[2,3,4],civil_reinforcements_per_wave=6,civil_reinforcements_per_stage=18,civil_reinforcements_dynamic_ship_anchor=True)
  proof.update(regional_five=True,regional_five_experimental=True,regional_story_gates=sum(len(x['story_gates']) for x in rp['scenes']),regional_enemy_records=160,regional_native_checks=json.loads((ROOT/'regional_five_validation.json').read_text(encoding='utf8'))['native_checks'],live_playthrough=False)
 # Deduplicate aliases and require independent options to touch disjoint bytes.
 for lists in [features,off]:
  for i,es in enumerate(lists):
   d={}
   for p,b in es:assert p not in d or d[p]==b;d[p]=b
   lists[i]=sorted(d.items())
 flat=sorted((p,p+len(b),i) for i,es in enumerate(features) for p,b in es)
 for a,b in zip(flat,flat[1:]):assert a[1]<=b[0],('option overlap',a,b)
 return common,off,features,proof

def merge(spans):
 out=[]
 for start,end in sorted(spans):
  if out and start<=out[-1][1]+4096:out[-1]=(out[-1][0],max(end,out[-1][1]))
  else:out.append((start,end))
 return out

def fingerprint(ranges,data):
 h=hashlib.sha256()
 for (p,original,base),b in zip(ranges,data):h.update(struct.pack('<QI',p,len(b)));h.update(hashlib.sha256(b).digest())
 return h.digest()

def profile_signer(ranges,base,features):
 # Imported art never varies with a checkbox. Hash those ranges once per
 # catalog, retaining the exact existing fingerprint format for compatibility.
 starts=[r[0] for r in ranges];dirty={bisect.bisect_right(starts,p)-1 for es in features for p,b in es}
 constant={i:hashlib.sha256(b).digest() for i,b in enumerate(base) if i not in dirty}
 def sign(data):
  h=hashlib.sha256()
  for i,((p,original,unused),b) in enumerate(zip(ranges,data)):
   h.update(struct.pack('<QI',p,len(b)));h.update(constant[i] if i in constant else hashlib.sha256(b).digest())
  return h.digest()
 return sign,dirty

def deflate(b):
 c=zlib.compressobj(9,zlib.DEFLATED,-15);return c.compress(b)+c.flush()

def load_pack(path):
 import io
 f=io.BytesIO(path.read_bytes())
 def n(fmt):return struct.unpack(fmt,f.read(struct.calcsize(fmt)))
 def blob():return f.read(n('<I')[0])
 assert f.read(8)==b'OGGOPT01';assert n('<I')[0]==1
 n('<Q');source_hash=f.read(32);count=n('<I')[0];assert count in [7,8,9,10,11,12]
 for _ in range(count):blob();blob()
 regions=[]
 for _ in range(n('<I')[0]):
  p,size=n('<QI');blob();base=zlib.decompress(blob(),-15);assert len(base)==size;regions.append((p,base))
 features=[]
 for _ in range(count):
  es=[]
  for _ in range(n('<I')[0]):p,size=n('<QI');es.append((p,f.read(size)))
  features.append(es)
 return regions,features,source_hash

def load_old_pack():return load_pack(OLD_PACK)[:2]

def build():
 PATCHER.mkdir(parents=True,exist_ok=True);common,off,features,proof=plan();old=load_old_pack();previous_pack=load_pack(PREVIOUS_PACK);older_pack=load_pack(OLDER_PACK);spirits_pack=load_pack(SPIRITS_PACK);party_pack=load_pack(PARTY_PACK);consistency_pack=load_pack(CONSISTENCY_PACK);previous_ten_pack=load_pack(PREVIOUS_TEN_PACK);previous_eleven_pack=load_pack(PREVIOUS_ELEVEN_PACK);previous_regional_pack=load_pack(PREVIOUS_REGIONAL_PACK);previous_bosses_pack=load_pack(PREVIOUS_BOSSES_PACK);previous_density_pack=load_pack(PREVIOUS_DENSITY_PACK);previous_beowulf_pack=load_pack(PREVIOUS_BEOWULF_PACK);previous_intermission_pack=load_pack(PREVIOUS_INTERMISSION_PACK);previous_civil_war_pack=load_pack(PREVIOUS_CIVIL_WAR_PACK);spans=[(p,p+len(b)) for p,b in old[0]]+[(p,p+len(b)) for p,b,a in BASE_CHANGES]+[(p,p+len(b)) for p,b in previous_pack[0]]+[(p,p+len(b)) for p,b in older_pack[0]]+[(p,p+len(b)) for p,b in spirits_pack[0]]+[(p,p+len(b)) for p,b in party_pack[0]]+[(p,p+len(b)) for p,b in consistency_pack[0]]+[(p,p+len(b)) for p,b in previous_ten_pack[0]]+[(p,p+len(b)) for p,b in previous_eleven_pack[0]]+[(p,p+len(b)) for p,b in previous_regional_pack[0]]+[(p,p+len(b)) for p,b in previous_bosses_pack[0]]+[(p,p+len(b)) for p,b in previous_density_pack[0]]+[(p,p+len(b)) for p,b in previous_beowulf_pack[0]]+[(p,p+len(b)) for p,b in previous_intermission_pack[0]]+[(p,p+len(b)) for p,b in previous_civil_war_pack[0]];sh=hashlib.sha256();ch=hashlib.sha256();size=TARGET.stat().st_size
 # Full-resource journals also include unchanged trailing padding. Cover it so
 # recognizing an older input can safely restore the exact earlier bytes.
 for journal in ['support_overhaul_journal.json','beowulf_stage_journal.json','intermission_six_journal.json','civil_war_journal.json','civil_reinforcements_journal.json','civil_guard_journal.json']:
  for e in json.loads((ROOT/journal).read_text(encoding='utf-8'))['edits']:
   at=e['offset'];n=len(unpack(e,'before'));spans.append((at//4096*4096,(at+n+4095)//4096*4096))
 print('Scanning original and canonical ISO without creating images...',flush=True)
 with source_image() as a,TARGET.open('rb') as b:
  pos=0
  while x:=a.read(8<<20):
   y=b.read(len(x));assert len(y)==len(x);sh.update(x);ch.update(y)
   if x!=y:
    aa=np.frombuffer(x,dtype=np.uint8);bb=np.frombuffer(y,dtype=np.uint8);flags=np.any((aa!=bb).reshape(-1,4096),axis=1)
    for i in np.flatnonzero(flags):spans.append((pos+int(i)*4096,pos+(int(i)+1)*4096))
   pos+=len(x)
 assert sh.hexdigest()==BASE_INFO['base_sha256']
 assert ch.hexdigest()==json.loads((ROOT/'current_target.json').read_text())['current_sha256']
 for p,b in common+[e for es in off+features for e in es]:spans.append((p//4096*4096,min(size,(p+len(b)+4095)//4096*4096)))
 spans=merge(spans);ranges=[];legacy=[]
 with source_image() as a,TARGET.open('rb') as b:
  for start,end in spans:ranges.append((start,read(a,start,end-start),bytearray(read(b,start,end-start))));legacy.append(bytes(ranges[-1][2]))
 starts=[r[0] for r in ranges]
 def setbytes(data,p,b):
  i=bisect.bisect_right(starts,p)-1;offset=p-starts[i];assert i>=0 and offset+len(b)<=len(data[i]);data[i][offset:offset+len(b)]=b
 base=[r[2] for r in ranges]
 for p,b in common+[e for es in off for e in es]:setbytes(base,p,b)
 immutable=[bytes(x) for x in base];profiles=[];sign,dirty=profile_signer(ranges,immutable,features)
 for mask in range(1<<len(OPTIONS)):
  data=[bytearray(x) if i in dirty else x for i,x in enumerate(immutable)]
  for bit,es in enumerate(features):
   if mask&(1<<bit):
    for p,b in es:setbytes(data,p,b)
  profiles.append(sign(data))
  if mask in [0,(1<<len(OPTIONS))-1]:assert profiles[-1]==fingerprint(ranges,data)
 assert len(set(profiles))==(1<<len(OPTIONS)),'Each checkbox must have a distinct reversible profile'
 legacy_inputs={fingerprint(ranges,legacy):4095}
 # Recognize the earlier canonical states before base/SP/price updates.
 previous=[bytearray(b) for b in legacy]
 for name in ['civil_guard_journal.json','civil_reinforcements_journal.json','civil_war_journal.json','intermission_six_journal.json','beowulf_stage_journal.json','regional_density_journal.json','regional_bosses_journal.json','regional_five_journal.json','followup_refinement_journal.json','huckebein_r_weapons_journal.json','huckebein_r_early_journal.json','early_equipment_journal.json','followup_story_journal.json','support_overhaul_journal.json','story_consistency_journal.json','party_25_journal.json','spirit_balance_25_journal.json','upstream_rebase_journal.json','sp_and_prices_revision_journal.json']:
  journal=json.loads((ROOT/name).read_text(encoding='utf-8'))
  for e in journal['edits']:setbytes(previous,e['offset'],unpack(e,'before'))
  legacy_inputs[fingerprint(ranges,previous)]=4095 if name in ['civil_guard_journal.json','civil_reinforcements_journal.json','civil_war_journal.json','intermission_six_journal.json','beowulf_stage_journal.json','regional_density_journal.json','regional_bosses_journal.json'] else 2047 if name in ['regional_five_journal.json','followup_refinement_journal.json'] else 1023 if name in ['huckebein_r_weapons_journal.json','huckebein_r_early_journal.json'] else 511 if name in ['early_equipment_journal.json','followup_story_journal.json'] else 127
 with SOURCE.open('rb') as old_source:old_original=[read(old_source,p,len(b)) for p,b,_ in ranges]
 legacy_inputs[fingerprint(ranges,old_original)]=0

 # Also recognize the canonical image after only the requested SP/cost changes.
 canonical_after=[bytearray(b) for b in legacy]
 for at,b in common:
  if len(b)==1:setbytes(canonical_after,at,b)
 for at,b in features[6]:setbytes(canonical_after,at,b)
 legacy_inputs[fingerprint(ranges,canonical_after)]=4095
 for regions,fs,base_hash in [load_pack(OLD_PACK),older_pack,spirits_pack,party_pack,consistency_pack,previous_pack,previous_ten_pack,previous_eleven_pack,previous_regional_pack,previous_bosses_pack,previous_density_pack,previous_beowulf_pack,previous_intermission_pack,previous_civil_war_pack]:
  source_data=old_original if base_hash!=sh.digest() else [r[1] for r in ranges]
  old_base=[bytearray(b) for b in source_data]
  for at,b in regions:setbytes(old_base,at,b)
  old_base=[bytes(b) for b in old_base];old_sign,old_dirty=profile_signer(ranges,old_base,fs)
  for mask in range(1<<len(fs)):
   data=[bytearray(b) if i in old_dirty else b for i,b in enumerate(old_base)]
   for bit,es in enumerate(fs):
    if mask&(1<<bit):
     for at,b in es:setbytes(data,at,b)
   digest=old_sign(data)
   if mask in [0,(1<<len(fs))-1]:assert digest==fingerprint(ranges,data)
   legacy_inputs[digest]=mask if len(fs)>=9 else mask&127
 pack=PATCHER/'OGG_options.bin'
 with pack.open('wb') as f:
  def w(fmt,*v):f.write(struct.pack(fmt,*v))
  def blob(b):w('<I',len(b));f.write(b)
  f.write(b'OGGOPT01');w('<IQ',1,size);f.write(sh.digest());w('<I',len(OPTIONS))
  for name,desc in OPTIONS:
   for s in [name,desc]:blob(s.encode('utf8'))
  w('<I',len(ranges))
  for (p,original,_),zero in zip(ranges,immutable):w('<QI',p,len(original));blob(deflate(original));blob(deflate(zero))
  for es in features:
   w('<I',len(es))
   for p,b in es:w('<QI',p,len(b));f.write(b)
  w('<I',len(profiles))
  for mask,digest in enumerate(profiles):w('<I',mask);f.write(digest)
  f.write(fingerprint(ranges,[r[1] for r in ranges]));w('<I',len(legacy_inputs))
  for digest,mask in legacy_inputs.items():f.write(digest);w('<I',mask)
 digest=hashlib.sha256(pack.read_bytes()).hexdigest()
 meta=dict(version=VERSION,original_iso_sha256=sh.hexdigest(),canonical_iso_sha256=ch.hexdigest(),iso_size=size,defaults=0,options=[dict(bit=i,name=n,description=d) for i,(n,d) in enumerate(OPTIONS)],profile_count=len(profiles),managed_ranges=len(ranges),managed_bytes=sum(len(r[1]) for r in ranges),pack_sha256=digest,pack_size=pack.stat().st_size,proof=proof,shutdown_requested=False,legacy_profiles=len(legacy_inputs),sp_cost_policy='native with 13 allied-clone role corrections',weapon_cost_steps=[1600,1600,1920,3200,3200],upstream_base={k:v for k,v in BASE_INFO.items() if k not in ['changes']})
 (HERE/'build_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in meta.items() if k not in ['options','proof']},indent=2),flush=True)
 return meta

if __name__=='__main__':build()
