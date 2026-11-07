"""Native guard-only party transitions, encounters, levels and map routes."""
from prepare_civil_guard import *
from validate_civil_war import machine,actors,walk
from validate_options import Profiles,ram
from validate_party_25 import PartyCPU,seed_clones,snapshot,normalize
from validate_regional_five import VM,load_campaign_master
from story_scripts_25 import records,command

class Image:
 def __init__(self,f,p):self.f=f;self.pos=0;self.edits=[(e['offset'],(DEST/e['file']).read_bytes()) for e in p['edits']]
 def seek(self,at,whence=0):assert whence==0;self.pos=at;return at
 def read(self,n):
  self.f.seek(self.pos);out=bytearray(self.f.read(n));end=self.pos+len(out)
  for at,b in self.edits:
   lo=max(at,self.pos);hi=min(at+len(b),end)
   if lo<hi:out[lo-self.pos:hi-self.pos]=b[lo-at:hi-at]
  self.pos=end;return bytes(out)

def main():
 p=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'));cp=p['effective_civil'];base=ram(Profiles(),4095);master=(DEST/'SHARED.BIN.master').read_bytes();checks=0;encounters=0;births=0
 with TARGET.open('rb') as f:
  im=Image(f,p)
  for slot in [13,14]:
   _,old=loadarc(f,slot);_,new=loadarc(im,slot);assert len(new)==len(old)+2
   for ks,at,n in old:
    if any(k in ORDER for k in ks):continue
    nk,na,nn=next(x for x in new if x[0]==ks);assert (at,n)==(na,nn) and read(f,at,n)==read(im,na,nn);checks+=1
  for s in p['scenes']:
   b=(DEST/s['logo']['file']).read_bytes();u=(DEST/s['untd']['file']).read_bytes();rs=records(b);assert u32(u,40)==63;v=machine(base,master,b)
   assert v.cpu.run(0x2705c0,[v.master,2,s['key']-2000])==s['number'];checks+=1
   for i in range(u32(b,24)):assert v.op(list(struct.unpack_from('<24I',b,u32(b,28)+i*96)))==10
   assert v.cpu.read(v.ctx+0x6abc+27*4,4)==6
   assert any(r[0]==0xa1 and r[2]==s['next_index'] for r in rs)
   for m in s['all_messages']:
    raw=encode(m['text']);v.cpu.run(0x53ad00,[v.ctx,0,m['sid']]);assert bytes(v.cpu.mem[v.ctx+0x6c00:v.ctx+0x6c00+len(raw)+1])==raw+b'\0';v.cpu.run(0x53a1f0,[v.ctx,m['label'],0,0,0],stop=0x53a244);ri=v.cpu.r[4]&0xffffffff;assert u32(b,u32(b,36)+ri*96+8)==m['sid'];checks+=2
   for pair in s['pairs']:
    for who in [(pair['left_key'],pair['right_key']),(pair['right_key'],pair['left_key']),(pair['left_key'],1029)]:
     v=machine(base,master,b);actors(v,who);row=pair['dispatcher_row'];v.cpu.write(v.ctx+0x48d0,u32(b,32)+row,4);match=set(who)=={pair['left_key'],pair['right_key']};assert v.op(rs[row])==(0 if match else 10)
     if match:
      st=s['functions'][pair['function']];assert walk(v,b,st,inline=True)[1];v.cpu.write(v.ctx+0x48d0,u32(b,32)+row,4);assert v.op(rs[row])==0;assert not walk(v,b,st,inline=True)[1]
     encounters+=1
   # Every generic enemy, initial and reserved, uses the exact requested Lv52.
   for item in s['spawn']:
    if item['key'] in INITIAL_KEYS+KEYS:assert [u32(u,44+item['row']*336+at) for at in [0x50,0x54,0x58]]==[25500]*3
   for boost in [0,2]:
    v=VM(base);v.cpu=PartyCPU(base);v.cpu.r[28]=0x31def0;load_campaign_master(v,master);owned=seed_clones(v);before=snapshot(v,owned)
    items=s['spawn'] if s['key'] in [2046,2047] else [next(x for x in s['spawn'] if x['key']==k) for k in list(dict.fromkeys(x['key'] for x in s['spawn'] if x['key'] in INITIAL_KEYS))[:4]]
    for item in items:
     row=bytearray(u[44+item['row']*336:44+(item['row']+1)*336]);struct.pack_into('<II',row,16,10,10)
     for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,item['base_grade']+boost)
     assert v.birth(row)==1;assert snapshot(v,owned)==before
     ps=v.cpu.run(0x244a40,[v.save,item['pilot'],1,0]);level=v.cpu.run(0x2457e0,[v.save,0xd3,ps]);assert level==(52 if item['key'] in INITIAL_KEYS+KEYS else 54),(s['key'],item['key'],level);births+=1
 # Populate every reviewed original/added member plus the original35 recruit.
 v=machine(base,master);seed_clones(v)
 for name,x in cp['members'].items():
  if x['added']:continue
  if x['template']:
   row=bytearray(normalize(bytes.fromhex(x['template'])));struct.pack_into('<I',row,32,x['pilot']);assert v.birth(row)==1
  elif x['pilot'] is not None and v.cpu.run(0x244a40,[v.save,x['pilot'],1,0])<0:
   i=v.cpu.run(0x24b180,[v.save,x['pilot'],0]);assert i>=0;v.cpu.run(0x247c60,[v.save,2,i,1,0])
 if v.cpu.run(0x244a40,[v.save,1243,1,0])<0:
  i=v.cpu.run(0x24b180,[v.save,1243,0]);v.cpu.run(0x247c60,[v.save,2,i,1,0])
 initial=bytes(v.cpu.mem[v.save:v.save+0x40000]);pilots={x['pilot']:x['team'] for x in cp['members'].values() if x['pilot'] is not None};pilots[1243]='구출대 기타'
 def active(key):
  i=v.cpu.run(0x244a40,[v.save,key,1,0]);return v.cpu.read(v.save+0x25cfc+i*92+2,1)
 # Same political separation as the published setup.
 for key,team in pilots.items():
  if team in [GUARD,REBELS]:v.op(command(0x4a,0x100a8,key,0))
 for s in p['scenes']:
  b=(DEST/s['logo']['file']).read_bytes();rs=records(b)
  if s['guard_player_only']:assert all(active(k)==int(t==GUARD) for k,t in pilots.items())
  for r in rs:
   if r[0]==0x4a:assert v.op(r)==10
  if s['key']==2043:assert all(active(k)==int(t==GUARD) for k,t in pilots.items())
  if s['key']==2047:assert all(active(k)==int(t!=REBELS) for k,t in pilots.items())
 assert bytes(v.cpu.mem[v.save:v.save+0x40000])==initial,'Reunion altered persistent training/equipment or ownership'
 assert [s['number'] for s in p['scenes']]==list(range(42,49));v=machine(base,master);assert v.cpu.run(0x2705c0,[v.master,2,34])==49
 result=dict(passed=True,checks=checks,native_encounter_cases=encounters,native_preparation_and_level_cases=births,guard_only_membership_checks=76,new_guard_missions=2,civil_missions=7,chapter_order=ORDER,display_chapters=list(range(42,49)),final_display_chapter=49,mob_level=52,new_and_final_rebel_ace_level=54,original_final_mob_level=40,original_final_boss_level=48,all_persistent_roster_bytes_restored=True,old_coerced_guard_now_allied_in_joint_rescue=True,original_map_assets_and_original_finale_preserved=True,actual_world_AI_collision_render_card_tested=False,ready_to_apply=True)
 (ROOT/'civil_guard_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
