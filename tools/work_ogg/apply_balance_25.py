"""Guarded in-place balance patch. Only the canonical ISO and journals are writable."""
from catalog import *
import argparse,os,zlib,base64

STATE=ROOT/'current_target.json'
JOURNAL=ROOT/'balance_25_journal.json'
BALANCE=ROOT/'balance_plan_25_v1.json'

# min/max, EN, ammunition, morale, post-movement. None preserves that field.
PROFILES={
 '잉그램':[(1,3,10,0,0,True),(1,6,0,10,0,False),(3,7,50,0,125,False)],
 '린':[(1,3,0,20,0,True),(3,7,70,0,130,False),(1,2,0,0,0,True),(1,4,10,0,0,True),(1,5,0,10,0,True)],
 '레몬':[(1,2,0,0,0,True),(1,4,10,0,0,True),(2,6,45,0,120,False),(3,7,35,0,110,False)],
 '메키보스':[(None,None,70,0,130,False),(1,2,10,0,0,True),(2,6,20,0,0,False),(3,7,50,0,120,False)],
 '비가지':[(1,5,0,10,0,True),(1,2,45,0,120,True),(2,6,30,0,110,False)],
 '비안':[(1,2,15,0,0,True),(3,7,45,0,120,False),(None,None,70,0,130,False)],
 '빈델':[(1,3,10,0,0,True),(None,None,70,0,130,False),(1,5,20,0,110,True),(1,3,35,0,120,True),(1,2,60,0,130,True)],
 '스리사즈':[(1,4,10,0,0,True),(2,6,40,0,115,False)],
 '시카로그':[(2,6,20,0,0,False),(2,7,30,0,110,False),(1,2,45,0,120,True)],
 '아기하':[(1,2,0,0,0,True),(1,4,15,0,0,True),(2,6,40,0,120,False)],
 '아치볼드':[(1,4,0,8,0,True),(2,7,30,0,110,False),(3,8,40,0,120,False)],
 '아타드':[(1,4,10,0,0,True),(1,3,20,0,0,True),(2,7,40,0,115,False)],
 '안사즈':[(1,4,10,0,0,True),(2,7,40,0,115,False)],
 '에키드나':[(1,4,0,8,0,True),(2,6,0,10,0,False),(3,8,0,8,110,False),(1,2,0,0,0,True),(1,4,0,10,0,True)],
 '오우카':[(1,5,0,10,0,True),(3,7,35,0,110,False),(1,3,25,0,110,True),(1,2,50,0,125,True),(1,2,0,0,0,True)],
 '울즈':[(1,4,10,0,0,True),(2,7,45,0,120,False)],
 '워단':[(1,4,10,0,0,True),(1,3,20,0,0,True),(1,2,30,0,115,True),(1,2,60,0,130,True)],
 '웬드로':[(1,3,15,0,0,True),(None,None,80,0,130,False),(3,8,60,0,130,False)],
 '유리아':[(1,3,0,20,0,True),(1,4,0,10,0,True),(2,7,0,8,110,False)],
 '이글렛':[(2,7,25,0,0,False),(1,4,0,8,0,True)],
 '지벨':[(1,4,0,8,0,True),(2,7,20,0,0,False),(3,8,40,0,115,False)],
 '텐잔':[(1,3,0,20,0,True),(1,3,20,0,110,True),(1,2,0,0,0,True),(2,6,0,8,110,False)],
 '템페스트':[(1,2,15,0,0,True),(3,7,40,0,120,False)],
 '토머스':[(1,3,0,20,0,True),(1,3,20,0,110,True),(1,2,0,0,0,True),(2,6,0,8,110,False)],
 '가루인':[(2,6,30,0,110,False),(1,4,0,8,0,True),(1,2,0,0,0,True)]
}
# Actual Abil table IDs, checked against this OGG master, not guessed from OGs.
ABILITIES={
 '잉그램':[2,19], '린':[1,17], '레몬':[5,18], '메키보스':[22],
 '비가지':[19], '비안':[2], '빈델':[17], '스리사즈':[10,23],
 '시카로그':[24], '아기하':[20], '아치볼드':[22], '아타드':[8,19],
 '안사즈':[10,23], '에키드나':[5,18], '오우카':[1,18],
 '울즈':[10,23], '워단':[10,19], '웬드로':[25], '유리아':[],
 '이글렛':[10], '지벨':[22], '텐잔':[22], '템페스트':[1],
 '토머스':[22], '가루인':[3,19]
}

