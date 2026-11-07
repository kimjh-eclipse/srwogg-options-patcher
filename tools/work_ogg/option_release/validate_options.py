"""Validate packaged scripts/hooks using the actual game's R5900 routines."""
from pathlib import Path
import sys,struct,zlib,io,json,bisect,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inspect_iso import SOURCE,OUT,inventory,u32
from build_options import rawmaster,load_old_pack,source_image,load_pack,OLD_PACK,PREVIOUS_PACK,OLDER_PACK,SPIRITS_PACK,PARTY_PACK,CONSISTENCY_PACK,PREVIOUS_TEN_PACK,PREVIOUS_ELEVEN_PACK,PREVIOUS_REGIONAL_PACK,PREVIOUS_BOSSES_PACK,PREVIOUS_DENSITY_PACK
from audit_story_layout import loadarc
from story_scripts_25 import records,text_at,encode
from campaign_bonus_scripts import EARLY
from story_vm import VM
from spirit_policy_25 import POLICY,apply_to_row
from validate_campaign_tuning import hostile_checks,reward_checks

HERE=Path(__file__).resolve().parent

class Profiles:
 def __init__(self):
  f=io.BytesIO((HERE.parent/'release_v20261107.5/patcher/OGG_options.bin').read_bytes())
  def n(fmt):return struct.unpack(fmt,f.read(struct.calcsize(fmt)))
  def blob():return f.read(n('<I')[0])
  assert f.read(8)==b'OGGOPT01';assert n('<I')[0]==1
  self.size=n('<Q')[0];f.read(32);count=n('<I')[0]
  for _ in range(count):blob();blob()
  self.regions=[]
  for _ in range(n('<I')[0]):
   p,size=n('<QI');original=zlib.decompress(blob(),-15);base=zlib.decompress(blob(),-15)
   assert len(original)==len(base)==size;self.regions.append((p,base))
  self.features=[]
  for _ in range(count):
   es=[]
   for _ in range(n('<I')[0]):p,size=n('<QI');es.append((p,f.read(size)))
   self.features.append(es)
  self.starts=[p for p,b in self.regions]
  profiles=n('<I')[0];self.known={}
  for _ in range(profiles):
   mask=n('<I')[0];self.known[f.read(32)]=mask
  self.known[f.read(32)]=-1
  for _ in range(n('<I')[0]):
   digest=f.read(32);mask=n('<I')[0];self.known[digest]=mask
 def data(self,mask):
  data=[bytearray(b) for p,b in self.regions]
  for bit,es in enumerate(self.features):
   if mask&(1<<bit):
    for p,b in es:
     i=bisect.bisect_right(self.starts,p)-1;rel=p-self.starts[i];data[i][rel:rel+len(b)]=b
  return data

class Image:
 def __init__(self,p,mask):self.p=p;self.data=p.data(mask);self.f=SOURCE.open('rb');self.pos=0
 def seek(self,at,whence=0):
  self.pos=at if whence==0 else self.pos+at if whence==1 else self.p.size+at;return self.pos
 def tell(self):return self.pos
 def read(self,n):
  self.f.seek(self.pos);out=bytearray(self.f.read(n));end=self.pos+len(out)
  for (at,base),data in zip(self.p.regions,self.data):
   lo=max(at,self.pos);hi=min(at+len(data),end)
   if lo<hi:out[lo-self.pos:hi-self.pos]=data[lo-at:hi-at]
  self.pos=end;return bytes(out)

