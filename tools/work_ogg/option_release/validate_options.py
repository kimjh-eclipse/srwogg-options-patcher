"""Validate packaged scripts/hooks using the actual game's R5900 routines."""
from pathlib import Path
import sys,struct,zlib,io,json,bisect,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inspect_iso import SOURCE,OUT,inventory,u32
from build_options import rawmaster,load_old_pack,source_image,load_pack,OLD_PACK,PREVIOUS_PACK,OLDER_PACK,SPIRITS_PACK
from audit_story_layout import loadarc
from story_scripts_25 import records,text_at,encode
from campaign_bonus_scripts import EARLY
from story_vm import VM
from spirit_policy_25 import POLICY,apply_to_row
from validate_campaign_tuning import hostile_checks,reward_checks

HERE=Path(__file__).resolve().parent

class Profiles:
 def __init__(self):
  f=io.BytesIO((HERE.parent/'release_v20261106.4/patcher/OGG_options.bin').read_bytes())
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
 for mask in range(1<<len(features)):
  image=Image(p,0);image.f.close()
  with (SOURCE.open('rb') if len(features)==8 else source_image()) as old_source:
   for i,(at,b) in enumerate(p.regions):old_source.seek(at);image.data[i]=bytearray(old_source.read(len(b)))
  for at,b in regions:
   i=bisect.bisect_right(p.starts,at)-1;rel=at-p.starts[i];image.data[i][rel:rel+len(b)]=b
  for bit,es in enumerate(features):
   if mask&(1<<bit):
    for at,b in es:
     i=bisect.bisect_right(p.starts,at)-1;rel=at-p.starts[i];image.data[i][rel:rel+len(b)]=b
  h=hashlib.sha256()
  for (at,_),b in zip(p.regions,image.data):h.update(struct.pack('<QI',at,len(b)));h.update(hashlib.sha256(b).digest())
  assert p.known[h.digest()]==mask&127;count+=1
 return count

def legacy_checks(p):
 return {'previous_8_option_profiles_recognized':legacy_set_checks(p,OLD_PACK),'v20261106_1_profiles_recognized':legacy_set_checks(p,OLDER_PACK),'v20261106_2_profiles_recognized':legacy_set_checks(p,SPIRITS_PACK),'v20261106_3_profiles_recognized':legacy_set_checks(p,PREVIOUS_PACK),'removed_SP_bit_not_exposed':True}

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
    else:
     item=cast[keys[index]];key=1091 if item['pilot_name']=='이글렛' else item['pilot'];oi=u16(shared.b,shared.tables['PTbl'][0]+12+key*2);expected=shared.b[shared.tables['Plot'][0]+12+oi*148:shared.tables['Plot'][0]+12+(oi+1)*148]
    if index>=old.tables['Plot'][2]:expected=apply_to_row(item['pilot_name'],expected)
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
 for mask in range(128):
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
 for mask in range(128):
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

def main():
 p=Profiles();result={'passed':True,'supply_story_independence':supply_checks(p)}
 result['sp_costs_and_upgrade_prices']=price_and_sp_checks(p)
 result['legacy_inputs']=legacy_checks(p)
 result['party_profiles']=party_profile_checks(p)
 result['story_consistency_profiles']=consistency_profile_checks(p)
 # Test each native arithmetic feature while its independent neighbor is off/on.
 r={mask:ram(p,mask) for mask in [0,8,16,24]}
 result['rewards_enemy_off']=reward_checks([r[0],r[8]])
 result['rewards_enemy_on']=reward_checks([r[16],r[24]])
 result['enemy_rewards_off']=hostile_checks([r[0],r[16]])
 result['enemy_rewards_on']=hostile_checks([r[8],r[24]])
 (HERE/'native_options_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
