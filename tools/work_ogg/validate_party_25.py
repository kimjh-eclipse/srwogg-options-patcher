"""Exercise actual persistent-roster handlers against a populated party.

Map actor lookups are absent-actor fixtures; persistent save routines are real.
This is not a full map/pathfinding/PCSX2 playthrough.
"""
from pathlib import Path
import sys,json,struct,collections,time
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_party' if (ROOT/'option_party/validate_options.py').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from story_vm import VM,CPU,TABLE
from catalog import Master,u16
from compare_ogs_units import getmaster
from inspect_iso import read,u32
from audit_story_layout import loadarc
from story_scripts_25 import records,command,NONE
from party_policy_25 import apply_to_master,edits_for_master

STORY=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'))
RECRUITS=[r for ch in STORY['chapters'] for r in ch['recruits']]
KEYS=[r['key'] for r in RECRUITS]
OPS={0x40,0x41,0x4a,0x80,0x81,0x86,0x8b,0x8c,0xc4,0xd4,0xd5,0xd6,0xdd}

class PartyCPU(CPU):
 def step(self):
  if self.pc in [0x213d90,0x214440]:
   self.write(0x17e0000+0x18,0xffffffff,4);self.put(2,0x17e0000);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  else:super().step()

def machine(base,master):
 vm=VM(base);vm.cpu=PartyCPU(bytes(vm.cpu.mem));vm.cpu.r[28]=0x31def0;vm.load_master(master);return vm

def inventory():
 commands=[];templates={};pilot_templates={}
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
  _,units=loadarc(f,13);_,scripts=loadarc(f,14)
  for ks,at,n in units:
   if not any(2001<=k<=2070 for k in ks):continue
   b=read(f,at,n)
   for i in range(u32(b,40)):
    row=b[44+i*336:44+(i+1)*336];uk=u32(row);pk=u32(row,32)
    if uk<1792 and pk<1792:
     templates.setdefault(uk,row);pilot_templates.setdefault(pk,row)
  for ks,at,n in scripts:
   if not any(2001<=k<=2070 for k in ks):continue
   for i,r in enumerate(records(read(f,at,n))):
    if r[0] in OPS:commands.append({'script':ks[0],'row':i,'record':r})
 return commands,templates,pilot_templates

def slots(vm):
 return {k:(vm.cpu.run(0x244c20,[vm.save,k,0,0]),vm.cpu.run(0x244a40,[vm.save,k,1,0])) for k in KEYS}

def snapshot(vm,index):
 c=vm.cpu;out={}
 for key,(u,p) in index.items():
  assert u>=0 and p>=0
  out[key]=(bytes(c.mem[vm.save+0x6efc+u*216:vm.save+0x6efc+(u+1)*216]),bytes(c.mem[vm.save+0x25cfc+p*92:vm.save+0x25cfc+(p+1)*92]))
 return out

def seed_clones(vm):
 for i,recruit in enumerate(RECRUITS):
  row=bytearray.fromhex(recruit['row_hex'])
  for p in range(0x38,0x50,4):struct.pack_into('<I',row,p,(i%5)+1)
  struct.pack_into('<I',row,0x50,10000+i*500)
  assert vm.birth(row)==1,recruit['name']
 index=slots(vm)
 for i,key in enumerate(KEYS):
  u,p=index[key];at=vm.save+0x25cfc+p*92
  vm.cpu.write(at+6,17+i,2);vm.cpu.write(at+8,101+i*7,2)
 return index

def normalize(row):
 b=bytearray(row);struct.pack_into('<I',b,8,0)
 for p in range(0x38,0x50,4):struct.pack_into('<I',b,p,0)
 for p in [0x50,0x54,0x58]:struct.pack_into('<I',b,p,5000)
 return bytes(b)

def seed_native(vm,master,commands,templates,pilot_templates):
 m=Master(master);units=set();pilots=set()
 for d in commands:
  r=d['record'];op=r[0]
  if r[2] in [0x100bd,0x100a8]:
   key=r[3];target=units if r[2]==0x100bd else pilots;tag='UTbl' if r[2]==0x100bd else 'PTbl'
  elif op in [0x81,0x80,0xc4,0xd4,0xdd] and r[2]<1792:
   key=r[2];target=units if op==0x81 else pilots;tag='UTbl' if op==0x81 else 'PTbl'
  else:continue
  if 0<=key<1792 and u16(master,m.tables[tag][0]+12+key*2)!=65535:target.add(key)
 for key in sorted(units):
  assert vm.op(command(0x5f,key,NONE,NONE,NONE))==10,('native unit fixture',key)
 for key in sorted(pilots):
  if vm.cpu.run(0x244a40,[vm.save,key,1,0])>=0:continue
  slot=vm.cpu.run(0x24b180,[vm.save,key,0]);assert slot>=0,('native pilot fixture',key)
  vm.cpu.run(0x247c60,[vm.save,2,slot,1,0])
 return len(units),len(pilots)

