"""Native text, stage access, branch and roster checks for prepared missions.

These checks do not stand in for a rendered battle or a memory-card load.
"""
from pathlib import Path
import sys,json,struct,hashlib
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_huckebein' if (ROOT/'option_huckebein').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from story_vm import VM,CPU
from regional_five_policy import *
from inspect_iso import read

def load_campaign_master(vm,blob):
 vm.load_master(blob)
 # Stag has an extra native row pointer; all following table objects shift4.
 for i,k in reversed(list(enumerate(range(0x18,0x8c,4)))):
  if i>16:
   a=vm.master+0x28+i*24;vm.cpu.mem[a+4:a+28]=vm.cpu.mem[a:a+24]
 vm.cpu.write(vm.master+0x1a8+24,0x1900000+Master(blob).tables['Stag'][0]+32,4)

class CountCPU(CPU):
 def step(self):
  if self.pc==0x2129e0:
   side=self.r[5]&0xffffffff;assert side in [0,2]
   self.put(2,self.counts[side]);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  else:super().step()

def condition_machine(base,allies,enemies):
 vm=VM(base);vm.cpu=CountCPU(base);vm.cpu.r[28]=0x31def0;vm.cpu.counts={0:allies,2:enemies};vm.cpu.write(vm.ctx+0x2870,0x319d40,4)
 for i in range(16):vm.cpu.write(vm.ctx+0x74ec+i*4,0xffffffff,4)
 vm.cpu.write(0x46ecec,0,4);return vm

def condition_event(vm,blob,start):
 rs=records(blob);i=start;shown=[]
 while i<len(rs):
  r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0] in [0x3e,0x25]:return None,shown
  if r[0]==0x30:shown.append(r[2])
  elif r[0] in [0x79,0x7a,0x93,0x91,0x9a,0xba]:
   result=vm.op(r)
   if result==13:return None,shown
   assert result==10
   i=vm.cpu.read(vm.ctx+0x48d0,4)+1;continue
  elif r[0]==0xa1:assert vm.op(r)==14;return r[2],shown
  else:assert r[0] in [0x26,0x7b,0x6d,0x67],r[0] # Render/result UI intentionally not emulated.
  i+=1
 raise AssertionError('event did not return')

