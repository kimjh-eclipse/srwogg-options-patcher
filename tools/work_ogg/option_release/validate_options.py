"""Validate packaged scripts/hooks using the actual game's R5900 routines."""
from pathlib import Path
import sys,struct,zlib,io,json,bisect
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inspect_iso import SOURCE,OUT,inventory,u32
from build_options import rawmaster
from audit_story_layout import loadarc
from story_scripts_25 import records
from campaign_bonus_scripts import EARLY
from story_vm import VM
from validate_campaign_tuning import hostile_checks,reward_checks

HERE=Path(__file__).resolve().parent

class Profiles:
 def __init__(self):
  f=io.BytesIO((HERE.parent/'release_v20261106/patcher/OGG_options.bin').read_bytes())
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

def main():
 p=Profiles();result={'passed':True,'supply_story_independence':supply_checks(p)}
 # Test each native arithmetic feature while its independent neighbor is off/on.
 r={mask:ram(p,mask) for mask in [0,8,16,24]}
 result['rewards_enemy_off']=reward_checks([r[0],r[8]])
 result['rewards_enemy_on']=reward_checks([r[16],r[24]])
 result['enemy_rewards_off']=hostile_checks([r[0],r[16]])
 result['enemy_rewards_on']=hostile_checks([r[8],r[24]])
 (HERE/'native_options_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