def supply_checks(p):
 result=[];meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf-8'))
 for mask in [0,1,4,5]:
  image=Image(p,mask);_,master=rawmaster(image,'SHARED.BIN');a,es=loadarc(image,14)
  _,at,size=next(e for e in es if 2003 in e[0]);image.seek(at);logo=image.read(size);rs=records(logo)
  start=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,63,7])
  end=next(i for i in range(start,len(rs)) if rs[i][0]==0xba and rs[i][2:5]==[0x100c1,63,7])+1
  vm=VM();vm.load_master(master.b);c=vm.cpu
  def qty(op,k):
   if op==0x60:return c.read(vm.diff+0x10c8+k,1)
   return sum(c.read(vm.save+0x21efc+i*4,2)==k for i in range(0x3e00//4))
  def execute():
   i=start;count=0
   while i<end:
    row=rs[i];c.write(vm.ctx+0x48d0,i,4)
    if row[0]!=0x30:
     assert row[0] in [0x93,0x91,0xba,0x60,0x64];assert vm.op(row)==10
     count+=row[0] in [0x60,0x64]
    i=c.read(vm.ctx+0x48d0,4)+1
   return count
  before=[qty(op,k) for op,k,name in EARLY];enabled=bool(mask&4)
  assert execute()==(8 if enabled else 0)
  assert [qty(op,k)-v for (op,k,name),v in zip(EARLY,before)]==[int(enabled)]*8
  assert execute()==0
  if not mask&1:
   assert at==meta['proof']['native_supply_script_offset']
   base=0x1800000;c.mem[base:base+len(logo)]=logo;c.run(0x5363c0,[vm.ctx,base])
   for msg in meta['proof']['native_supply_messages']:
    raw=bytes.fromhex(msg['encoded']);c.run(0x53ad00,[vm.ctx,0,msg['string_id']]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)])==raw
    c.run(0x53a1f0,[vm.ctx,msg['label'],0,0,0],stop=0x53a244);idx=c.r[4]&0xffffffff
    assert u32(logo,u32(logo,36)+idx*96+8)==msg['string_id']
  image.f.close();result.append(dict(mask=mask,story=bool(mask&1),supplies=enabled,first_grants=8 if enabled else 0,repeat_grants=0))
 return result

def ram(p,mask):
 image=Image(p,mask);entries=inventory(image);elf=next(e for e in entries if e['name'].startswith('SLPS_'));mp=next(e for e in entries if e['name']=='MPOL.BIN;1')
 out=bytearray((OUT/'terrain_fresh_ram.bin').read_bytes())
 image.seek(mp['offset']);overlay=image.read(mp['size']);out[0x422000:0x422000+len(overlay)]=overlay
 for (at,base),data in zip(p.regions,image.data):
  lo=max(at,elf['offset']+0x180);hi=min(at+len(data),elf['offset']+elf['size'])
  if lo<hi:
   pc=0x100000+lo-elf['offset']-0x180;out[pc:pc+hi-lo]=data[lo-at:hi-at]
 image.f.close();return bytes(out)

def legacy_set_checks(p,path):
 regions,features,source_hash=load_pack(path);count=0
 # Imported art is identical across an older release's profiles. Read and hash
 # those constant ranges once, rather than rereading the ISO for every mask.
 with (SOURCE.open('rb') if len(features)==8 else source_image()) as old_source:
  base=[]
  for at,b in p.regions:old_source.seek(at);base.append(bytearray(old_source.read(len(b))))
 for at,b in regions:
  i=bisect.bisect_right(p.starts,at)-1;rel=at-p.starts[i];base[i][rel:rel+len(b)]=b
 dirty={bisect.bisect_right(p.starts,at)-1 for es in features for at,b in es};base=[bytes(b) for b in base];constant={i:hashlib.sha256(b).digest() for i,b in enumerate(base) if i not in dirty}
 for mask in range(1<<len(features)):
  data=[bytearray(b) if i in dirty else b for i,b in enumerate(base)]
  for bit,es in enumerate(features):
   if mask&(1<<bit):
    for at,b in es:
     i=bisect.bisect_right(p.starts,at)-1;rel=at-p.starts[i];data[i][rel:rel+len(b)]=b
  h=hashlib.sha256()
  for i,((at,_),b) in enumerate(zip(p.regions,data)):h.update(struct.pack('<QI',at,len(b)));h.update(constant[i] if i in constant else hashlib.sha256(b).digest())
  assert p.known[h.digest()]==(mask if len(features)>=9 else mask&127);count+=1
 return count

def _legacy_checks_through_bosses(p):
 return {'previous_8_option_profiles_recognized':legacy_set_checks(p,OLD_PACK),'v20261106_1_profiles_recognized':legacy_set_checks(p,OLDER_PACK),'v20261106_2_profiles_recognized':legacy_set_checks(p,SPIRITS_PACK),'v20261106_3_profiles_recognized':legacy_set_checks(p,PARTY_PACK),'v20261106_4_profiles_recognized':legacy_set_checks(p,CONSISTENCY_PACK),'v20261106_5_profiles_recognized':legacy_set_checks(p,PREVIOUS_PACK),'v20261107_profiles_recognized':legacy_set_checks(p,PREVIOUS_TEN_PACK),'v20261107_1_profiles_recognized':legacy_set_checks(p,PREVIOUS_ELEVEN_PACK),'v20261107_2_profiles_recognized':legacy_set_checks(p,PREVIOUS_REGIONAL_PACK),'v20261107_3_profiles_recognized':legacy_set_checks(p,PREVIOUS_BOSSES_PACK),'removed_SP_bit_not_exposed':True}

