"""Run actual OGG code against the prospective campaign changes."""
from campaign_native_tuning import *
from campaign_bonus_scripts import EARLY,records,loadarc,TARGET,DEAD,NONE,command
from story_vm import VM
from compare_ogs_units import getmaster
from catalog import Master,u16
from apply_balance_25 import get_record
from r5900_scalar_check import CPU
import numpy as np

def resources(target,edits):
 with target.open('rb') as f:
  entries=inventory(f);elf=next(x for x in entries if x['name'].startswith('SLPS_'));mp=next(x for x in entries if x['name']=='MPOL.BIN;1');overlay=read(f,mp['offset'],mp['size'])
 ram=bytearray((OUT/'terrain_fresh_ram.bin').read_bytes())
 ram[0x422000:0x422000+len(overlay)]=overlay
 # Include the already-installed chapter/repaired-weapon hooks in the baseline.
 story=json.loads((ROOT/'story_25_journal.json').read_text(encoding='utf8'))
 import base64,zlib
 for e in story['edits']:
  if elf['offset']<=e['offset']<elf['offset']+elf['size']:
   pc=0x100000+e['offset']-elf['offset']-0x180;b=zlib.decompress(base64.b64decode(e['after_zlib_base64']));ram[pc:pc+len(b)]=b
 patched=bytearray(ram)
 for off,a,b,l in edits:
  if elf['offset']<=off<elf['offset']+elf['size']:pc=0x100000+off-elf['offset']-0x180
  elif mp['offset']<=off<mp['offset']+mp['size']:pc=0x422000+off-mp['offset']
  else:continue
  assert patched[pc:pc+len(a)]==a,(l,hex(pc));patched[pc:pc+len(b)]=b
 return bytes(ram),bytes(patched)

def initializer_checks(rams):
 count=0
 for seed in [0,0x13579bdf,0xffffffff]:
  for start,stop in [(SQ_START,SQ_END),(FLOAT_START,None)]:
   cs=[]
   for ram in rams:
    c=CPU(ram);c.r=[0]+[0xabc000+i for i in range(1,32)];c.fpr=[(seed+i*12347)&0xffffffff for i in range(32)]
    c.r[2]=0x1800000;c.r[3]=0x1000;c.write(0x1f00000+12,0x1000,4);c.writes.clear()
    c.mem[0x1800000:0x1800600]=b'\xa5'*0x600
    if stop:c.run(start,stop=stop)
    else:c.run(start,[0x1800000])
    cs.append(c)
   assert cs[0].r==cs[1].r and cs[0].fpr==cs[1].fpr,(hex(start),'registers')
   stores=[{(a,n) for a,n,pc in c.writes} for c in cs];assert stores[0]==stores[1]
   for a,n in stores[0]:assert cs[0].mem[a:a+n]==cs[1].mem[a:a+n]
   count+=1
 return count

def actor_machines(rams):
 master=getmaster(TARGET);ch=json.loads((ROOT/'story_25_journal.json').read_text(encoding='utf8'))['chapters'];rec=next(c for c in ch if c['chapter']==23)['recruits'][0]
 out=[];obj=0x1800000;stage=0x1400000;settings=0x1840000
 for ram in rams:
  vm=VM();vm.cpu=CPU(ram);c=vm.cpu;c.r[28]=0x31def0;vm.load_master(master.b);assert vm.birth(bytes.fromhex(rec['row_hex']))==1
  for off,val in [(0,vm.diff),(4,vm.save),(0x10,stage),(0x18,0),(0x168,settings)]:c.write(obj+off,val,4)
  for i in range(3):c.write(settings+0x128+i*4,500,4)
  c.write(settings+0x134,0,4)
  idx,_=get_record(master,'Unit','UTbl',rec['key'],100);body=0x1900000+master.tables['Unit'][0]+12+idx*100
  assert c.run(0x2369d0,[obj,0x130,0,0,0])==0
  out.append((vm,obj,stage,settings,body))
 return out

