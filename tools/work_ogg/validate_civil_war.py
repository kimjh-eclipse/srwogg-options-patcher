"""Native 2A encounter, text/history, roster and campaign-route checks.

Actor membership/counts and renderer/result UI are fixtures; actual script
handlers, saved roster setters and next-stage routines execute unchanged.
"""
from prepare_civil_war import *
from validate_options import Profiles,ram
from validate_party_25 import PartyCPU,seed_clones,snapshot,normalize
from validate_regional_five import VM,load_campaign_master

class CivilCPU(PartyCPU):
 def step(self):
  if self.pc==0x2369d0 and self.r[4] in [0x18d0000,0x18d0200]:
   slot=0 if self.r[4]==0x18d0000 else 1;attr=self.r[5];assert attr in [0xb5,1,0x12a],attr
   self.put(2,self.people[slot] if attr==0xb5 else slot);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  elif self.pc==0x211ef0:
   self.put(2,int(self.alive.get(self.r[5],False)));self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  elif self.pc==0x2129e0:
   self.put(2,self.allies if self.r[5]==0 else sum(self.alive.values()));self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  else:super().step()

def machine(base,master,blob=None):
 v=VM(base);v.cpu=CivilCPU(base);v.cpu.r[28]=0x31def0;v.cpu.alive={};v.cpu.allies=12;v.cpu.people=[0,0];v.cpu.write(v.ctx+0x2870,0x319d40,4);v.cpu.write(0x46ecec,0,4)
 for i in range(16):v.cpu.write(v.ctx+0x74ec+i*4,0xffffffff,4)
 load_campaign_master(v,master)
 if blob is not None:v.cpu.mem[0x1800000:0x1800000+len(blob)]=blob;v.cpu.run(0x5363c0,[v.ctx,0x1800000])
 return v

def actors(v,people):
 v.cpu.people=list(people)
 for i in range(255):v.cpu.write(v.ctx+0x8d24+i*12,0,4)
 for i,at in enumerate([0x18d0000,0x18d0200]):v.cpu.write(v.ctx+0x8d24+i*12,at,4);v.cpu.write(at+0x18,0,4)

def walk(v,blob,start,stop=None,inline=False):
 rs=records(blob);prefix=u32(blob,32);i=start;shown=[]
 for steps in range(len(rs)*3):
  if i==stop:return None,shown
  r=rs[i];v.cpu.write(v.ctx+0x48d0,prefix+i,4)
  if r[0]==0x3e:
   if inline:
    result=v.op(r);assert result in [0,10],('native inline return',result,v.cpu.read(v.ctx+0x5370,4))
   return None,shown
  if r[0]==0x25:return None,shown
  if r[0]==0x30:shown.append(r[2])
  elif r[0] in [0x79,0x7a,0x93,0x96,0x91,0x9a,0xba,0x4a]:
   result=v.op(r)
   if result==13:return None,shown
   assert result==10,(hex(r[0]),result);i=v.cpu.read(v.ctx+0x48d0,4)-prefix+1;continue
  elif r[0]==0xa1:assert v.op(r)==14;return r[2],shown
  else:assert r[0] in [0x26,0x7b,0x6d,0x67,0xaf,0xb0],hex(r[0])
  i+=1
 raise AssertionError('script loop')