def legacy_checks(p):
 result=_legacy_checks_through_bosses(p)
 result['v20261107_4_profiles_recognized']=legacy_set_checks(p,PREVIOUS_DENSITY_PACK)
 return result

def price_and_sp_checks(p):
 from catalog import u16
 from r5900_scalar_check import CPU
 with source_image() as source:
  _,shared=rawmaster(source,'SHARED.BIN'); originals={name:rawmaster(source,name)[1] for name in ['SHARED.BIN','IM.BIN']}
 cast={r['new_key']:r for r in json.loads((HERE.parent/'manifest_selected_27.json').read_text(encoding='utf-8'))['cast']}
 cases=0
 for mask in [0,127]:
  image=Image(p,mask)
  for name in ['SHARED.BIN','IM.BIN']:
   _,m=rawmaster(image,name);old=originals[name];vm=VM();vm.load_master(m.b);keys={}
   for key in range(m.tables['PTbl'][2]):
    index=u16(m.b,m.tables['PTbl'][0]+12+key*2)
    if index!=65535:keys.setdefault(index,key)
   for index,at,row in m.rows('Plot'):
    if index<old.tables['Plot'][2]:expected=old.b[old.tables['Plot'][0]+12+index*148:old.tables['Plot'][0]+12+(index+1)*148]
    elif keys.get(index)==1930:
     oi=u16(old.b,old.tables['PTbl'][0]+12+1094*2);expected=old.b[old.tables['Plot'][0]+12+oi*148:old.tables['Plot'][0]+12+(oi+1)*148]
    else:
     item=cast[keys[index]];key=1091 if item['pilot_name']=='이글렛' else item['pilot'];oi=u16(shared.b,shared.tables['PTbl'][0]+12+key*2);expected=shared.b[shared.tables['Plot'][0]+12+oi*148:shared.tables['Plot'][0]+12+(oi+1)*148]
    if index>=old.tables['Plot'][2] and keys.get(index)!=1930:expected=apply_to_row(item['pilot_name'],expected)
    for slot in range(6):
     assert row[0x72+slot]==expected[0x72+slot]
     if index in keys:assert vm.cpu.run(0x272730,[vm.master,keys[index],slot])==expected[0x72+slot];cases+=1
    assert row[0x7f]==(expected[0x7f] if row[0x7e] else 0)
  image.f.close()
 # Execute the game's invested-weapon-cost loop for every grade and level.
 price_cases=0
 for mask in [0,64]:
  c=CPU(ram(p,mask));steps=[1600,1600,1920,3200,3200] if mask else [2000,3000,5000,6500,7500]
  for tier,step in enumerate(steps):
   for level in range(1,16):
    c.r[2]=tier;c.r[3]=level;c.r[16]=0;c.run(0x26c7e8,stop=0x26c828)
    assert c.r[16]==step*level*(level+1)//2,(mask,tier,level,c.r[16]);price_cases+=1
  a=Image(p,mask);_,master=rawmaster(a,'SHARED.BIN')
  if not mask:baseline=bytes(master.b)
  else:assert bytes(master.b)==baseline,'Price option changed master/growth data'
  a.f.close()
 return {'native_SP_accessor_checks':cases,'native_cost_sum_checks':price_cases,'ten_stage_totals':[88000,88000,105600,176000,176000],'role_based_clone_SP_in_all_profiles':True,'price_option_preserves_weapon_growth':True}

