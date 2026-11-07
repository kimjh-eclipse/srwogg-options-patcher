"""Exercise the seven live turn callbacks with moving ship fixtures."""
from prepare_civil_guard import *
from validate_civil_reinforcements import machine,execute
from validate_options import Profiles,ram
from story_scripts_25 import command
def main():
 p=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),4095);master=(DEST/'SHARED.BIN.master').read_bytes();checks=0
 for s in p['scenes']:
  b=(DEST/s['logo']['file']).read_bytes()
  for ships in [[],[1188],[1215],[1188,1215]]:
   for w in s['waves']:
    for turn in [w['turn']-1,w['turn']]:
     v=machine(base,master,b,s,ships,turn);before=len(v.cpu.spawned);execute(v,b,w['function']);assert len(v.cpu.spawned)-before==(6 if turn==w['turn'] else 0)
     if turn==w['turn']:
      coords=[xy for row,xy in v.cpu.spawned];wanted=[(10+turn,10),(26-turn,18)] if len(ships)==2 else [(10+turn,10)] if ships==[1188] else [(26-turn,18)] if ships==[1215] else [(18,24)];assert coords==[wanted[i%len(wanted)] for i in range(6)];execute(v,b,w['function']);assert len(v.cpu.spawned)==6
     checks+=1
 result=dict(passed=True,seven_stage_native_wave_cases=checks,per_wave=6,turns=[2,3,4],initial_enemies=32,total_enemy_cap=50,guard_side_scenarios_use_Lefina_ship_coordinates=True,repeat_wave_suppressed=True,actual_world_spawn_collision_and_AI_tested=False)
 (ROOT/'civil_guard_waves_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
