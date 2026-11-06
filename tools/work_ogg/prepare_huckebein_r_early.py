"""Increment the existing early-equipment event with one native unpiloted unit."""
from pathlib import Path
import sys,json,struct,hashlib
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_huckebein' if (ROOT/'option_huckebein').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from build_options import rawmaster,TARGET
from audit_story_layout import loadarc
from inspect_iso import read,u32
from catalog import u16
from story_scripts_25 import records,command,NONE,wrap,text_at,encode
from story_consistency_logo import guarded_block,replace_box
from campaign_bonus_scripts import insert_commands
from early_equipment_policy import FLAG,UNITS,WEAPONS
from prepare_early_equipment import execute,qty
from story_vm import VM

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('huckebein_r_early_applied')
 # The preceding release supplies the unchanged executable for offline checks.
 sys.path.insert(0,str(ROOT/'option_followup'))
 with TARGET.open('rb') as f:
  archive,es=loadarc(f,14);_,at,size=next(e for e in es if 2003 in e[0]);old=read(f,at,size)
  _,master=rawmaster(f,'SHARED.BIN');idx=u16(master.b,master.tables['UTbl'][0]+12+1209*2);row=master.b[master.tables['Unit'][0]+12+idx*100:master.tables['Unit'][0]+12+(idx+1)*100];name=master.text(u16(row,12));assert 'Ｒ' in name
  rs=records(old);start,end=guarded_block(old,FLAG);assert not any(r[0]==0x5f and r[2]==1209 for r in rs[start:end])
  text='빌트팔켄 L, 아슈세이버, 휴케바인 Mk-3 R을 한 기씩 지급한다. 기체만이다.'
  blob,note=replace_box(old,'카이','빌트팔켄',text,1090)
  point=next(i for i in range(start,end) if rs[i][0]==0x64)
  blob=insert_commands(blob,point,[command(0x5f,1209,NONE,NONE,NONE)])
  assert len(blob)==size+96 and not any(read(f,at+size,96))
  assert all(at+len(blob)<=lo or at>=lo+n for ks,lo,n in es if lo!=at)
  e=next(e for e in archive['entries'] if 2003 in e['keys']);dp=archive['directory']+8+e['index']*8
  before=read(f,at,len(blob))
 out=ROOT/'analysis/huckebein_r_early';out.mkdir(exist_ok=True);(out/'story.logo').write_bytes(blob)
 # Use only the prior release's RAM helper; its game executable is unchanged.
 from importlib.util import spec_from_file_location,module_from_spec
 spec=spec_from_file_location('prior_profiles',ROOT/'option_followup/validate_options.py');prior=module_from_spec(spec);spec.loader.exec_module(prior);base=prior.ram(prior.Profiles(),1023)
 cases=[]
 for enabled,owned in [(False,False),(True,False),(True,True)]:
  vm=VM(base);vm.load_master(master.b);c=vm.cpu
  if owned:
   for key,n in UNITS:assert vm.op(command(0x5f,key,NONE,NONE,NONE))==10
  saved_units=bytes(c.mem[vm.save+0x6efc:vm.save+0x6efc+128*216]);pilots=bytes(c.mem[vm.save+0x25cfc:vm.save+0x3b2fc])
  assert execute(vm,blob,enabled)==(5 if enabled else 0)
  for key,n in UNITS:assert (c.run(0x244c20,[vm.save,key,0,0])>=0)==(enabled or owned)
  assert [qty(vm,k) for k,n in WEAPONS]==[int(enabled)]*2
  assert bytes(c.mem[vm.save+0x25cfc:vm.save+0x3b2fc])==pilots
  if owned:assert bytes(c.mem[vm.save+0x6efc:vm.save+0x6efc+128*216])==saved_units
  save=bytes(c.mem[vm.save:vm.save+0x40000]);diff=bytes(c.mem[vm.diff:vm.diff+0x1300]);assert execute(vm,blob,enabled)==0;assert bytes(c.mem[vm.save:vm.save+len(save)])==save
  other=VM(base);other.load_master(master.b);other.cpu.mem[other.save:other.save+len(save)]=save;other.cpu.mem[other.diff:other.diff+len(diff)]=diff;assert execute(other,blob,enabled)==0
  cases.append({'enabled':enabled,'already_owned':owned,'grants':5 if enabled else 0,'no_pilot_changes':True,'repeat_and_saved_state_reload_grants':0})
 vm=VM(base);c=vm.cpu;address=0x1800000;c.mem[address:address+len(blob)]=blob;c.run(0x5363c0,[vm.ctx,address]);sid=note['string_id'];raw=encode(note['text']);c.run(0x53ad00,[vm.ctx,0,sid]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0'
 line=next(r for r in records(blob) if r[0]==0x30 and r[2]==sid);c.run(0x53a1f0,[vm.ctx,line[1],0,0,0],stop=0x53a244);assert u32(blob,u32(blob,36)+(c.r[4]&0xffffffff)*96+8)==sid
 p={'prepared':True,'before_sha256':state['current_sha256'],'offset':at,'size':len(blob),'before_extent_sha256':hashlib.sha256(before).hexdigest(),'pointer_offset':dp,'pointer_hex':struct.pack('<II',at-archive['directory'],len(blob)).hex(),'units':UNITS,'weapons':WEAPONS,'flag':FLAG,'dialogue':note}
 v={'passed':True,'added_unit_key':1209,'added_unit_name':name,'chapter':3,'new_pilots':0,'master_UNTD_and_other_units_unchanged':True,'native_text_history_checks':2,'cases':cases,'live_playthrough':False,'save_reload':'Save/Diff arrays restored into a new VM; no memory-card I/O'}
 for name,data in [('huckebein_r_early_prepared',p),('huckebein_r_early_validation',v)]: (ROOT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(v,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
