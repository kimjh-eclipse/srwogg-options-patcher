"""Prepare and verify the early equipment event; never boots PCSX2."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'option_followup' if (ROOT/'option_followup').exists() else ROOT/'option_release'),str(ROOT)]
from validate_options import Profiles,ram
from build_options import rawmaster
from audit_story_layout import loadarc
from story_scripts_25 import records,text_at,command,NONE
from inspect_iso import read,u32
from story_consistency_logo import guarded_block
from story_vm import VM
from early_equipment_policy import *

def execute(vm,blob,enabled):
 rs=records(blob);start,end=guarded_block(blob,FLAG);i=start;grants=0
 while i<end:
  r=rs[i].copy();vm.cpu.write(vm.ctx+0x48d0,i,4)
  if i==start+1 and not enabled:r[4]=2
  if r[0]==0x30:i+=1;continue
  assert r[0] in [0x93,0x91,0x5f,0x64,0xba];assert vm.op(r)==10
  grants+=r[0] in [0x5f,0x64];i=vm.cpu.read(vm.ctx+0x48d0,4)+1
 return grants

def qty(vm,key):return sum(vm.cpu.read(vm.save+0x21efc+i*4,2)==key for i in range(0x3e00//4))

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('early_equipment_applied');p=Profiles();base=ram(p,511)
 with Path(state['canonical_iso']).open('rb') as f:
  archive,es=loadarc(f,14)
  for ks,at,n in es:
   assert all(not(r[2:5]==[0x100c1,*FLAG]) for r in records(read(f,at,n))),('flag already used',ks)
  _,at,n=next(e for e in es if 2003 in e[0]);old=read(f,at,n);blob,note=script(old);end=STORY_ALLOCATION+len(blob)
  assert end<0x1b000000 and not any(read(f,STORY_ALLOCATION,len(blob)))
  assert all(end<=at or STORY_ALLOCATION>=at+len(b) for at,b in p.regions)
  e=next(e for e in archive['entries'] if 2003 in e['keys']);dp=archive['directory']+8+e['index']*8
  _,master=rawmaster(f,'SHARED.BIN')
 out=ROOT/'analysis/early_equipment';out.mkdir(exist_ok=True);(out/'story.logo').write_bytes(blob)
 text_checks=0;vm=VM(base);c=vm.cpu;address=0x1800000;c.mem[address:address+len(blob)]=blob;c.run(0x5363c0,[vm.ctx,address])
 for msg in note['messages']:
  raw=bytes.fromhex(msg['encoded']);c.run(0x53ad00,[vm.ctx,0,msg['string_id']]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0';c.run(0x53a1f0,[vm.ctx,msg['label'],0,0,0],stop=0x53a244);idx=c.r[4]&0xffffffff;assert u32(blob,u32(blob,36)+idx*96+8)==msg['string_id'];text_checks+=2
 cases=[]
 for enabled,owned in [(False,False),(True,False),(True,True)]:
  vm=VM(base);vm.load_master(master.b);c=vm.cpu
  assert vm.op(command(0x5f,1218,NONE,NONE,NONE))==10
  if owned:
   for key,name in UNITS:assert vm.op(command(0x5f,key,NONE,NONE,NONE))==10
  for key,name in WEAPONS:assert vm.op(command(0x64,key,0))==10
  original_slot=c.run(0x244c20,[vm.save,1218,0,0]);original=bytes(c.mem[vm.save+0x6efc+216*original_slot:vm.save+0x6efc+216*(original_slot+1)])
  pilots=bytes(c.mem[vm.save+0x25cfc:vm.save+0x3b2fc]);existing={key:bytes(c.mem[vm.save+0x6efc+216*c.run(0x244c20,[vm.save,key,0,0]):vm.save+0x6efc+216*(c.run(0x244c20,[vm.save,key,0,0])+1)]) for key,name in UNITS} if owned else {}
  assert execute(vm,blob,enabled)==(4 if enabled else 0)
  for key,name in UNITS:
   slot=c.run(0x244c20,[vm.save,key,0,0]);assert (slot>=0)==(enabled or owned)
   if owned:assert bytes(c.mem[vm.save+0x6efc+216*slot:vm.save+0x6efc+216*(slot+1)])==existing[key]
  assert [qty(vm,k) for k,n in WEAPONS]==[1+int(enabled)]*2
  assert bytes(c.mem[vm.save+0x25cfc:vm.save+0x3b2fc])==pilots
  assert bytes(c.mem[vm.save+0x6efc+216*original_slot:vm.save+0x6efc+216*(original_slot+1)])==original
  save=bytes(c.mem[vm.save:vm.save+0x40000]);diff=bytes(c.mem[vm.diff:vm.diff+0x1300]);assert execute(vm,blob,enabled)==0
  assert bytes(c.mem[vm.save:vm.save+len(save)])==save and bytes(c.mem[vm.diff:vm.diff+len(diff)])==diff
  vm=VM(base);vm.load_master(master.b);vm.cpu.mem[vm.save:vm.save+len(save)]=save;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff;assert execute(vm,blob,enabled)==0
  cases.append({'enabled':enabled,'already_owned_units':owned,'grant_commands':4 if enabled else 0,'pilots_unchanged':True,'existing_unit_records_preserved':True,'repeat_and_saved_state_reload_grants':0})
 prepared={'prepared':True,'before_sha256':state['current_sha256'],'offset':STORY_ALLOCATION,'size':len(blob),'pointer_offset':dp,'pointer_hex':struct.pack('<II',STORY_ALLOCATION-archive['directory'],len(blob)).hex(),'flag':list(FLAG),'units':UNITS,'weapons':WEAPONS,'note':note}
 (ROOT/'early_equipment_prepared.json').write_text(json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf-8')
 result={'passed':True,'chapter':3,'flag':list(FLAG),'units':UNITS,'weapons':WEAPONS,'native_text_history_checks':text_checks,'cases':cases,'unit_pilot_weapon_master_data_changed':False,'new_pilots':0,'live_playthrough':False,'save_reload':'Save/Diff arrays restored into a fresh VM; no memory-card I/O'}
 (ROOT/'early_equipment_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
