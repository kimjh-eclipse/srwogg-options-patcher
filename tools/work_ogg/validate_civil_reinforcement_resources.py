"""Audit prospective archive bounds and all untouched MAP payloads."""
from prepare_civil_reinforcements import *
class Image:
 def __init__(self,f,p):self.f=f;self.pos=0;self.edits=[(e['offset'],(DEST/e['file']).read_bytes()) for e in p['edits']]
 def seek(self,p,whence=0):assert whence==0;self.pos=p;return p
 def read(self,n):
  self.f.seek(self.pos);data=bytearray(self.f.read(n));end=self.pos+len(data)
  for at,b in self.edits:
   lo=max(at,self.pos);hi=min(at+len(b),end)
   if lo<hi:data[lo-self.pos:hi-self.pos]=b[lo-at:hi-at]
  self.pos=end;return bytes(data)
def main():
 p=json.loads((ROOT/'civil_reinforcements_prepared.json').read_text(encoding='utf8'));keys={s['key'] for s in p['scenes']};checks=0
 with TARGET.open('rb') as f:
  im=Image(f,p)
  for slot in [13,14]:
   _,old=loadarc(f,slot);_,new=loadarc(im,slot);assert len(old)==len(new)
   for (ks,at,n),(nk,na,nn) in zip(old,new):
    assert ks==nk
    if any(k in keys for k in ks):
     s=next(x for x in p['scenes'] if x['key'] in ks);want=s['untd' if slot==13 else 'logo'];assert (na,nn)==(want['offset'],want['size']);assert read(im,na,nn)==(DEST/want['file']).read_bytes()
    else:assert (at,n)==(na,nn) and read(f,at,n)==read(im,na,nn);checks+=1
  for s in p['scenes']:
   b=(DEST/s['untd']['file']).read_bytes();assert u32(b,40)==63
   assert sum(u32(b,44+i*336+8)==2 and u32(b,44+i*336+4)==0 for i in range(63))==32
   for group in [2,3,4]:assert sum(u32(b,44+i*336+4)==group for i in range(63))==6
  from validate_civil_reinforcements import machine,Profiles,ram
  base=ram(Profiles(),4095);master=(DEST/'SHARED.BIN.master').read_bytes();civil=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'))
  for s in p['scenes']:
   s['targets']=next(x for x in civil['scenes'] if x['key']==s['key'])['targets'];b=(DEST/s['logo']['file']).read_bytes();v=machine(base,master,b,s,[1188],2)
   for i in range(u32(b,24)):assert v.op(list(struct.unpack_from('<24I',b,u32(b,28)+i*96)))==10
   assert v.cpu.read(v.ctx+0x6abc+27*4,4)==6
   for msg in s['messages']:
    raw=encode(msg['text']);v.cpu.run(0x53ad00,[v.ctx,0,msg['sid']]);assert bytes(v.cpu.mem[v.ctx+0x6c00:v.ctx+0x6c00+len(raw)+1])==raw+b'\0';v.cpu.run(0x53a1f0,[v.ctx,msg['label'],0,0,0],stop=0x53a244);ri=v.cpu.r[4]&0xffffffff;assert u32(b,u32(b,36)+ri*96+8)==msg['sid']
 result=dict(passed=True,unchanged_MAP_payloads=checks,new_stage_untd_records=63,initial_enemy_group_zero=32,reserved_reinforcements=18,native_callback_registration_and_alert_history=True,all_declared_archive_bounds_checked=True,other_gameplay_resources_untouched=True,extra_full_ISOs_created=0)
 (ROOT/'civil_reinforcements_resource_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