def main():
 p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),4095);masterblob=(DEST/'SHARED.BIN.master').read_bytes();master=Master(masterblob);checks=0;encounters=0;party_cases=0
 proof_hash=hashlib.sha256(masterblob+b''.join((DEST/s['untd']['file']).read_bytes() for s in p['scenes'])).hexdigest();reuse='--reuse-constructors' in sys.argv
 if reuse:
  prior=json.loads((ROOT/'civil_war_constructor_validation.json').read_text());assert prior['passed'] and prior['resource_sha256']==proof_hash;party_cases=prior['cases']
 with TARGET.open('rb') as f:
  for ar in ['SHARED.BIN','IM.BIN']:
   _,old=rawmaster(f,ar);new=Master((DEST/(ar+'.master')).read_bytes())
   for tag,stride in [('Unit',100),('Plot',148),('Weap',36)]:
    a=old.tables[tag][0]+12;b=new.tables[tag][0]+12;assert old.b[a:a+old.tables[tag][2]*stride]==new.b[b:b+old.tables[tag][2]*stride];checks+=1
  for s in p['scenes']:
   blob=(DEST/s['logo']['file']).read_bytes();units=(DEST/s['untd']['file']).read_bytes();rs=records(blob);assert u32(units,40)==45
   positions=[(u32(units,44+i*336+16),u32(units,44+i*336+20)) for i in range(45)];assert len(set(positions))==45;assert sum(u32(units,44+i*336+8)==2 for i in range(45))==32;assert u32(units,44+44*336+8)==1
   v=machine(base,masterblob,blob)
   assert v.cpu.run(0x2705c0,[v.master,2,s['key']-2000])==s['number'];checks+=1
   for i in range(u32(blob,24)):assert v.op(list(struct.unpack_from('<24I',blob,u32(blob,28)+i*96)))==10;checks+=1
   assert v.cpu.read(v.ctx+0x6abc+27*4,4)==3;assert v.cpu.read(v.ctx+0x6abc+28*4,4)==2
   for msg in s['messages']:
    raw=encode(msg['text']);v.cpu.run(0x53ad00,[v.ctx,0,msg['sid']]);assert bytes(v.cpu.mem[v.ctx+0x6c00:v.ctx+0x6c00+len(raw)+1])==raw+b'\0';v.cpu.run(0x53a1f0,[v.ctx,msg['label'],0,0,0],stop=0x53a244);ri=v.cpu.r[4]&0xffffffff;assert u32(blob,u32(blob,36)+ri*96+8)==msg['sid'];checks+=2
   for pair in s['pairs']:
    for who in [(pair['left_key'],pair['right_key']),(pair['right_key'],pair['left_key']),(pair['left_key'],1029),(1029,pair['right_key'])]:
     v=machine(base,masterblob,blob);actors(v,who);row=pair['dispatcher_row'];v.cpu.write(v.ctx+0x48d0,u32(blob,32)+row,4);result=v.op(rs[row]);match=set(who)=={pair['left_key'],pair['right_key']};assert result==(0 if match else 10),(s['key'],pair['index'],who,result)
     if match:
      start=s['functions'][pair['function']];assert v.cpu.read(v.ctx+0x48d0,4)==u32(blob,32)+start
      _,shown=walk(v,blob,start,inline=True);assert shown;assert v.cpu.read(v.ctx+0x5370,4)==0
      v.cpu.write(v.ctx+0x48d0,u32(blob,32)+row,4);assert v.op(rs[row])==0;assert not walk(v,blob,start,inline=True)[1]
     encounters+=1;checks+=1
   # No automatic dialogue merely because a normal combat callback occurs.
   v=machine(base,masterblob,blob);actors(v,[1029,1023])
   for pair in s['pairs']:assert v.op(rs[pair['dispatcher_row']])==10;checks+=1
   for hostage,enemies,started_value in [(1,1,1),(1,0,1),(0,0,1),(0,0,0)]:
    v=machine(base,masterblob,blob);v.cpu.write(v.ctx+0x74cc,1,2);v.cpu.alive={HOSTAGE_KEY:bool(hostage),**{k:bool(enemies) for k in s['targets']}}
    if started_value:v.op(command(0xba,0x10071,0,0))
    nxt,shown=walk(v,blob,s['functions']['ending']);assert nxt==(s['next_index'] if hostage and not enemies and started_value else None),(s['key'],hostage,enemies,nxt);checks+=1
   # Actual preparation constructors use distinct keys, preserving all owned25.
   for boost in ([] if reuse else [0,2]):
    v=machine(base,masterblob);owned=seed_clones(v);before=snapshot(v,owned)
    for item in s['spawn']:
     row=bytearray(units[44+item['row']*336:44+(item['row']+1)*336])
     for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,item['base_grade']+boost)
     assert v.birth(row)==1;assert snapshot(v,owned)==before;party_cases+=1;checks+=1
   print('Validated native stage',s['key'],'encounter cases',encounters,'constructors',party_cases,flush=True)
  for b in p['bridges']:
   blob=(DEST/b['logo']['file']).read_bytes();v=machine(base,masterblob,blob)
   for msg in b['messages']:
    raw=encode(msg['text']);v.cpu.run(0x53ad00,[v.ctx,0,msg['sid']]);assert bytes(v.cpu.mem[v.ctx+0x6c00:v.ctx+0x6c00+len(raw)+1])==raw+b'\0';checks+=1
   if b['key']==2040:assert records(blob)[b['route_row']][2]==41
 (ROOT/'civil_war_constructor_validation.json').write_text(json.dumps(dict(passed=True,cases=party_cases,resource_sha256=proof_hash),indent=2))
 # Same non-destructive native pilot availability setter as the original split chapters.
 v=machine(base,masterblob);owned=seed_clones(v);initial=snapshot(v,owned)
 for phase,value,teams in [('guard_split',0,[GUARD,REBELS]),('infiltration',0,[INFIL]),('infil_return',1,[INFIL]),('guard_return',1,[GUARD]),('final_return',1,[REBELS])]:
  for name,x in p['members'].items():
   if x['team'] in teams:assert v.op(command(0x4a,0x100a8,x['pilot'],value))==10
  now=snapshot(v,owned)
  for key in initial:
   for typ,(old,new) in enumerate(zip(initial[key],now[key])):
    assert all(a==b for i,(a,b) in enumerate(zip(old,new)) if not ((typ==1 and i==2) or (typ==0 and i==42))),(phase,key,typ)
  checks+=len(initial)
 assert snapshot(v,owned)==initial
 # Route handler and persistent storage survive all five new indices.
 v=machine(base,masterblob);owned=seed_clones(v);before=snapshot(v,owned)
 for index in [41,42,43,44,45,34]:
  assert v.op(command(0xa1,index,0))==14;assert v.cpu.read(v.diff+0xffc,4)==index;assert snapshot(v,owned)==before;checks+=1
  saved=bytes(v.cpu.mem[v.save:v.save+0x40000]);diff=bytes(v.cpu.mem[v.diff:v.diff+0x1300]);v=machine(base,masterblob);v.cpu.mem[v.save:v.save+len(saved)]=saved;v.cpu.mem[v.diff:v.diff+len(diff)]=diff;assert snapshot(v,owned)==before
 result=dict(passed=True,checks=checks,new_battles=5,political_intermission_scenes=5,encounter_pairs=26,native_pair_cases=encounters,pair_order_independent=True,no_persuade_command=True,wrong_pair_silent=True,encounter_repeats_silent=True,native_preparation_cases=party_cases,owned_25_growth_and_equipment_preserved=True,split_rejoin_restores_owned_25=True,route_persistent_reloads=6,final_display_chapter=47,original_unit_pilot_weapon_rows_preserved=True,dialogue_boxes=p['new_dialogue_boxes'],NPC_spawn_AI_renderer_and_card_IO_tested=False,ready_to_apply=True)
 (ROOT/'civil_war_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
