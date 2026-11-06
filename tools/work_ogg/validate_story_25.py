"""Structural and native-code checks of the complete prospective story patch."""
from story_scripts_25 import *
from story_vm import VM
from story_native_hooks import install,test_loops,test_average
from story_master_25 import PROFILES,get_record
from probe_native import elfmem
import numpy as np

def map_pilot_getters():
 old=elfmem(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso');new=(OUT/'terrain_fresh_ram.bin').read_bytes()
 a=np.frombuffer(new,dtype='<u4');start,end=0x260000//4,0x280000//4;out=[]
 for pc in [0x1a3ef0,0x1a3e70,0x1a3df0,0x1a3d70,0x1a3cf0,0x1a3c70]:
  w=np.frombuffer(old[pc:pc+128],dtype='<u4');mask=np.array([0xffff0000 if x>>26 else 0xffffffff for x in w],dtype=np.uint32)
  score=np.zeros(end-start,dtype=np.uint16);exact=score.copy()
  for j,x in enumerate(w):v=a[start+j:end+j];score+=((v&mask[j])==(x&mask[j]));exact+=(v==x)
  rank=score.astype(np.uint32)*64+exact;best=int(np.argmax(rank));out.append((best+start)*4);assert score[best]>=25
 assert len(set(out))==6;return out

def validate_masters(report):
 count=0;getters=map_pilot_getters();balance=json.loads((ROOT/'balance_plan_25_v1.json').read_text(encoding='utf8'))
 units={u['name']:u for u in balance['units']}
 for ar,note in report['master_changes'].items():
  vm=VM();c=vm.cpu;install(c);blob=(OUT/f'story_prepared/{ar}.master').read_bytes();m=Master(blob);vm.load_master(blob)
  for progress in [0,13,14,17,18,35]:
   c.write(vm.diff+0x1000,progress,4)
   for n in note['pilots']:
    for fn,stat in [(0x276f40,'hp'),(0x276ec0,'en'),(0x276d40,'armor'),(0x276e40,'move'),(0x276dc0,'mobility')]:
     assert c.run(fn,[vm.master,n['key']])==units[n['name']]['proposed_base'][stat],(ar,progress,n['name'],stat);count+=1
    assert c.run(0x275a80,[vm.master,n['key']])==0;count+=1
   for lock in note['locks']:
    pointer=c.run(0x278880,[vm.master+0x40,lock['full_unit_index']])
    full=progress>=lock['cleared_threshold'];expected=lock['full_weapon'] if full else lock['locked_weapon']
    assert c.read(pointer+0x24+lock['slot']*2,2)==expected
    _,wr=get_record(m,'Weap','WTbl',expected,36)
    assert (wr[0x1b]==255)==(not full);count+=2
  for n in note['pilots']:
   for fn,want in zip(getters,n['after'][1:]):assert c.run(fn,[vm.master,n['key']])==want,(hex(fn),n['name']);count+=1
   _,p=get_record(m,'Plot','PTbl',n['key'],148)
   assert 40<=p[0x64]<=60 and 43 not in p[0x7e:0x84];assert all(x in [0,1] for x in p[0x72:0x78]);count+=2
 return count,getters

def validate_text(report):
 vm=VM();c=vm.cpu;ctx=vm.ctx;base=0x1800000;count=0
 for ch in report['chapters']:
  b=(OUT/f"story_prepared/{ch['key']}.logo").read_bytes();c.mem[base:base+len(b)]=b;c.run(0x5363c0,[ctx,base])
  prefix=u32(b,32);n=u32(b,40);assert u32(b,44)==u32(b,36)+prefix*96
  original=(OUT/f"story_layout/{ch['key']}.bin").read_bytes();pt=ch['before_record']
  for i,row in enumerate(records(original)[:pt]):
   if row[0] in [0x90,0x91]:
    for field in ([6,7] if row[0]==0x90 else [7]):
     assert row[field]>=0x80000000 or i+row[field]<=pt,('recruitment could be conditionally skipped',ch['chapter'],i)
  for i in range(u32(b,48)):
   p=u32(b,52)+i*16;kind,target=u32(b,p),u32(b,p+8)
   if kind==0 or kind in ch['active_script_sheets']:
    assert 0<=target<=(n if kind else prefix),(ch['chapter'],i,kind,target,n,prefix)
  for msg in ch['messages']:
   raw=bytes.fromhex(msg['encoded']);assert len(raw)<128
   c.run(0x53ad00,[ctx,0,msg['string_id']]);assert bytes(c.mem[ctx+0x6c00:ctx+0x6c00+len(raw)])==raw
   c.run(0x53a1f0,[ctx,msg['label'],0,0,0],stop=0x53a244);idx=c.r[4]&0xffffffff
   p=u32(b,36)+idx*96
   assert u32(b,p)==0x30 and u32(b,p+4)==msg['label'] and u32(b,p+8)==msg['string_id']
   count+=2
 return count

def simulate_block(vm,ch,spawn=True):
 rows=ch['inserted_rows'];i=0;spawns=0;messages=0
 while i<len(rows):
  r=rows[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0]==0x30:messages+=1;i+=1;continue
  if r[0]==0xca:
   assert r[2]==ch['group']
   if spawn:
    for recruit in ch['recruits']:assert vm.birth(bytes.fromhex(recruit['row_hex']))==1;spawns+=1
   i+=1;continue
  assert r[0] in [0x93,0x91,0xba]
  vm.op(r);i=vm.cpu.read(vm.ctx+0x48d0,4)+1
 return spawns,messages

def validate_recruitment(report):
 vm=VM();c=vm.cpu;install(c);blob=(OUT/'story_prepared/SHARED.BIN.master').read_bytes();vm.load_master(blob)
 # Start with the three original chapter-one allies through the real constructor.
 with SOURCE.open('rb') as f:
  a,es=loadarc(f,13);_,p,n=next(x for x in es if 2001 in x[0]);b=read(f,p,n)
  # loadarc reads current entries; source has the original three-ally payload.
  initial=[b[44+i*336:44+(i+1)*336] for i in range(u32(b,40)) if u32(b,44+i*336+8)==0]
  assert len(initial)==3
  for r in initial:assert vm.birth(r)==1
 rows=[];body_checks=0;once=0;seen=set()
 for ch in report['chapters']:
  c.write(vm.diff+0x1000,ch['chapter']-1,4)
  owned=[]
  for i in range(192):
   p=vm.save+0x25cfc+i*92
   if c.read(p+2,1):
    # Raise the existing party between stages; include a small level spread.
    exp=min(49000,(ch['chapter']+3)*500+(i%3)*500);c.write(p+0xa,exp,2);owned.append(exp)
  expected=sum(owned)//len(owned)
  before=[(c.read(vm.save+0x6efc+i*216,2),bytes(c.mem[vm.save+0x6efc+i*216:vm.save+0x6efc+(i+1)*216])) for i in range(128)]
  spawns,msgs=simulate_block(vm,ch);assert spawns==len(ch['recruits']) and msgs==len(ch['messages'])
  for recruit in ch['recruits']:
   key=recruit['key'];assert key not in seen;seen.add(key)
   slot=c.run(0x244c20,[vm.save,key,0,0]);pilot=c.run(0x244a40,[vm.save,key,1,0]);assert slot>=0 and pilot>=0
   assert c.read(vm.save+0x25cfc+pilot*92+0xa,2)==expected,(recruit['name'],'average EXP')
   grades=[c.run(0x248950,[vm.save,k,slot,0]) for k in [0xd,0xe,0xf,0x10]]
   assert grades==[recruit['initial_upgrade']]*4,(recruit['name'],grades)
   # Fixed-weapon upgrades retain their save-array slots before/after the unlock.
   for progress in [0,35]:
    c.write(vm.diff+0x1000,progress,4)
    for wslot in range(8):
     if c.run(0x2459b0,[vm.save,0x75,slot,wslot])<=0:continue
     ptr=0x17f0000;c.write(ptr,wslot,4);g=c.run(0x248950,[vm.save,0xc,slot,ptr])
     assert g==recruit['initial_upgrade'],(recruit['name'],'weapon grade',wslot,g)
     body_checks+=1
   rows.append(dict(name=recruit['name'],chapter=ch['chapter'],unit_slot=slot,pilot_slot=pilot,experience=expected,body_upgrades=grades))
  # A second event invocation must skip every dialogue, deployment and upgrade.
  snapshot=bytes(c.mem[vm.save:vm.save+0x40000]);spawns,msgs=simulate_block(vm,ch)
  assert (spawns,msgs)==(0,0) and snapshot==bytes(c.mem[vm.save:vm.save+0x40000]);once+=1
 assert len(seen)==25
 # Flags sit in four unused bytes of the saved Diff object, not transient map flags.
 flagbase=vm.diff+0x1248+60
 mask=int.from_bytes(c.mem[flagbase:flagbase+4],'little');assert mask==(1<<len(report['chapters']))-1
 return dict(recruits=rows,all_25_registered=True,second_invocations_skipped=once,weapon_upgrade_checks=body_checks,
             persistent_flag_bytes=hex(flagbase),simulated_deployment='group command intercepted; actual native UNTD constructor executed',
             live_map_pathfinding_tested=False)

def validate(report):
 result={'passed':False,'live_playthrough':False}
 result['equivalent_zero_fill_checks']=test_loops();result['average_experience_edge_cases']=test_average()
 result['master_native_checks'],getters=validate_masters(report);result['pilot_base_getters']=[hex(p) for p in getters]
 result['native_string_and_history_checks']=validate_text(report)
 result['recruitment']=validate_recruitment(report)
 story=json.loads((ROOT/'story_plan_25_v1.json').read_text(encoding='utf8'));actual={r['name']:c['chapter'] for c in report['chapters'] for r in c['recruits']}
 assert all(actual[r['name']]==r['playable'] for r in story['characters'])
 arrivals={name:c['chapter'] for c in report['chapters'] for name in c['arrivals']};assert all(arrivals[r['name']]==r['arrival'] for r in story['characters'])
 result.update(passed=True,chapter_coverage=22,lineup_coverage=25)
 (ROOT/'story_25_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 return result

if __name__=='__main__':
 report=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'));print(json.dumps(validate(report),ensure_ascii=False,indent=2),flush=True)