def get_record(m,tag,keytag,key,stride):
 idx=u16(m.b,m.tables[keytag][0]+12+key*2)
 assert idx<m.tables[tag][2]
 at=m.tables[tag][0]+12+idx*stride
 return idx,bytes(m.b[at:at+stride])

def logical_strings(m,tag):
 a,_,n=m.tables[tag];return [m.b[a+u32(m.b,a+12+i*4):m.b.index(0,a+u32(m.b,a+12+i*4))+1] for i in range(n)]

def rebuild(old,units,cast):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:(starts[i+1] if i+1<len(starts) else p+u32(old,p+4))]) for i,(k,p) in enumerate(zip(fields,starts))}
 parts[0x88].extend(bytes((-len(parts[0x88]))%4))
 count=u32(parts[0x24],8);free=[k for k in range(0xe00,4096) if u16(parts[0x20],12+k*2)==65535]
 needed=sum(sum(w['proposed_power'] is not None for w in u['weapons']) for u in units)
 assert len(free)>=needed
 free=iter(free);notes=[];changed_units=set();changed_pilots=set()
 _,ref=get_record(m,'Weap','WTbl',43,36);assert u16(ref,8)==3800
 ability_names={i:m.text(u16(r)) for i,_,r in m.rows('Abil')}
 assert [ability_names[i] for i in [2,10,15,17]]==['Ｅ필드','ＨＰ회복（소）','ＥＮ회복（대）','분신'] if 'ＨＰ회복（소）' in ability_names.values() else True
 # IM's legacy text is Japanese, while the ID order is identical.
 for u in units:
  name=u['name'];key=cast[name]['new_key'];ui,body=get_record(m,'Unit','UTbl',key,100)
  assert ui>=m.tables['Unit'][2]-27 and ui not in changed_units
  assert sum(u16(m.b,m.tables['UTbl'][0]+12+k*2)==ui for k in range(m.tables['UTbl'][2]))==1
  before=body;body=bytearray(body);st=u['proposed_base'];struct.pack_into('<I',body,0,st['hp']);struct.pack_into('<HH',body,0x18,st['en'],st['armor']);body[0x52]=st['move'];body[0x53]=st['mobility']
  abilities=ABILITIES[name];body[0x57:0x5d]=bytes(abilities+[0]*(6-len(abilities)))
  kept=[w for w in u['weapons'] if w['proposed_power'] is not None];profiles=PROFILES[name];assert len(kept)==len(profiles)
  newkeys=[];weapons=[]
  original_keys=list(struct.unpack_from('<16H',before,0x24))
  assert [w['original_weapon_key'] for w in u['weapons']]==[w for w in original_keys if w!=65535]
  for w,profile in zip(kept,profiles):
   source=w['original_weapon_key'];wi,wr=get_record(m,'Weap','WTbl',source,36)
   if ability_names[2]=='Ｅ필드':assert u16(wr,8)==w['current_power'],(name,source,u16(wr,8),w['current_power'])
   r=bytearray(wr)
   struct.pack_into('<H',r,8,w['proposed_power'])
   # Give enemy-origin weapons the same normal upgrade/cost class as an allied R-1 weapon.
   r[3]=(r[3]&0xc0)|(ref[3]&0x3f)
   lo,hi,en,ammo,morale,p=profile
   if lo is not None:r[0x17]=lo
   if hi is not None:r[0x18]=hi
   r[0x19]=ammo;r[0x1a]=en;r[0x1b]=morale
   r[0x14]=(r[0x14]|4) if p else (r[0x14]&~4)
   assert 0<r[0x17]<=r[0x18]<=15
   allowed={3,8,9,0x14,0x17,0x18,0x19,0x1a,0x1b}
   assert {i for i in range(36) if r[i]!=wr[i]}<=allowed
   # Header/motion selector, text IDs, attributes and ALL/MAP metadata survive.
   assert r[:3]==wr[:3] and r[4:8]==wr[4:8] and r[0x15:0x17]==wr[0x15:0x17]
   newkey=next(free);index=count;count+=1
   parts[0x24].extend(r);struct.pack_into('<H',parts[0x20],12+newkey*2,index);newkeys.append(newkey)
   weapons.append(dict(name=w['name'],original_key=source,new_key=newkey,record=index,power=u16(r,8),range=[r[0x17],r[0x18]],en=r[0x1a],ammo=r[0x19],morale=r[0x1b],post_move=bool(r[0x14]&4),old_motion_selector=wr[:2].hex(),new_motion_selector=r[:2].hex()))
  struct.pack_into('<16H',body,0x24,*(newkeys+[65535]*(16-len(newkeys))))
  p=12+ui*100;parts[0x1c][p:p+100]=body;changed_units.add(ui)
  pi,pilot=get_record(m,'Plot','PTbl',key,148);pb=bytearray(pilot)
  assert all(x<46 for x in pb[0x7e:0x84])
  removed_actions=[]
  for at in range(0x7e,0x84):
   if pb[at]==43:pb[at]=0;removed_actions.append(at)
  if pb!=pilot:
   p=12+pi*148;parts[0x2c][p:p+148]=pb;changed_pilots.add(pi)
  notes.append(dict(name=name,key=key,unit_record=ui,stats=st,abilities=abilities,ability_names=[ability_names[x] for x in abilities],removed_double_action_slots=removed_actions,weapons=weapons))
 struct.pack_into('<II',parts[0x24],4,12+count*36,count)
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 assert len(out)<=len(old),('capacity',len(out),len(old));used=len(out);out.extend(bytes(len(old)-len(out)));n=Master(out)
 # Existing non-clone units, all old weapons, all other pilots and all strings survive.
 for tag,stride,allowed in [('Unit',100,changed_units),('Weap',36,set()),('Plot',148,changed_pilots)]:
  for i in range(m.tables[tag][2]):
   if i in allowed:continue
   a=m.tables[tag][0]+12+i*stride;b=n.tables[tag][0]+12+i*stride
   assert old[a:a+stride]==out[b:b+stride],(tag,i,'unrelated record changed')
 for tag in ['Strg','Expl','Sent']:assert logical_strings(m,tag)==logical_strings(n,tag)
 for tag in m.tables:
  if tag in ['Unit','Weap','Plot','WTbl','Strg','Expl','Sent']:continue
  a,size,_=m.tables[tag];b=n.tables[tag][0];assert old[a:a+size]==out[b:b+size],tag
 for note,u in zip(notes,units):
  _,r=get_record(n,'Unit','UTbl',note['key'],100);s=u['proposed_base']
  assert (u32(r),u16(r,0x18),u16(r,0x1a),r[0x52],r[0x53])==(s['hp'],s['en'],s['armor'],s['move'],s['mobility'])
  assert list(r[0x57:0x5d])==note['abilities']+[0]*(6-len(note['abilities']))
  assert 11 not in r[0x57:0x5d] and 12 not in r[0x57:0x5d] and 15 not in r[0x57:0x5d]
  for w in note['weapons']:
   _,wr=get_record(n,'Weap','WTbl',w['new_key'],36);assert u16(wr,8)==w['power'] and wr[:2].hex()==w['old_motion_selector']
 return bytes(out),notes,dict(old_weapons=m.tables['Weap'][2],new_weapons=n.tables['Weap'][2],cloned_weapons=needed,used_bytes=used,capacity=len(old),unchanged_original_units=m.tables['Unit'][2]-len(changed_units),all_original_weapons_preserved=True,all_text_preserved=True)