def alias_regression(base,old,fixed):
 result=[]
 for progress in [0,14,35]:
  for has_native in [False,True]:
   outputs=[]
   for blob in [old,fixed]:
    vm=machine(base,blob);c=vm.cpu;c.write(vm.diff+0x1000,progress,4)
    # Clone first is intentional: the original family scan previously picked it.
    recruit=next(r for r in RECRUITS if r['name']=='린');assert vm.birth(bytes.fromhex(recruit['row_hex']))==1
    if has_native:assert vm.op(command(0x5f,0x4ad,NONE,NONE,NONE))==10
    idx={0x701:(c.run(0x244c20,[vm.save,0x701,0,0]),c.run(0x244a40,[vm.save,0x701,1,0]))}
    before=snapshot(vm,idx);assert vm.op(command(0x4a,0x100bd,0x4ad,0))==10;after=snapshot(vm,idx)
    outputs.append(before!=after)
    if blob is fixed:assert before==after
   assert outputs==[True,False],(progress,has_native,outputs)
   result.append({'cleared_chapters':progress,'native_unit_present':has_native,'old_collateral_change':True,'fixed_clone_preserved':True})
 return result

def recovery_checks(base,old,fixed):
 vm=machine(base,old);c=vm.cpu;rec=next(r for r in RECRUITS if r['name']=='린');row=bytearray.fromhex(rec['row_hex'])
 for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,5)
 assert vm.birth(row)==1
 index={0x701:(c.run(0x244c20,[vm.save,0x701,0,0]),c.run(0x244a40,[vm.save,0x701,1,0]))}
 p=vm.save+0x25cfc+index[0x701][1]*92;c.write(p+6,77,2);c.write(p+8,901,2);c.write(p+10,24000,2)
 before=snapshot(vm,index);assert vm.op(command(0x4a,0x100bd,0x4ad,0))==10;assert snapshot(vm,index)!=before
 vm.load_master(fixed);assert vm.op(command(0x4a,0x100bd,0x701,1))==10;assert snapshot(vm,index)==before
 saved=bytes(c.mem[vm.save:vm.save+0x40000]);assert vm.op(command(0x4a,0x100bd,0x701,1))==10;assert saved==bytes(c.mem[vm.save:vm.save+len(saved)])
 empty=machine(base,fixed);before_empty=bytes(empty.cpu.mem[empty.save:empty.save+0x40000]);assert empty.op(command(0x4a,0x100bd,0x701,1))==10
 assert before_empty==bytes(empty.cpu.mem[empty.save:empty.save+len(before_empty)])
 return {'already_affected_clone_reactivated':True,'experience_PP_grades_preserved':True,'repeat_recovery_no_change':True,'absent_clone_not_granted':True}

def command_checks(base,master,commands,templates,pilot_templates):
 vm=machine(base,master);index=seed_clones(vm);native_counts=seed_native(vm,master,commands,templates,pilot_templates)
 assert slots(vm)==index
 c=vm.cpu;save=bytes(c.mem[vm.save:vm.save+0x40000]);diff=bytes(c.mem[vm.diff:vm.diff+0x1300]);expected=snapshot(vm,index)
 by_op=collections.Counter();errors=[]
 for d in commands:
  c.mem[vm.save:vm.save+len(save)]=save;c.mem[vm.diff:vm.diff+len(diff)]=diff
  r=d['record']
  try:
   got=vm.op(r);assert got==(5 if r[0]==0x86 else 10),('unexpected handler return',got)
   actual=snapshot(vm,index)
   for key in KEYS:
    a,b=expected[key];x,y=actual[key]
    if r[0]==0xc4 and r[2]==0x10003:
     b=bytearray(b);y=bytearray(y);b[0x2d]&=~3;y[0x2d]&=~3
    assert a==x and b==y,('clone record changed',hex(key))
   assert slots(vm)==index,('clone ownership/slots changed',d)
   by_op[hex(r[0])]+=1
  except Exception as e:errors.append({'script':d['script'],'row':d['row'],'opcode':hex(r[0]),'error':str(e)})
  if sum(by_op.values())%150==0:print('Native roster handlers tested:',sum(by_op.values()),flush=True)
 return {'cases':sum(by_op.values()),'by_opcode':dict(by_op),'native_unit_target_types':native_counts[0],'native_pilot_targets':native_counts[1],'errors':errors,'map_actor_lookups':'absent-actor fixtures; all save mutations executed natively'}