def hostile_checks(rams):
 machines=actor_machines(rams);stats=hp=dispatch=0
 for side in range(6):
  for hostile in [False,True]:
   for vm,obj,stage,settings,body in machines:vm.cpu.write(obj+0x74,side,1);vm.cpu.write(stage+0x15573c+side,int(hostile),1)
   for attr in range(0xd4,0xda):
    a,b=[vm.cpu.run(0x2369d0,[obj,attr,0,0,0]) for vm,obj,stage,settings,body in machines]
    assert b==a+(5 if hostile else 0),(side,hostile,attr,a,b);stats+=1
   for base in [0,1,3700,10000,19999,20000,63000]:
    for upgraded in [0,1000]:
     values=[]
     for vm,obj,stage,settings,body in machines:
      vm.cpu.write(body,base,4);assert vm.cpu.run(0x249300,[vm.save,0x14,0,0])==base
      values.append(vm.cpu.run(0x236890,[obj,base+upgraded]))
     assert values[1]==values[0]+(base//10 if hostile and 0<base<20000 else 0),(side,hostile,base,upgraded,values);hp+=1
 for base in [3700,19999,20000,63000]:
  for hostile in [False,True]:
   values=[]
   for vm,obj,stage,settings,body in machines:
    vm.cpu.write(body,base,4);vm.cpu.write(obj+0x74,2,1);vm.cpu.write(stage+0x15573e,int(hostile),1)
    values.append(vm.cpu.run(0x2369d0,[obj,0x14,0,0,0]))
   assert values[1]==values[0]+(base//10 if hostile and base<20000 else 0),(base,hostile,values);dispatch+=1
 for vm,obj,stage,settings,body in machines:vm.cpu.write(obj+0x10,0,4)
 for attr in range(0xd4,0xda):assert machines[0][0].cpu.run(0x2369d0,[machines[0][1],attr,0,0,0])==machines[1][0].cpu.run(0x2369d0,[machines[1][1],attr,0,0,0])
 return dict(pilot_stat_cases=stats,hp_cases=hp,hp_dispatcher_cases=dispatch,missing_map_cases=6)

def reward_checks(rams):
 B=0x1800000
 class RewardCPU(CPU):
  def step(self):
   pc=self.pc;v=None
   if pc==0x4aa648:self.trace.append((int(self.r[16])-B,int(self.r[17]),int(self.r[3])))
   if pc==0x2369d0:
    attr=self.r[5]&0xffffffff
    values={0x130:1,0x1a2:1,0x1a0:0,0x6d:self.cfg['funds'],0x119:self.cfg.get('funds_extra',0),0x17b:self.cfg.get('luck',0),0xcf:50 if self.cfg.get('ace') else 0,0x10d:0 if self.cfg.get('ace_percent') else -1,0x6f:self.cfg['pp'],0x11b:self.cfg.get('pp_extra',0),0x196:self.cfg.get('training',0),0x1a6:0 if self.cfg.get('map_half') else -1,0x9c:self.cfg.get('map_half',0),0xbe:self.cfg.get('copilot_half',0),0x189:0}
    if attr==0x1b8:v=2 if self.cfg.get('money_skill' if self.r[7]==0x18 else 'full_sub_pp') else 0
    else:assert attr in values,hex(attr);v=values[attr]
   elif pc==0x173f50:v=self.cfg.get('difficulty',2)
   elif pc==0x2700b0:v=self.cfg.get('ace_percent',0)
   elif pc==0x226a00:v=int(self.r[5]>=self.cfg.get('pilots',1))
   if v is not None:self.visits[pc]+=1;self.count+=1;self.put(2,v);self.pc=self.r[31]&0xffffffff;self.pending=None
   else:super().step()
 cs=[RewardCPU(ram) for ram in rams];cases=[]
 for side in [0,1]:
  for value in [0,1,2,5,7,100,65535]:cases.append(dict(side=side,funds=value,pp=min(value,255)))
  for extra in [{'luck':1},{'ace':1},{'money_skill':1},{'ace_percent':17},{'luck':1,'ace':1,'money_skill':1,'ace_percent':23,'training':1},{'training':1},{'map_half':1},{'copilot_half':1},{'participants':4,'pilots':4},{'participants':4,'pilots':4,'training':1,'map_half':1},{'participants':4,'full_sub_pp':1},{'dead':False},{'funds_extra':173,'pp_extra':3}]:cases.append(dict(side=side,funds=1237,pp=7,**extra))
  for mode in [0,1]:cases.append(dict(side=side,funds=531,pp=5,difficulty=mode,ace=True))
 for cfg in cases:
  initial=bytearray(0x3000);struct.pack_into('<I',initial,0,B+0x12a0)
  for group in [0x12a0,0x1920]:
   for i in range(4):struct.pack_into('<i',initial,group+i*0x1a0+0x18,-1)
  allies=0x1920 if cfg['side'] else 0x12a0;targets=0x12a0 if cfg['side'] else 0x1920
  for i in range(cfg.get('participants',1)):struct.pack_into('<i',initial,allies+i*0x1a0+0x18,0)
  if cfg.get('participants',1)==4:
   struct.pack_into('<I',initial,0x1fb4,1)
   for i in [2,3]:initial[(0x950 if cfg['side'] else 0)+i*0x254+0x2d]=1
  struct.pack_into('<i',initial,targets+0x18,0);struct.pack_into('<i',initial,(0 if cfg['side'] else 0x950)+4,0 if cfg.get('dead',True) else 1)
  pp=[(0x950 if cfg['side'] else 0)+i*0x254+0x244+j*4 for i in range(4) for j in range(4)];money=[0x1fec,0x1ff0]
  for p in pp:struct.pack_into('<I',initial,p,11)
  for p in money:struct.pack_into('<I',initial,p,137)
  results=[]
  for c in cs:c.mem[B:B+len(initial)]=initial;c.cfg=cfg;c.trace=[];c.run(REWARD,[B,cfg['side']]);results.append(bytes(c.mem[B:B+len(initial)]))
  a,b=results
  if cfg.get('participants')==4 and cfg.get('pilots')==4:assert all(u32(a,p)>11 for p in pp)
  for p in pp:assert u32(b,p)-11==2*(u32(a,p)-11),(cfg,'PP',p,u32(a,p),u32(b,p),cs[0].trace,cs[1].trace)
  for p in money:assert u32(b,p)-137==(u32(a,p)-137)*6//5,(cfg,'money',p,u32(a,p),u32(b,p))
  a,b=bytearray(a),bytearray(b)
  for p in pp+money:a[p:p+4]=b[p:p+4]
  assert a==b,('other battle state modified',cfg)
 return dict(cases=len(cases),native_reward_arithmetic=True,property_inputs='controlled fixtures',full_battle_property_integration=False,rounding='floor',minimum_PP_doubled=True)

def grants_checks(hidden):
 vm=VM();c=vm.cpu;vm.load_master(getmaster(TARGET).b)
 def quantity(op,key):
  if op==0x60:return c.read(vm.diff+0x10c8+key,1)
  return sum(c.read(vm.save+0x21efc+i*4,2)==key for i in range(0x3e00//4))
 logo=(OUT/'bonus_2003.logo').read_bytes();rs=records(logo)
 start=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,63,7])
 end=next(i for i in range(start,len(rs)) if rs[i][0]==0xba and rs[i][2:5]==[0x100c1,63,7])+1
 def block():
  i=start;grants=0
  while i<end:
   r=rs[i];c.write(vm.ctx+0x48d0,i,4)
   if r[0]!=0x30:
    assert r[0] in [0x93,0x91,0xba,0x60,0x64];assert vm.op(r)==10
    grants+=r[0] in [0x60,0x64]
   i=c.read(vm.ctx+0x48d0,4)+1
  return grants
 before={(op,k):quantity(op,k) for op,k,n in EARLY};assert block()==8
 for op,key,name in EARLY:assert quantity(op,key)==before[op,key]+1,(name,quantity(op,key))
 snapshot=(bytes(c.mem[vm.save:vm.save+0x40000]),bytes(c.mem[vm.diff:vm.diff+0x1300]))
 assert block()==0
 assert snapshot==(bytes(c.mem[vm.save:vm.save+0x40000]),bytes(c.mem[vm.diff:vm.diff+0x1300]))
 assert vm.op(command(0x5f,1410,NONE,NONE,NONE))==10
 slot=c.run(0x244c20,[vm.save,1410,0,0]);assert slot>=0
 snapshot=bytes(c.mem[vm.save:vm.save+0x40000]);assert vm.op(command(0x5f,1410,NONE,NONE,NONE))==10
 assert snapshot==bytes(c.mem[vm.save:vm.save+0x40000])
 # The later native rewards remain additional to the explicitly requested early copies.
 for op,key in [(0x60,31),(0x64,3513),(0x60,32),(0x64,3530),(0x60,33)]:
  old=quantity(op,key);assert vm.op(command(0x8a))==10;assert vm.op(command(op,key,0))==10
  assert quantity(op,key)==old+1
 return dict(early_each_one=True,early_repeat_grants=0,mironga_slot=slot,mironga_repeat_does_not_duplicate=True,natural_rewards_additional_to_early_copies=True)

def spawn_checks(rams):
 with TARGET.open('rb') as f:
  _,es=loadarc(f,13);_,p,n=next(x for x in es if 2001 in x[0]);b=read(f,p,n)
 template=next(b[44+i*336:44+(i+1)*336] for i in range(u32(b,40)) if u32(b,44+i*336+8)==2)
 m=getmaster(TARGET);count=0
 for difficulty in range(3):
  for side in range(6):
   for base in [0,5,14,15]:
    results=[]
    for which,ram in enumerate(rams):
     vm=VM();vm.cpu=CPU(ram);c=vm.cpu;c.r[28]=0x31def0;vm.load_master(m.b)
     row=bytearray(template);struct.pack_into('<I',row,8,side)
     grade=min(base+(2 if which and side in [2,3,4] else 0),15)
     for off in range(0x38,0x50,4):struct.pack_into('<I',row,off,grade)
     c.write(vm.diff+0xff4,difficulty,4);assert vm.birth(row)==1
     slot=c.run(0x244c20,[vm.save,u32(row),0,0]);assert slot>=0
     body=[c.run(0x248950,[vm.save,prop,slot,0]) for prop in range(0xd,0x11)]
     ptr=0x17f0000;c.write(ptr,0,4);weapon=c.run(0x248950,[vm.save,0xc,slot,ptr])
     results.append((body,weapon))
    add=2 if side in [2,3,4] else 0
    assert results[1][0]==[min(x+add,15) for x in results[0][0]],(difficulty,side,base,results)
    assert results[1][1]==min(results[0][1]+add,15),(difficulty,side,base,results)
    count+=1
 return dict(native_spawn_cases=count,difficulties=3,factions=6,cap=15,non_enemy_grades_unchanged=True)

def weapon_checks(edits,notes):
 ram=(OUT/'terrain_fresh_ram.bin').read_bytes()
 funcs={'power':0x274ff0,'en':0x274cf0,'morale':0x274c70,'barrier':0x273da0,'all':0x273fd0,'cost':0x2748a0,'growth':0x274810,'motion':0x273b10}
 assert u32(ram,0x274d60)==0x9042001a and u32(ram,0x274ce0)==0x9042001b
 assert u32(ram,0x273e04)==0x90420015 and u32(ram,0x274034)==0x90420014
 for name,sh,shr in [('barrier',26,30),('all',24,31),('growth',26,29)]:
  values=[u32(ram,p) for p in range(funcs[name]+0x60,funcs[name]+0x94,4)]
  assert ((2<<16)|(2<<11)|(sh<<6)|60) in values and ((2<<16)|(2<<11)|(shr<<6)|62) in values
 count=0
 with TARGET.open('rb') as f:
  for ar in ['SHARED.BIN','IM.BIN']:
   e=json.loads((OUT/(ar+'.3.json')).read_text())['entries'][0];raw=read(f,e['offset'],e['size']);b=bytearray(raw)
   for off,a,n,l in edits:
    if e['offset']<=off<e['offset']+e['size']:assert b[off-e['offset']:off-e['offset']+len(a)]==a;b[off-e['offset']:off-e['offset']+len(n)]=n
   m=Master(b);original=Master(raw)
   for tag in ['Unit','Plot']:
    p,size,_=m.tables[tag];assert b[p:p+size]==raw[p:p+size]
   vm=VM();vm.load_master(b);c=vm.cpu
   for n in notes['weapons']:
    key=n['key'];_,wr=get_record(m,'Weap','WTbl',key,36);_,oldwr=get_record(original,'Weap','WTbl',key,36)
    expected={'power':u16(wr,8),'en':wr[0x1a],'morale':wr[0x1b],'barrier':(wr[0x15]>>4)&3,'all':int(bool(wr[0x14]&0x80)),'cost':wr[3]&7,'growth':(wr[3]>>3)&7}
    for name,want in expected.items():assert c.run(funcs[name],[vm.master,key])==want,(ar,name,key,want);count+=1
    assert wr[:2]==oldwr[:2] and wr[0x21]==oldwr[0x21];count+=1
   # All 25 custom clones and their 83 independent balanced weapons remain byte-identical.
   for key in range(0xe00,0xe53):assert get_record(m,'Weap','WTbl',key,36)==get_record(original,'Weap','WTbl',key,36)
 return dict(native_weapon_checks=count,functions={k:hex(v) for k,v in funcs.items()},unit_and_pilot_masters_preserved=True,additional_25_unit_balance_preserved=True)

def script_text_checks(hidden):
 vm=VM();c=vm.cpu;ctx=vm.ctx;base=0x1800000;checks=0
 for key,messages in [(2003,hidden['early_block']['messages']),(2054,hidden['space_messages'])]:
  b=(OUT/f'bonus_{key}.logo').read_bytes();c.mem[base:base+len(b)]=b;c.run(0x5363c0,[ctx,base])
  for msg in messages:
   raw=bytes.fromhex(msg['encoded']);c.run(0x53ad00,[ctx,0,msg['string_id']]);assert bytes(c.mem[ctx+0x6c00:ctx+0x6c00+len(raw)])==raw
   c.run(0x53a1f0,[ctx,msg['label'],0,0,0],stop=0x53a244);idx=c.r[4]&0xffffffff;p=u32(b,36)+idx*96
   assert u32(b,p)==0x30 and u32(b,p+4)==msg['label'] and u32(b,p+8)==msg['string_id'];checks+=2
 return checks

if __name__=='__main__':
 edits,note=native_plan(TARGET);rams=resources(TARGET,edits)
 print('initializers',initializer_checks(rams),flush=True)
 print('hostile',hostile_checks(rams),flush=True)
 print('rewards',reward_checks(rams),flush=True)
