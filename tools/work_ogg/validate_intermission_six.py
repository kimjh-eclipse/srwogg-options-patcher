"""Native dialogue/history/guards for the incremental ship communications."""
from prepare_intermission_six import *
sys.path.insert(0,str(ROOT/('option_intermission' if (ROOT/'option_intermission').exists() else 'option_release')))
from validate_options import Profiles,ram
from validate_regional_five import VM,CountCPU,load_campaign_master
from story_scripts_25 import records,text_at,command
from intermission_six_content import SCENES

class Counts(CountCPU):
 def step(self):
  if self.pc==0x211ef0:
   self.put(2,int(self.boss_alive));self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
  else:super().step()

def machine(base,master,scene,enemies,boss_alive):
 v=VM(base);v.cpu=Counts(base);v.cpu.r[28]=0x31def0;v.cpu.counts={0:12,2:enemies};v.cpu.boss_alive=boss_alive
 v.cpu.write(v.ctx+0x2870,0x319d40,4);v.cpu.write(v.ctx+0x74cc,scene,2);v.cpu.write(0x46ecec,0,4)
 for i in range(16):v.cpu.write(v.ctx+0x74ec+i*4,0xffffffff,4)
 load_campaign_master(v,master);return v

def walk(v,b,start,stop=None):
 rs=records(b);i=start;shown=[];seen=[]
 for steps in range(len(rs)*3):
  if i==stop:return shown,seen,None
  r=rs[i];seen.append(r[0]);v.cpu.write(v.ctx+0x48d0,i,4)
  if r[0] in [0x3e,0x25]:return shown,seen,None
  if r[0]==0x30:shown.append(r[2])
  elif r[0] in [0x79,0x7a,0x93,0x96,0x91,0x9a,0xba]:
   result=v.op(r)
   if result==13:return shown,seen,None
   assert result==10,(hex(r[0]),result);i=v.cpu.read(v.ctx+0x48d0,4)+1;continue
  elif r[0]==0xa1:assert v.op(r)==14;return shown,seen,r[2]
  else:assert r[0] in [0x26,0x7b,0x6d,0x67,0xaf,0xb0],hex(r[0])
  i+=1
 raise AssertionError('event loop')

