"""Targeted dialogue/event verification; no emulator or gameplay playthrough."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_support' if (ROOT/'option_support').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from story_vm import VM
from story_scripts_25 import records,text_at,command
from story_consistency_logo import guarded_block
from inspect_iso import u32

def run_interval(vm,blob,start,end):
 rs=records(blob);i=start;shown=[]
 while i<end:
  r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0]==0x30:shown.append(r[2]);i+=1;continue
  assert r[0] in [0x93,0x91,0xba];assert vm.op(r)==10;i=vm.cpu.read(vm.ctx+0x48d0,4)+1
 return shown

def main():
 p=json.loads((ROOT/'followup_story_prepared.json').read_text(encoding='utf-8'));assert p['prepared'];base=ram(Profiles(),511);checks=hist=0;scenes=[];blobs={}
 for s in p['scenes']:
  blob=(ROOT/'analysis/followup_prepared'/f'{s["key"]}.logo').read_bytes();blobs[s['chapter']]=blob;rs=records(blob);vm=VM(base);c=vm.cpu;address=0x1800000;c.mem[address:address+len(blob)]=blob;c.run(0x5363c0,[vm.ctx,address]);prefix=u32(blob,32)
  for i,r in enumerate(rs):
   if r[0]==0x30:assert u32(blob,u32(blob,60)+r[1]*4)==prefix+i;hist+=1
  for msg in s['messages']:
   raw=bytes.fromhex(msg['encoded']);assert len(raw)<128 and text_at(blob,msg['string_id'])==raw;c.run(0x53ad00,[vm.ctx,0,msg['string_id']]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0';c.run(0x53a1f0,[vm.ctx,msg['label'],0,0,0],stop=0x53a244);i=c.r[4]&0xffffffff;assert u32(blob,u32(blob,36)+i*96+8)==msg['string_id'];checks+=2
  start,end=guarded_block(blob,s['flag']);assert all(r[0] in [0x93,0x91,0x30,0xba] for r in rs[start:end]);vm=VM(base);assert len(run_interval(vm,blob,start,end))==len(s['messages']);assert not run_interval(vm,blob,start,end)
  save=bytes(vm.cpu.mem[vm.save:vm.save+0x40000]);diff=bytes(vm.cpu.mem[vm.diff:vm.diff+0x1300]);vm=VM(base);vm.cpu.mem[vm.save:vm.save+len(save)]=save;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff;assert not run_interval(vm,blob,start,end);assert bytes(vm.cpu.mem[vm.save:vm.save+len(save)])==save
  scenes.append({'chapter':s['chapter'],'boxes':len(s['messages']),'repeat_and_saved_state_reload_skipped':True})
 # The new chapter29 scene must remain visible when optional maintenance is off.
 combo=[];blob=blobs[29];start,end=guarded_block(blob,[63,2]);ms,me=guarded_block(blob,[63,1]);assert end==ms
 for enabled in [False,True]:
  b=bytearray(blob)
  if not enabled:
   pos=u32(b,44)+(ms+1)*96+4*4;b[pos:pos+4]=(2).to_bytes(4,'little')
  vm=VM(base);n=len(run_interval(vm,b,start,me));assert n==16+(3 if enabled else 0);assert not run_interval(vm,b,start,me);combo.append({'maintenance_enabled':enabled,'new_followup_boxes':16,'maintenance_boxes':3 if enabled else 0})
 # Older saves that have seen the short epilogue still get this new scene if
 # the enclosing native event is entered again; the old block remains skipped.
 blob=blobs[36];start,end=guarded_block(blob,[63,5]);es,ee=guarded_block(blob,[62,5]);assert end==es
 for seen in [False,True]:
  vm=VM(base)
  if seen:assert vm.op(command(0xba,0x100c1,62,5))==10
  assert len(run_interval(vm,blob,start,ee))==16+(0 if seen else 8);assert not run_interval(vm,blob,start,ee)
  assert [r for r in records(blob) if r[0]==0x30][-1][2]==718
 result={'passed':True,'scope':'targeted native dialogue/history and persistent event flags; no playthrough','live_playthrough':False,'scenes':scenes,'scene_count':5,'new_boxes':p['boxes'],'native_string_history_checks':checks,'dialogue_history_entries_checked':hist,'native_original_records_and_strings_preserved':True,'only_text_and_event_flags_added':True,'chapter29_maintenance_independence':combo,'old_epilogue_state_independence':True,'original_final_lines_still_last':True,'save_reload':'persistent Save/Diff arrays restored into a fresh VM; no memory-card I/O'}
 (ROOT/'followup_story_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