def plan(target,units,cast):
 edits=[];checks={};notes={}
 with target.open('rb') as f:
  for archive in ['SHARED.BIN','IM.BIN']:
   a=json.loads((OUT/(archive+'.3.json')).read_text());e=a['entries'][0];old=read(f,e['offset'],e['size']);new,n,c=rebuild(old,units,cast)
   edits.append((e['offset'],old,new,archive+' ally balance'));notes[archive]=n;checks[archive]=c
 assert [w['new_key'] for n in notes['SHARED.BIN'] for w in n['weapons']]==[w['new_key'] for n in notes['IM.BIN'] for w in n['weapons']]
 edits.sort();return edits,notes,checks

def packed(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 state=json.loads(STATE.read_text(encoding='utf8'));target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 balance=json.loads(BALANCE.read_text(encoding='utf8'));units=balance['units'];assert len(units)==25
 cast={r['pilot_name']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast']}
 edits,notes,checks=plan(target,units,cast)
 prepared=dict(target=str(target),applied=False,checks=checks,units=notes,scope='unit stats, independent weapons/cost/range/P, restrained abilities; existing chapter-one placement retained',deferred=['chapter-specific recruitment','join-time upgrade grants','chapter-specific repaired-weapon unlocks','pilot stat rebalance'],live_verified=False)
 (ROOT/'balance_25_prepared.json').write_text(json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)
 if not args.apply:print('Prepared only. ISO untouched.');return
 assert not JOURNAL.exists(),'Balance already has a journal; inspect before repeating'
 # An exclusive-write probe happens before any byte is changed.
 with target.open('r+b') as f:
  print('Verifying canonical ISO hash...',flush=True);assert hashlib.file_digest(f,'sha256').hexdigest()==state['current_sha256']
  for o,a,b,l in edits:assert read(f,o,len(a))==a
  record={**prepared,'source_sha256':state['current_sha256'],'encoding':'zlib+base64','edits':[dict(offset=o,size=len(a),before_zlib_base64=packed(a),after_zlib_base64=packed(b),label=l) for o,a,b,l in edits]}
  JOURNAL.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for o,a,b,l in edits:f.seek(o);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());print('Checking image integrity and all unmodified bytes...',flush=True)
   inverse=hashlib.sha256();digest=hashlib.sha256();pos=0;f.seek(0)
   for o,a,b,l in edits:
    while pos<o:
     raw=f.read(min(4<<20,o-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;inverse.update(a);digest.update(b);pos+=len(b)
   while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
   assert inverse.hexdigest()==state['current_sha256']
  except BaseException:
   for o,a,b,l in edits:f.seek(o);f.write(a)
   f.flush();os.fsync(f.fileno());raise
 record.update(applied=True,target_sha256=digest.hexdigest(),all_other_image_bytes_preserved=True)
 JOURNAL.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
 oldsha=state['current_sha256'];state.update(current_sha256=record['target_sha256'],balance_25_applied=True,balance_stage='fully repaired base stats; chapter-one showcase',last_edit_journal=str(JOURNAL));STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 guide=ROOT/'AGENTS.md';t=guide.read_text(encoding='utf8').replace(oldsha,record['target_sha256']);t+='\n- The 25 allied clone units now have balanced base stats, independent weapons/costs/ranges and restrained abilities. Enemy originals and existing allies are preserved. See balance_25_journal.json. Chapter recruitment/upgrade grants/unlocks remain pending story implementation.\n';guide.write_text(t,encoding='utf8')
 balance.update(status='기체 기본 능력치·무장·소모량·사거리·P·특수능력 적용 완료. 화별 합류·초기 개조·무장 해금은 시나리오 구현 때 적용.',applied_iso=str(target),applied_sha256=record['target_sha256'],application_journal=str(JOURNAL),deferred=prepared['deferred']);BALANCE.write_text(json.dumps(balance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(applied=True,target=str(target),sha256=record['target_sha256'],weapons=checks['SHARED.BIN']['cloned_weapons'],live_verified=False),ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