def main():
 p=json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),2047);checks=0;reports=[]
 cast=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast'];expected={x['pilot_name'] for x in cast}-{ '아기라','세프타킨'}
 actual={n for s in SCENARIOS for n in s['focus']};assert actual==expected,(actual^expected)
 master=(ROOT/'analysis/regional_five/SHARED.BIN.master').read_bytes();m=Master(master);vm=VM(base);load_campaign_master(vm,master);c=vm.cpu
 for s in p['scenes']:
  value=c.run(0x2705c0,[vm.master,2,s['key']-2000]);assert value==s['number'];checks+=1
  ptr=c.run(0x270580,[vm.master,2,s['key']-2000]);raw=encode(s['title']);assert bytes(c.mem[ptr:ptr+len(raw)+1])==raw+b'\0';checks+=1
 for k,number in [(2033,40),(2034,41)]:assert c.run(0x2705c0,[vm.master,2,k-2000])==number;checks+=1
 for s in p['scenes']:
  blob=(ROOT/'analysis/regional_five'/s['logo']['file']).read_bytes();rows=records(blob);unit=(ROOT/'analysis/regional_five'/s['untd']['file']).read_bytes();vm=VM(base);c=vm.cpu;load_campaign_master(vm,master);at=0x1800000;c.mem[at:at+len(blob)]=blob;c.run(0x5363c0,[vm.ctx,at]);prefix=u32(blob,32)
  assert len(unit)==44+u32(unit,40)*336 and u32(unit,40)==28
  ur=[unit[44+i*336:44+(i+1)*336] for i in range(u32(unit,40))];assert sum(u32(r,8)==6 for r in ur)==12 and sum(u32(r,8)==2 for r in ur)==16
  for r in ur:
   if u32(r,8)==2:
    assert u32(r,32) in [1029,1023,1237]
    assert u16(m.b,m.tables['UTbl'][0]+12+u32(r)*2)<m.tables['Unit'][2]
    assert u16(m.b,m.tables['PTbl'][0]+12+u32(r,32)*2)<m.tables['Plot'][2]
  assert not any(r[0] in [0x5f,0x60,0x64,0x40,0x41,0xd5,0xd6,0xdd] for r in rows),'No roster/part/weapon grants or removals'
  for msg in s['messages']:
   r=next(r for r in rows if r[0]==0x30 and r[1]==msg['label']);assert u32(blob,u32(blob,60)+r[1]*4)==prefix+rows.index(r)
   raw=encode(msg['text']);c.run(0x53ad00,[vm.ctx,0,msg['sid']]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0'
   c.run(0x53a1f0,[vm.ctx,msg['label'],0,0,0],stop=0x53a244);ri=c.r[4]&0xffffffff;assert u32(blob,u32(blob,36)+ri*96+8)==msg['sid'];checks+=2
  for i in range(u32(blob,24)):
   ev=list(struct.unpack_from('<24I',blob,u32(blob,28)+i*96));assert vm.op(ev)==10
  assert c.read(vm.ctx+0x6abc+27*4,4)==3;checks+=1
  assert vm.op(command(0xc3,12))==10 and c.read(vm.ctx+0x7480,2)==12;checks+=1
  for scene in [0,1,2]:
   c.write(vm.ctx+0x74cc,scene,2)
   for target in [0,1,2]:assert vm.op(command(0x79,0x10018,target,NONE))==(10 if scene==target else 13);checks+=1
  for i in s['story_gates']:
   for enabled in [False,True]:
    assert vm.op(rows[i-1])==10;c.write(vm.ctx+0x48d0,i,4);cond=rows[i].copy();cond[4]=0 if enabled else 2;assert vm.op(cond)==10
    assert c.read(vm.ctx+0x48d0,4)==(i if enabled else i+cond[7]-1);checks+=1
  for flag in [0,1,2]:
   vm=VM(base);vm.cpu.write(0x46ecec,0,4);assert vm.op(command(0x93,0x10071,0,flag,0x800f,NONE,NONE,NONE))==10;assert vm.readreg(0x800f)==0
   assert vm.op(command(0xba,0x10071,0,flag))==10;assert vm.op(command(0x93,0x10071,0,flag,0x800f,NONE,NONE,NONE))==10;assert vm.readreg(0x800f)==1;checks+=2
  nxt=next(r[2] for r in rows if r[0]==0xa1 and r[2]<100);assert nxt==(s['key']-2000+1 if s['key']<2039 else 33)
  truth=[]
  for allies,enemies,started in [(0,0,False),(0,16,False),(12,16,True),(12,1,True),(12,0,True),(1,16,True),(0,16,True)]:
   for event in ['defeat','ending']:
    vm=condition_machine(base,allies,enemies);vm.cpu.write(vm.ctx+0x74cc,1,2)
    if started:assert vm.op(command(0xba,0x10071,0,0))==10
    result,shown=condition_event(vm,blob,s['functions'][event])
    expect=(0xffffffff if started and allies==0 else None) if event=='defeat' else (nxt if started and enemies==0 else None)
    assert result==expect,(s['key'],event,allies,enemies,started,result,expect);checks+=1
    truth.append(dict(allies=allies,enemies=enemies,deployment_finished=started,event=event,next_index=result))
  reports.append(dict(key=s['key'],title=s['title'],dialogue_boxes=len(s['messages']),next_index=nxt,victory_defeat_truth_table=truth))
 # Native stage-index and played-bit handling accepts every new index; it also
 # accepts returning to the original 35/36 indices. This is not map completion.
 vm=VM(base)
 for index in [35,36,37,38,39,33,34]:
  vm.cpu.run(0x173030,[vm.diff,index]);assert vm.cpu.read(vm.diff+0xffc,4)==index;checks+=1
 # Populate owned clones, then run the actual next-stage command and restore
 # persistent arrays into a fresh VM between each mission. No map actor, UI or
 # card-file simulation is substituted for a real playthrough.
 from validate_party_25 import seed_clones,snapshot
 vm=VM(base);load_campaign_master(vm,master);owned=seed_clones(vm);original=snapshot(vm,owned);vm.cpu.write(vm.diff+0xffc,32,4);reloads=[]
 for index in [35,36,37,38,39,33,34]:
  previous=vm.cpu.read(vm.diff+0xffc,4);assert vm.op(command(0xa1,index,0))==14
  assert vm.cpu.read(vm.diff+0xffc,4)==index
  assert vm.cpu.read(vm.diff+0x2cc+previous//8,1)&(1<<(previous%8))
  assert snapshot(vm,owned)==original
  saved=bytes(vm.cpu.mem[vm.save:vm.save+0x40000]);diff=bytes(vm.cpu.mem[vm.diff:vm.diff+0x1300])
  vm=VM(base);load_campaign_master(vm,master);vm.cpu.mem[vm.save:vm.save+len(saved)]=saved;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff
  assert vm.cpu.read(vm.diff+0xffc,4)==index and snapshot(vm,owned)==original;checks+=4;reloads.append(dict(previous_index=previous,next_index=index,played_flag_byte=hex(0x2cc+previous//8),roster_stats_preserved=True))
 assert vm.cpu.read(vm.diff+0x2d0,1)&0xfb==0xfb
 report=dict(passed=True,native_checks=checks,missions=reports,all_25_story_participants_covered=True,original_geometry_and_unit_weapon_pilot_tables_preserved=True,new_dialogue_only_when_story_enabled=True,party_creation_or_removal=False,persistent_Save_Diff_reload_cases=reloads,memory_card_IO_tested=False,scope='native text/history/stage getters/event registration/annihilation guards/next-stage handler and persistent array reload; army counts supplied by fixture, result/deployment UI and memory-card load not emulated',battle_playthrough_verified=False,ready_for_experimental_apply=True)
 (ROOT/'regional_five_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
