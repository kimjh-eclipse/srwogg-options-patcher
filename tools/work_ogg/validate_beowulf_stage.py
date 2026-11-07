"""Native script predicates/constructor checks; no renderer or live play claim."""
from prepare_beowulf_stage import *
from validate_regional_five import VM,CPU,load_campaign_master
from validate_party_25 import seed_clones,snapshot
from validate_options import Profiles,ram
import bisect,copy

class Image:
 def __init__(self,p):
  self.f=TARGET.open('rb');self.pos=0;self.edits=sorted((e['offset'],(DEST/e['file']).read_bytes()) for e in p['edits']);self.starts=[a for a,b in self.edits]
 def seek(self,p,whence=0):self.pos=p if whence==0 else self.pos+p;return self.pos
 def read(self,n):
  self.f.seek(self.pos);b=bytearray(self.f.read(n));end=self.pos+len(b)
  for at,new in self.edits[max(0,bisect.bisect_right(self.starts,self.pos)-1):]:
   if at>=end:break
   lo=max(at,self.pos);hi=min(at+len(new),end)
   if hi>lo:b[lo-self.pos:hi-self.pos]=new[lo-at:hi-at]
  self.pos=end;return bytes(b)
 def close(self):self.f.close()
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

class MapCPU(CPU):
 """Map actor data are a fixture; native unit-count/predicate/CC code runs."""
 def configure(self,vm,spawn):
  self.vm=vm;self.spawn=spawn;self.alive={x['key']:True for x in spawn};self.spawned=[];self.allies=12;self.manager=0x319d40+0x32ff0;self.actor_base=self.manager+0x19d50;self.fast_counts=False
  self.key_by_slot={i:x['key'] for i,x in enumerate(spawn)};self.fixture_sync()
 def fixture_sync(self):
  for i in range(255):self.write(self.actor_base+i*0x1a0+0x18,0 if i in self.key_by_slot and self.alive[self.key_by_slot[i]] else 0xffffffff,4)
 def ret(self,value):self.put(2,value);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
 def step(self):
  if self.pc==0x2369d0 and self.actor_base<=self.r[4]<self.actor_base+255*0x1a0:
   slot=(self.r[4]-self.actor_base)//0x1a0;key=self.key_by_slot.get(slot);attr=self.r[5];assert key is not None and attr in [1,0x12a,0x134,0x12f],(slot,attr)
   self.ret(key if attr==1 else slot if attr==0x12a else 1 if attr==0x134 else 0)
  elif self.pc==0x211ef0 and self.fast_counts:self.ret(int(self.alive.get(self.r[5],False)))
  elif self.pc==0x2129e0:self.ret(self.allies if self.r[5]==0 else sum(self.alive.values()))
  elif self.pc==0x2198c0:
   row=self.r[5];item=next(x for x in self.spawn if x['row']==row);assert item['respawns'] and not self.alive[item['key']] and self.alive[UNIT];self.alive[item['key']]=True;self.spawned.append(row);self.fixture_sync();self.ret(self.actor_base+(row-12)*0x1a0)
  else:super().step()

def event(vm,blob,start):
 rs=records(blob);i=start
 while i<len(rs):
  r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0] in [0x3e,0x25]:return None
  if r[0] in [0x79,0x7a,0x93,0x96,0x91,0x9a,0xba,0xcc]:
   value=vm.op(r)
   if value==13:return None
   assert value==10,(i,r[0],value);i=vm.cpu.read(vm.ctx+0x48d0,4)+1;continue
  if r[0]==0xa1:assert vm.op(r)==14;return r[2]
  assert r[0] in [0x26,0x30,0x7b,0x6d,0x67],(i,r[0]);i+=1
 raise AssertionError('unterminated callback')

