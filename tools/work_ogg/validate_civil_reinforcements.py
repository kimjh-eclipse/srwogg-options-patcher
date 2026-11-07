"""Native callback filters, actor lookup and relative-spawn handler checks.

Only map counting/spawn construction and visual completion are fixtures.
The native pilot lookup, coordinate getter, CB coroutine and guards run.
"""
from prepare_civil_reinforcements import *
from validate_options import Profiles,ram
from validate_party_25 import PartyCPU,seed_clones,snapshot
from validate_regional_five import VM,load_campaign_master

class WaveCPU(PartyCPU):
 def ret(self,value):self.put(2,value);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
 def sync(self,ships,turn):
  for i in range(255):self.write(self.actor_base+i*416+0x18,0xffffffff,4)
  self.actor_info={};self.unit_alive={1996:True,**{k:True for k in self.targets}}
  for i,(unit,pilot,pos) in enumerate([(1188,1137,(10+turn,10)),(1215,1209,(26-turn,18)),(1996,1993,(18,24))]):
   if i<2 and unit not in ships:continue
   at=self.actor_base+i*416;self.actor_info[at]=(unit,pilot,pos);self.unit_alive[unit]=True
   for off,val in [(0x10,0x319d40),(0x18,i),(0x1c,0),(0x50,-1),(0x7c,0),(0x28,0),(0x2c,pos[0]),(0x30,pos[1])]:self.write(at+off,val&0xffffffff,4 if off!=0x7c else 1)
 def step(self):
  if self.pc==0x2369d0 and self.r[4] in self.actor_info:
   unit,pilot,pos=self.actor_info[self.r[4]];attr=self.r[5]
   assert attr in [0x12a,0xb5,0x134],hex(attr)
   self.ret((self.r[4]-self.actor_base)//416 if attr==0x12a else (pilot if self.r[6]==0 else 65535) if attr==0xb5 else 1)
  elif self.pc==0x211ef0:self.ret(int(self.unit_alive.get(self.r[5],False)))
  elif self.pc==0x2198c0:
   row=self.r[5];assert 45<=row<63;assert self.r[6]&0xffffffff==0xffffffff and self.r[7]==1 and self.r[10]==0
   coords=(self.r[8]&0xffffffff,self.r[9]&0xffffffff);assert coords in [x[2] for x in self.actor_info.values()]
   self.spawned.append((row,coords));at=0x18d0000;self.write(at+0x18,0,4);self.ret(at)
  elif self.pc==0x4f3430:self.ret(1)
  else:super().step()

def machine(base,master,blob,s,ships,turn,phase=0):
 v=VM(base);v.cpu=WaveCPU(base);v.cpu.r[28]=0x31def0;load_campaign_master(v,master);v.cpu.write(v.ctx+0x2870,0x319d40,4);v.cpu.write(v.ctx+0x74cc,0,2);v.cpu.write(0x46ecec,0,4)
 v.cpu.targets=s['targets'];v.cpu.actor_base=0x319d40+0x32ff0+0x19d50;v.cpu.spawned=[];v.cpu.sync(ships,turn);v.cpu.write(0x319d40+0x154fd8,turn+1,4);v.cpu.write(0x319d40+0x155766,phase,1)
 v.cpu.mem[0x1800000:0x1800000+len(blob)]=blob;v.cpu.run(0x5363c0,[v.ctx,0x1800000]);v.op(command(0xba,0x10071,0,0));return v

def execute(v,blob,start):
 rs=records(blob);i=start;prefix=u32(blob,32)
 for _ in range(len(rs)*2):
  r=rs[i];v.cpu.write(v.ctx+0x48d0,prefix+i,4)
  if r[0] in [0x3e,0x25]:return
  if r[0] in [0x26,0x30,0x7b]:i+=1;continue
  assert r[0] in [0x79,0x93,0x91,0x9a,0x96,0xba,0xcb],hex(r[0])
  result=v.op(r)
  if r[0]==0xcb:
   fn=u32(v.ram,0x572d40+0xcb*12+8)
   assert result==0,(result,r[2:4],v.cpu.spawned,v.cpu.read(v.ctx+0x7538,4))
   for _ in range(4):
    result=v.cpu.run(fn,[v.ctx,v.rec])
    if result==5:break
   assert result==5,'relative-spawn coroutine did not complete'
   i+=1;continue
  if result==13:return
  assert result==10,(hex(r[0]),result);i=v.cpu.read(v.ctx+0x48d0,4)-prefix+1
 raise AssertionError('callback loop')

def main():
 p=json.loads((ROOT/'civil_reinforcements_prepared.json').read_text(encoding='utf8'));civil=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),4095);master=(DEST/'SHARED.BIN.master').read_bytes();cases=0;constructors=0
 with TARGET.open('rb') as f:
  for archive in ['SHARED.BIN','IM.BIN']:
   _,old=rawmaster(f,archive);new=(DEST/(archive+'.master')).read_bytes();expected=bytearray(old.b)
   for j,key in enumerate(KEYS):struct.pack_into('<H',expected,old.tables['UTbl'][0]+12+key*2,u16(old.b,old.tables['UTbl'][0]+12+SOURCES[j%6]*2))
   assert new==expected
  for s in p['scenes']:
   src=next(x for x in civil['scenes'] if x['key']==s['key']);s['targets']=src['targets'];blob=(DEST/s['logo']['file']).read_bytes();units=(DEST/s['untd']['file']).read_bytes();assert u32(units,40)==63
   old=read(f,src['untd']['offset'],src['untd']['size']);assert units[44:44+45*336]==old[44:];assert records(blob)[:s['old_main_rows']]==records(read(f,src['logo']['offset'],src['logo']['size']))
   for ships in [[],[1188],[1215],[1188,1215]]:
    v=machine(base,master,blob,s,ships,1)
    for wave in s['waves']:
     er=command(0x42,27,wave['event_descriptor'],wave['turn'],0)
     for turn in [1,2,3,4,5]:
      v.cpu.sync(ships,turn);v.cpu.write(0x319d40+0x154fd8,turn+1,4)
      # Original native turn-and-side filter; literal turn/phase from event row.
      for j,x in enumerate(er):v.cpu.write(v.rec+j*4,x,4)
      for phase in [0,1,2]:
       v.cpu.write(0x319d40+0x155766,phase,1);mapped=u32(base,0x564370+phase*4);assert v.cpu.run(0x5383e0,[v.ctx,v.rec,0])==int(turn==wave['turn'] and mapped==0);cases+=1
      v.cpu.write(0x319d40+0x155766,0,1)
      before=len(v.cpu.spawned);execute(v,blob,wave['function']);count=len(v.cpu.spawned)-before;assert count==(6 if turn==wave['turn'] else 0),(s['key'],ships,wave['turn'],turn,count)
      if count:
       assert [row for row,xy in v.cpu.spawned[-6:]]==wave['rows']
       wanted=[(10+turn,10),(26-turn,18)] if len(ships)==2 else [(10+turn,10)] if ships==[1188] else [(26-turn,18)] if ships==[1215] else [(18,24)]
       assert [xy for row,xy in v.cpu.spawned[-6:]]==[wanted[i%len(wanted)] for i in range(6)]
       execute(v,blob,wave['function']);assert len(v.cpu.spawned)==before+6;cases+=1
    # Completed objectives/transport loss/predeployment all reject every wave.
    for state in ['won','lost','before_selection','wrong_scene']:
     for wave in s['waves']:
      v=machine(base,master,blob,s,ships,wave['turn'])
      if state=='won':v.cpu.unit_alive.update({k:False for k in s['targets']})
      if state=='lost':v.cpu.unit_alive[1996]=False
      if state=='before_selection':v.op(command(0x7e,0x10071,0,0))
      if state=='wrong_scene':v.cpu.write(v.ctx+0x74cc,2,2)
      execute(v,blob,wave['function']);assert not v.cpu.spawned,(s['key'],state);cases+=1
   for boost in [0,2]:
    v=VM(base);v.cpu=PartyCPU(base);v.cpu.r[28]=0x31def0;load_campaign_master(v,master);owned=seed_clones(v);before=snapshot(v,owned)
    for item in s['spawn']:
     row=bytearray(units[44+item['row']*336:44+(item['row']+1)*336]);struct.pack_into('<II',row,16,10,10)
     for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,item['base_grade']+boost)
     assert v.birth(row)==1;assert snapshot(v,owned)==before;constructors+=1
   print('Validated reinforcement stage',s['key'],flush=True)
 result=dict(passed=True,callback_cases=cases,native_constructor_cases=constructors,turns=[2,3,4],per_wave=6,per_stage_added=18,initial_enemies=32,total_enemies=50,original_native_turn_and_phase_filter_executed=True,native_pilot_lookup_and_coordinate_getter_executed=True,native_CB_three_step_coroutine_executed=True,moving_ship_positions_forwarded=True,both_ships_split_three_each=True,no_ship_falls_back_to_transport=True,once_per_wave=True,old_story_routes_dialogue_roster_and_initial_rows_preserved=True,all_owned_25_records_preserved=True,master_changes_only_18_unit_aliases=True,actual_map_creation_collision_AI_and_renderer_tested=False,ready_to_apply=True)
 (ROOT/'civil_reinforcements_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