def party_profile_checks(p):
 from inspect_iso import lice,read
 from party_policy_25 import edits_for_master,STORY_RECOVERY,NATIVE_RECOVERY
 keys=[r['key'] for ch in json.loads((HERE.parent/'story_25_prepared.json').read_text(encoding='utf-8'))['chapters'] for r in ch['recruits']]
 cases=0
 for mask in range(2048):
  image=Image(p,mask)
  try:
   entry=next(e for e in inventory(image) if e['name']=='MAP.BIN;1');outer=lice(image,entry['offset'],entry['size']);parent=outer['entries'][14];archive=lice(image,parent['offset'],parent['size'])
   recovery=next(e for e in archive['entries'] if 2026 in e['keys'])
   assert recovery['offset']==(STORY_RECOVERY if mask&1 else NATIVE_RECOVERY)
   rows=records(read(image,recovery['offset'],recovery['size']))
   assert sum(r[0]==0x4a and r[2:5]==[0x100bd,0x701,1] for r in rows)==1
   for name in ['SHARED.BIN','IM.BIN']:
    _,master=rawmaster(image,name);assert not edits_for_master(master.b,keys)
   cases+=1
  finally:image.f.close()
 return {'profiles':cases,'all_MAP14_pointers_within_declared_span':True,'private_family_identity_in_both_archives':True,'chapter28_existing_clone_recovery_story_on_and_off':True}

def consistency_profile_checks(p):
 from story_consistency_policy import FINAL_RESPONSE_FLAG
 from inspect_iso import read
 plan=json.loads((HERE.parent/'story_consistency_prepared.json').read_text(encoding='utf-8'))
 cases=0
 with source_image() as source:
  archive,entries=loadarc(source,14);stock={}
  for key,sid in [(2033,366),(2034,169)]:
   _,at,n=next(e for e in entries if key in e[0]);stock[key]=text_at(read(source,at,n),sid)
 for mask in range(2048):
  image=Image(p,mask)
  try:
   _,entries=loadarc(image,14)
   for chapter in plan['chapters']:
    _,at,n=next(e for e in entries if chapter['key'] in e[0]);blob=read(image,at,n)
    if mask&1:
     for change in chapter['replacements']:assert text_at(blob,change['string_id'])==encode(change['text'])
    elif chapter['key'] in stock:
     sid=366 if chapter['key']==2033 else 169;assert text_at(blob,sid)==stock[chapter['key']]
   _,at,n=next(e for e in entries if 2034 in e[0]);blob=read(image,at,n)
   assert sum(r[0]==0x93 and r[2:5]==[0x100c1,*FINAL_RESPONSE_FLAG] for r in records(blob))==int(bool(mask&1))
   cases+=1
  finally:image.f.close()
 return {'profiles':cases,'revised_dialogue_selected_only_with_story_option':True,'native_dialogue_restored_when_story_off':True,'new_final_response_selected_only_with_story_option':True}

def support_overhaul_profiles(p):
 from support_overhaul_policy import SUPPORT_FLAG,MAINTENANCE_FLAG
 from story_consistency_logo import guarded_block
 from catalog import u16
 from validate_support_overhaul import block,qty
 info=json.loads((HERE.parent/'support_overhaul_prepared.json').read_text(encoding='utf-8'));cases=0
 for mask in range(2048):
  image=Image(p,mask)
  try:
   _,entries=loadarc(image,14);_,at,n=next(e for e in entries if 2050 in e[0]);blob=image_read(image,at,n);start,end=guarded_block(blob,SUPPORT_FLAG)
   assert records(blob)[start+1][4]==(0 if mask&128 else 2)
   _,at,n=next(e for e in entries if 2027 in e[0]);blob=image_read(image,at,n)
   if mask&1:
    start,end=guarded_block(blob,MAINTENANCE_FLAG);assert records(blob)[start+1][4]==(0 if mask&256 else 2)
   else:assert not any(r[0]==0x93 and r[2:5]==[0x100c1,*MAINTENANCE_FLAG] for r in records(blob))
   for ar in ['SHARED.BIN','IM.BIN']:
    _,master=rawmaster(image,ar)
    for u in info['masters'][ar]['units']:
     idx=u16(master.b,master.tables['UTbl'][0]+12+u['key']*2);at=master.tables['Unit'][0]+12+idx*100;expected=u['after_unit_hex'] if mask&256 else u['before_unit_hex'];assert master.b[at:at+100]==bytes.fromhex(expected)
   cases+=1
  finally:image.f.close()
 native=[]
 for mask in [0,1,128,129,256,257,384,385]:
  image=Image(p,mask);_,master=rawmaster(image,'SHARED.BIN');_,es=loadarc(image,14);_,at,n=next(e for e in es if 2050 in e[0]);blob=image_read(image,at,n);vm=VM(ram(p,mask));vm.load_master(master.b)
  got=block(vm,blob,SUPPORT_FLAG,True)[0];assert got==(2 if mask&128 else 0);assert [qty(vm,k) for k in [3557,3558]]==[int(bool(mask&128))]*2;assert block(vm,blob,SUPPORT_FLAG,True)[0]==0;native.append({'mask':mask,'grants':got,'repeat_grants':0});image.f.close()
 return {'profiles':cases,'support_independent_of_story_and_maintenance':True,'maintenance_body_and_dialogue_follow_checkbox':True,'native_support_profiles':native,'unchanged_body_when_maintenance_off':True}