def guard_reload_checks(base,master):
 vm=machine(base,master);events=0;repeats=0;reloads=0;guarded=[]
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
  _,scripts=loadarc(f,14)
  for ch in STORY['chapters']:
   _,at,n=next(e for e in scripts if ch['key'] in e[0]);rows=records(read(f,at,n));group,bit=ch['flag']
   start=next(i for i,r in enumerate(rows) if r[0]==0x93 and r[2:5]==[0x100c1,group,bit])
   end=next(i for i in range(start+1,len(rows)) if rows[i][0]==0xba and rows[i][2:5]==[0x100c1,group,bit])+1
   def block():
    i=start;spawned=0
    while i<end:
     r=rows[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
     if r[0]==0x30:i+=1;continue
     if r[0]==0xca:
      assert r[2]==ch['group']
      for recruit in ch['recruits']:assert vm.birth(bytes.fromhex(recruit['row_hex']))==1;spawned+=1
      i+=1;continue
     assert r[0] in [0x93,0x91,0xba];assert vm.op(r)==10;i=vm.cpu.read(vm.ctx+0x48d0,4)+1
    return spawned
   assert block()==len(ch['recruits']);events+=len(ch['recruits'])
   current=[r['key'] for chapter in STORY['chapters'] if chapter['chapter']<=ch['chapter'] for r in chapter['recruits']]
   for i,key in enumerate(current):
    pilot=vm.cpu.run(0x244a40,[vm.save,key,1,0]);assert pilot>=0
    vm.cpu.write(vm.save+0x25cfc+pilot*92+6,40+i,2);vm.cpu.write(vm.save+0x25cfc+pilot*92+8,400+i,2)
   save=bytes(vm.cpu.mem[vm.save:vm.save+0x40000]);diff=bytes(vm.cpu.mem[vm.diff:vm.diff+0x1300])
   assert block()==0 and save==bytes(vm.cpu.mem[vm.save:vm.save+len(save)]) and diff==bytes(vm.cpu.mem[vm.diff:vm.diff+len(diff)]);repeats+=1
   if ch['chapter'] in [8,19,31]:
    vm=machine(base,master);vm.cpu.mem[vm.save:vm.save+len(save)]=save;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff
    assert block()==0 and save==bytes(vm.cpu.mem[vm.save:vm.save+len(save)]) and diff==bytes(vm.cpu.mem[vm.diff:vm.diff+len(diff)]);reloads+=1
   guarded.append(ch['chapter'])
 assert events==25
 index=slots(vm);assert all(u>=0 and p>=0 for u,p in index.values())
 # Exercise a native cross-boarding pair and confirm both directions survive
 # restoration of persistent save data without re-running recruitment.
 c=vm.cpu;u1,p1=index[0x701];u2,p2=index[0x70f]
 assert c.run(0x24a560,[vm.save,p1,u2,0])==1
 assert c.run(0x24a560,[vm.save,p2,u1,0])==1
 assert c.run(0x24a430,[vm.save,p1])==u2 and c.run(0x24a430,[vm.save,p2])==u1
 save=bytes(c.mem[vm.save:vm.save+0x40000]);diff=bytes(c.mem[vm.diff:vm.diff+0x1300]);vm=machine(base,master)
 vm.cpu.mem[vm.save:vm.save+len(save)]=save;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff
 assert vm.cpu.run(0x24a430,[vm.save,p1])==u2 and vm.cpu.run(0x24a430,[vm.save,p2])==u1
 return {'native_recruits_registered':events,'repeat_blocks_skipped':repeats,'persistent_state_reloads':reloads+1,'cross_boarding_relations_preserved':True,'chapters':guarded,'deployment':'group command intercepted; actual native UNTD constructor executed','reload':'persistent Save/Diff arrays restored into a fresh native-code VM; no PCSX2 memory-card I/O'}

def main():
 commands,templates,pilot_templates=inventory();base=ram(Profiles(),127);old=bytes(getmaster(ROOT.parent/'SRWOGS_EX_K_TEST.ISO').b);fixed=apply_to_master(old,KEYS)
 if fixed==old:
  # Reconstruct only the old alias in memory to keep the regression repeatable
  # after the canonical image has been fixed. Never write this fixture to ISO.
  b=bytearray(old);m=Master(b);idx=u16(b,m.tables['UTbl'][0]+12+0x701*2);at=m.tables['Unit'][0]+12+idx*100
  for pos in [at,at+struct.unpack_from('<h',b,at+0x62)[0]]:struct.pack_into('<h',b,pos+0x14,0x4af)
  old=bytes(b);assert apply_to_master(old,KEYS)==fixed
 assert fixed!=old
 result={'passed':False,'live_playthrough':False,'script_count':len(set(d['script'] for d in commands)),'target_commands':len(commands),'alias_regression':alias_regression(base,old,fixed),'existing_save_recovery':recovery_checks(base,old,fixed)}
 print('Alias regression reproduced and fixed.',flush=True)
 result['native_roster_handlers']=command_checks(base,fixed,commands,templates,pilot_templates)
 result['recruitment_and_reload']=guard_reload_checks(base,fixed)
 result['passed']=not result['native_roster_handlers']['errors']
 (ROOT/'party_25_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
 assert result['passed']

if __name__=='__main__':main()
