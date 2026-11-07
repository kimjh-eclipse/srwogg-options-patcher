"""Regress the relocated sixth battle's respawn and new outgoing route."""
from validate_civil_war import *
from validate_beowulf_stage import MapCPU
class BridgeCPU(MapCPU,PartyCPU):pass
def event(v,b,start):
 rs=records(b);i=start
 while i<len(rs):
  r=rs[i];v.cpu.write(v.ctx+0x48d0,i,4)
  if r[0] in [0x3e,0x25]:return None
  if r[0] in [0x79,0x7a,0x93,0x96,0x91,0x9a,0xba,0xcc,0x4a]:
   result=v.op(r)
   if result==13:return None
   assert result==10;i=v.cpu.read(v.ctx+0x48d0,4)+1;continue
  if r[0]==0xa1:assert v.op(r)==14;return r[2]
  assert r[0] in [0x26,0x30,0x7b,0x6d,0x67,0xaf,0xb0],hex(r[0]);i+=1
 raise AssertionError('unterminated event')
def main():
 p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));s=next(x for x in p['bridges'] if x['key']==2040);b=(DEST/s['logo']['file']).read_bytes()
 ip=json.loads((ROOT/'intermission_six_prepared.json').read_text(encoding='utf8'));old=next(x for x in ip['scenes'] if x['key']==2040);bp=json.loads((ROOT/'beowulf_stage_prepared.json').read_text(encoding='utf8'))
 def row(name):return s['old_row_positions'][str(old['old_row_positions'][str(bp['functions'][name])])]
 base=ram(Profiles(),4095);v=VM(base);v.cpu=BridgeCPU(base);v.cpu.r[28]=0x31def0;v.cpu.write(v.ctx+0x2870,0x319d40,4);load_campaign_master(v,(DEST/'SHARED.BIN.master').read_bytes());v.cpu.configure(v,bp['spawn']);v.cpu.write(0x46ecec,0,4);v.cpu.write(v.ctx+0x74cc,2,2);v.cpu.fast_counts=True;v.op(command(0xba,0x10071,0,0))
 for cycle in range(100):
  key=bp['spawn'][cycle%30]['key'];v.cpu.alive[key]=False;v.cpu.fixture_sync();before=len(v.cpu.spawned);assert event(v,b,row('reinforcements')) is None;assert len(v.cpu.spawned)==before+1
 v.cpu.alive[1930]=False;v.cpu.alive[1931]=False;v.cpu.fixture_sync();before=len(v.cpu.spawned);assert event(v,b,row('reinforcements')) is None and len(v.cpu.spawned)==before;assert event(v,b,row('ending'))==41
 result=dict(passed=True,relocated_respawn_cycles=100,boss_death_stops_respawns=True,new_civil_war_route_index=41,original_map_spawn_service_is_fixture=True)
 (ROOT/'civil_war_beowulf_bridge_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