def image_read(image,at,n):image.seek(at);return image.read(n)

def common_weapon_cross_checks(p):
 from build_options import TARGET,unpack
 from catalog import u16
 entries=[e for e in json.loads((HERE.parent/'campaign_tuning_journal.json').read_text(encoding='utf-8'))['edits'] if 'common weapon key' in e['label']];expected={};keys={}
 with TARGET.open('rb') as current:
  for ar in ['SHARED.BIN','IM.BIN']:
   _,master=rawmaster(current,ar);at,size,_=master.tables['Weap'];on=bytes(master.b[at:at+size]);off=bytearray(on);keys[ar]=[]
   for e in entries:
    if not e['label'].startswith(ar+' '):continue
    key=int(e['label'].rsplit(' ',1)[1]);index=u16(master.b,master.tables['WTbl'][0]+12+key*2);pos=12+index*36;assert on[pos:pos+36]==unpack(e,'after');off[pos:pos+36]=unpack(e,'before');keys[ar].append(key)
   expected[ar]=(bytes(off),on)
 comparisons=0
 for mask in range(2048):
  image=Image(p,mask)
  try:
   for ar in expected:
    _,m=rawmaster(image,ar);at,size,_=m.tables['Weap'];assert bytes(m.b[at:at+size])==expected[ar][int(bool(mask&32))],('common/maintenance weapon-table mismatch',mask,ar);comparisons+=1
  finally:image.f.close()
 native=0
 for mask in [0,32,256,288]:
  image=Image(p,mask)
  try:
   for ar in expected:
    _,m=rawmaster(image,ar);vm=VM(ram(p,mask));vm.load_master(m.b)
    for key in keys[ar]:
     index=u16(m.b,m.tables['WTbl'][0]+12+key*2);row=m.b[m.tables['Weap'][0]+12+index*36:m.tables['Weap'][0]+12+(index+1)*36]
     for fn,want in [(0x274ff0,int.from_bytes(row[8:10],'little')),(0x274cf0,row[0x1a]),(0x274d70,row[0x19])]:assert vm.cpu.run(fn,[vm.master,key])==want;native+=1
  finally:image.f.close()
 return {'whole_weapon_table_comparisons':comparisons,'native_accessor_checks':native,'common_weapon_toggle_independent_of_maintenance':True,'unrelated_and_cloned_weapon_rows_preserved':True}

def main():
 p=Profiles();result={'passed':True,'pack_sha256':hashlib.sha256((HERE.parent/'release_v20261107.5/patcher/OGG_options.bin').read_bytes()).hexdigest(),'supply_story_independence':supply_checks(p)}
 result['sp_costs_and_upgrade_prices']=price_and_sp_checks(p)
 result['legacy_inputs']=legacy_checks(p)
 result['party_profiles']=party_profile_checks(p)
 result['story_consistency_profiles']=consistency_profile_checks(p)
 result['support_overhaul_profiles']=support_overhaul_profiles(p)
 result['common_weapon_maintenance_cross_checks']=common_weapon_cross_checks(p)
 # Test each native arithmetic feature while its independent neighbor is off/on.
 r={mask:ram(p,mask) for mask in [0,8,16,24]}
 result['rewards_enemy_off']=reward_checks([r[0],r[8]])
 result['rewards_enemy_on']=reward_checks([r[16],r[24]])
 result['enemy_rewards_off']=hostile_checks([r[0],r[16]])
 result['enemy_rewards_on']=hostile_checks([r[8],r[24]])
 (HERE/'native_options_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