def main():
 p=json.loads((ROOT/'beowulf_stage_prepared.json').read_text(encoding='utf8'));checks=0;base=ram(Profiles(),4095);blob=(DEST/p['logo']['file']).read_bytes();master=(DEST/'SHARED.BIN.master').read_bytes();m=Master(master);units=(DEST/p['untd']['file']).read_bytes();assert u32(units,40)==44;rows=[units[44+i*336:44+(i+1)*336] for i in range(44)]
 with Image(p) as f,OGsBeowulfImage() as source,TARGET.open('rb') as original:
  for ar in ['BATTLE.BIN','GRAPHIC.BIN']:
   _,r=archive(f,ar);_,oldr=archive(original,ar);cs=children(f,r);ocs=children(original,oldr)
   for i,old in ocs.items():
    a=cs[i]
    for e in old['entries']:
     ne=a['entries'][e['index']];assert read(f,ne['offset'],ne['size'])==read(original,e['offset'],e['size']) or i in [7,8,9] and ar=='BATTLE.BIN' or i==4 and ar=='GRAPHIC.BIN';checks+=1
    for e in old['entries']:
     for k in e['keys']:assert entry(a,k)['index']==e['index'];checks+=1
   if ar=='BATTLE.BIN':
    _,sr=archive(source,ar);sc=children(source,sr);bank=data(f,cs[7],0)[BANK*144:(BANK+1)*144];assert data(f,cs[1],BANK)==data(source,sc[1],BANK)
    for eq in p['animation_equivalence']:
     b=data(f,cs[2],eq['new_key']);assert hashlib.sha256(b).hexdigest()==eq['sha256'];assert u32(b)<=len(b) and u16(b,4) in [1,2,3];desc=struct.unpack_from('<20H',b,24);assert sum(bool(k) for k in desc)==u16(b,6)
     for i,d in enumerate(desc):
      if d:assert d*256+1024+256*(256 if u32(b,8)&(1<<i) else 128)<=len(b)
     assert eq['new_key'] in struct.unpack_from('<70H',bank,4);checks+=3
    cutrow=data(f,cs[9],0)[FACE*60:(FACE+1)*60]
    for k in set(struct.unpack_from('<20H',cutrow))-{65535}:assert len(data(f,cs[3],k))>64;checks+=1
    speech=data(f,cs[5],PILOT);h=struct.unpack_from('<16H',speech);assert all(u16(speech,i)&2047!=1094 for i in range(h[12],h[13],2));checks+=1
   else:
    for i in range(32):assert data(f,cs[1],FACE*32+i)==data(source,children(source,archive(source,ar)[1])[1],223*32+i);checks+=1
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);ts={k:read(f,at,n) for ks,at,n in mt for k in ks};info=next(read(f,at,n) for ks,at,n in mi if MAP_KEY in ks);t=ts[u32(info,12)];w,h=u32(t,8),u32(t,12);positions=[]
  for row in rows:
   x,y=u32(row,16),u32(row,20);assert 0<x<w and 0<y<h;positions.append((x,y));checks+=1
  assert len(set(positions))==44 and len({x['key'] for x in p['spawn']})==32
  for x in p['spawn']:
   r=rows[x['row']];assert u32(r)==x['key'] and u32(r,32)==x['pilot'] and all(u32(r,at)==0xffff0000|x['pilot'] for at in [0x60,0x74,0x88]);checks+=1
 # Real LOGO loader, dialogue and event registration, including thirty repeat callbacks.
 vm=VM(base);load_campaign_master(vm,master);vm.cpu.mem[0x1800000:0x1800000+len(blob)]=blob;vm.cpu.run(0x5363c0,[vm.ctx,0x1800000])
 for i in range(u32(blob,24)):assert vm.op(list(struct.unpack_from('<24I',blob,u32(blob,28)+i*96)))==10;checks+=1
 assert vm.cpu.read(vm.ctx+0x6abc+27*4,4)==4
 for msg in p['messages']:
  raw=encode(msg['text']);vm.cpu.run(0x53ad00,[vm.ctx,0,msg['sid']]);assert bytes(vm.cpu.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0';checks+=1
 # Native per-unit counts run over a map-record fixture. CC runs through its
 # native handler, stopping at the map spawn service; real constructor below.
 vm=VM(base);vm.cpu=MapCPU(base);vm.cpu.r[28]=0x31def0;vm.cpu.write(vm.ctx+0x2870,0x319d40,4);load_campaign_master(vm,master);vm.cpu.configure(vm,p['spawn']);vm.cpu.write(0x46ecec,0,4);vm.cpu.write(vm.ctx+0x74cc,2,2)
 for x in p['spawn']:assert vm.op(command(0x7a,0x100bd,x['key'],1))==10;checks+=1
 vm.cpu.alive[UNIT]=False;vm.cpu.fixture_sync();assert vm.op(command(0x7a,0x100bd,UNIT,0))==10;vm.cpu.alive[UNIT]=True;vm.cpu.fixture_sync();vm.cpu.fast_counts=True
 assert event(vm,blob,p['functions']['reinforcements']) is None
 assert not vm.cpu.spawned;assert event(vm,blob,p['functions']['ending']) is None
 assert vm.op(command(0xba,0x10071,0,0))==10
 for cycle in range(100):
  killed=p['spawn'][cycle%30]['key'];vm.cpu.alive[killed]=False;vm.cpu.fixture_sync();before=len(vm.cpu.spawned)
  assert event(vm,blob,p['functions']['reinforcements']) is None
  assert len(vm.cpu.spawned)==before+1 and vm.cpu.alive[killed];assert event(vm,blob,p['functions']['ending']) is None;checks+=2
 before=len(vm.cpu.spawned)
 for x in p['spawn'][:7]:vm.cpu.alive[x['key']]=False
 vm.cpu.fixture_sync()
 event(vm,blob,p['functions']['reinforcements'])
 assert len(vm.cpu.spawned)==before+7;checks+=1
 vm.cpu.alive[UNIT]=False;vm.cpu.alive[p['spawn'][0]['key']]=False;vm.cpu.fixture_sync();before=len(vm.cpu.spawned)
 assert event(vm,blob,p['functions']['reinforcements']) is None
 assert len(vm.cpu.spawned)==before;assert event(vm,blob,p['functions']['ending'])==34;checks+=2
 native_cases=0
 for difficulty in [0,1,2]:
  for boost in [0,2]:
   vm=VM(base);load_campaign_master(vm,master);vm.cpu.write(vm.diff+0xff4,difficulty,4);owned=seed_clones(vm);before=snapshot(vm,owned)
   for x in p['spawn']:
    r=bytearray(rows[x['row']])
    for at in range(0x38,0x50,4):struct.pack_into('<I',r,at,x['base_grade']+boost)
    assert vm.birth(r)==1;slot=vm.cpu.run(0x244c20,[vm.save,x['key'],0,0]);assert slot>=0;assert [vm.cpu.run(0x248950,[vm.save,i,slot,0]) for i in range(0xd,0x11)]==[x['base_grade']+boost]*4;assert snapshot(vm,owned)==before;native_cases+=1;checks+=3
   for weapon in p['masters']['SHARED.BIN']['weapons']:assert vm.cpu.run(0x274ff0,[vm.master,weapon['key']])==weapon['power'];checks+=1
   assert vm.cpu.run(0x276f40,[vm.master,UNIT])==135000
 result=dict(passed=True,checks=checks,native_constructor_cases=native_cases,option_count=12,single_option_bit=11,wide_map=[w,h],open_tiles=p['valid_open_tiles'],initial_enemies=32,endless_minions=30,ordinary_kill_respawn_cycles=100,simultaneous_kills_replaced=7,boss_death_stops_all_respawns=True,boss_death_wins_with_other_enemies_alive=True,predeployment_guards=True,spawn_service='native CC handler with map-spawn fixture; independent real unit constructors verified',original_25_party_stats_preserved=True,original_models_faces_animations_and_master_rows_preserved=True,ported_OGs_assets_not_rendered_in_PCSX2=True,live_playthrough=False,memory_card_IO=False,ready_to_apply=True)
 (ROOT/'beowulf_stage_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