def main():
 p=json.loads((ROOT/'intermission_six_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),4095);checks=0;reports=[]
 cast=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast'];expected={x['pilot_name'] for x in cast}-{'아기라','세프타킨'}
 used={who for x in SCENES.values() for phase in ['pre','post'] for kind,lines in x[phase] for who,text in lines if kind=='story'};assert expected<=used,(expected-used)
 with TARGET.open('rb') as f:
  _,master=rawmaster(f,'SHARED.BIN')
  for s in p['scenes']:
   old=read(f,s['old_logo']['offset'],s['old_logo']['size']);b=(DEST/s['logo']['file']).read_bytes();rs=records(b);ors=records(old);pos={int(k):v for k,v in s['old_row_positions'].items()}
   for i,r in enumerate(ors):
    a=rs[pos[i]];ignore=[6,7] if r[0]==0x90 else [7] if r[0]==0x91 else []
    assert all(a[j]==r[j] for j in range(24) if j not in ignore);checks+=1
   assert not any(r[0] in [0x5f,0x60,0x64,0x40,0x41,0xd5,0xd6,0xdd] for i,r in enumerate(rs) if i not in set(pos.values()))
   pre=s['phases']['pre'];post=s['phases']['post'];assert pre['end']==pos[next(i for i,r in enumerate(ors) if r[0]==0xca)]
   assert max(i for i,r in enumerate(rs[:post['start']]) if r[0]==0x6d)<post['start']
   assert rs[post['end']][0]==0xa1;assert any(r[0]==0x7b for r in rs[pre['start']:pre['end']])
   alert=s['messages'][0];assert alert['who'] in ['에이타','윤'] and any(t in alert['text'].replace('　',' ') for t in ['경보','전투 배치','함내 전파'])
   vm=VM(base);load_campaign_master(vm,master.b);vm.cpu.mem[0x1800000:0x1800000+len(b)]=b;vm.cpu.run(0x5363c0,[vm.ctx,0x1800000])
   for i in range(u32(b,24)):assert vm.op(list(struct.unpack_from('<24I',b,u32(b,28)+96*i)))==10;checks+=1
   assert vm.cpu.read(vm.ctx+0x6abc+27*4,4)==(4 if s['key']==2040 else 3)
   for msg in s['messages']:
    raw=text_at(b,msg['sid']);vm.cpu.run(0x53ad00,[vm.ctx,0,msg['sid']]);assert bytes(vm.cpu.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0'
    vm.cpu.run(0x53a1f0,[vm.ctx,msg['label'],0,0,0],stop=0x53a244);ri=vm.cpu.r[4]&0xffffffff;assert u32(b,u32(b,36)+ri*96+8)==msg['sid'];checks+=2
   # All original narrative gates and all new clone interaction gates follow bit0.
   outcomes=[]
   funcs=[u32(b,u32(b,52)+i*16+8) for i in range(1,u32(b,48))]
   for enabled in [False,True]:
    blob=bytearray(b)
    for i in s['old_story_gates']+s['new_story_gates']:struct.pack_into('<I',blob,u32(blob,44)+i*96+16,0 if enabled else 2)
    for phase,scene,enemies,boss in [('pre',0,32,True),('tactical',2,32,True),('post',1,0,False)]:
     n=s['phases'][phase];start=max(i for i in funcs if i<=n['start']);v=machine(base,master.b,scene,enemies,boss)
     if phase!='pre':assert v.op(command(0xba,0x10071,0,0))==10
     shown,ops,nxt=walk(v,blob,start,n['end'] if phase!='post' else None)
     own=[m for m in s['messages'] if m['phase']==phase];actual=[m['sid'] for m in own if m['sid'] in shown];wanted=[m['sid'] for m in own if m['kind']=='common' or enabled];assert actual==wanted,(s['key'],phase,enabled)
     if phase=='post':assert nxt==(s['key']-1999 if s['key']<2039 else 33 if s['key']==2039 else 34)
     if phase=='pre':
      assert v.op(command(0xba,0x10071,0,0))==10;assert not walk(v,blob,start,n['end'])[0]
     if phase=='post':
      # Ending guard rejects an unfinished battle before any post scene.
      v=machine(base,master.b,scene,1,True);v.op(command(0xba,0x10071,0,0));assert not walk(v,blob,start)[0]
     checks+=1;outcomes.append(dict(story_enabled=enabled,phase=phase,new_boxes=len(actual),next_index=nxt))
   reports.append(dict(key=s['key'],new_boxes=len(s['messages']),outcomes=outcomes))
 # Re-run endless reinforcement logic at its relocated native function addresses.
 from validate_beowulf_stage import MapCPU,event
 bp=json.loads((ROOT/'beowulf_stage_prepared.json').read_text(encoding='utf8'));s=next(s for s in p['scenes'] if s['key']==2040);b=(DEST/s['logo']['file']).read_bytes();positions={int(k):v for k,v in s['old_row_positions'].items()};vm=VM(base);vm.cpu=MapCPU(base);vm.cpu.r[28]=0x31def0;vm.cpu.write(vm.ctx+0x2870,0x319d40,4);load_campaign_master(vm,master.b);vm.cpu.configure(vm,bp['spawn']);vm.cpu.write(0x46ecec,0,4);vm.cpu.write(vm.ctx+0x74cc,2,2);vm.cpu.fast_counts=True;vm.op(command(0xba,0x10071,0,0))
 respawn=positions[bp['functions']['reinforcements']];ending=positions[bp['functions']['ending']]
 for cycle in range(100):
  key=bp['spawn'][cycle%30]['key'];vm.cpu.alive[key]=False;vm.cpu.fixture_sync();before=len(vm.cpu.spawned);assert event(vm,b,respawn) is None;assert len(vm.cpu.spawned)==before+1
 vm.cpu.alive[1930]=False;vm.cpu.alive[1931]=False;vm.cpu.fixture_sync();before=len(vm.cpu.spawned);assert event(vm,b,respawn) is None and len(vm.cpu.spawned)==before;assert event(vm,b,ending)==34;checks+=102
 result=dict(passed=True,checks=checks,missions=6,pre_scenes=6,post_scenes=6,tactical_expansions=6,new_lines=p['new_lines'],new_boxes=p['new_boxes'],all_25_added_members_in_ship_scenes=True,ship_crew_alerts_before_deployment=True,post_scenes_after_native_result_before_next_stage=True,native_text_history_and_option_guards=True,relocated_beowulf_fixture_cycles=100,boss_death_stops_respawns_and_routes_to_finale=True,original_gameplay_records_preserved=True,live_render_or_playthrough=False,ready_to_apply=True,details=reports)
 (ROOT/'intermission_six_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False))
if __name__=='__main__':main()
