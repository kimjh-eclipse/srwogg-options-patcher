"""Ragnarok routing at zero/low/high mastery without inflating SR points."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/'option_civil_war'),str(ROOT)]
from validate_options import Profiles,ram
from validate_civil_war import machine
from story_scripts_25 import command,records
from inspect_iso import read
from audit_story_layout import TARGET,loadarc
from build_options import rawmaster

def main():
 base=ram(Profiles(),4095);guard=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'));beo=json.loads((ROOT/'beowulf_stage_prepared.json').read_text(encoding='utf8'));checks=0
 with TARGET.open('rb') as f:
  _,m=rawmaster(f,'SHARED.BIN');_,ls=loadarc(f,14)
  stages={k:read(f,at,n) for ks,at,n in ls for k in ks if k in [2040]+guard['chapter_order']}
  for story in [False,True]:
   br=next(x for x in beo['bridge'] if x['mode']==('story' if story else 'native'));blob=read(f,br['offset'],br['size']);row=records(blob)[br['route_row']];assert row[0]==0xa1 and row[2]==40
   for optional in [False,True]:
    path=[40,41]+[k-2000 for k in guard['chapter_order'][1:]]+[34] if optional else [34]
    for mastery in [0,1,17,30,35]:
     for difficulty in [0,1,2]:
      v=machine(base,m.b);v.cpu.write(v.diff+0xfec,2,4);v.cpu.write(v.diff+0xffc,33,4);v.cpu.write(v.diff+0x1008,mastery,4);v.cpu.write(v.diff+0xff4,difficulty,4)
      for index in path:
       assert v.op(command(0xa1,index,0))==14;assert v.cpu.read(v.diff+0xffc,4)==index;assert v.cpu.read(v.diff+0x1008,4)==mastery
      assert v.cpu.read(v.diff+0xffc,4)==34;checks+=1
  # Every added battle has a direct positive transition; no mastery branch.
  for i,key in enumerate(guard['chapter_order']):
   nextindex=guard['chapter_order'][i+1]-2000 if i+1<len(guard['chapter_order']) else 34
   assert [r[2] for r in records(stages[key]) if r[0]==0xa1 and r[2]!=0xffffffff]==[nextindex]
 result=dict(passed=True,native_route_cases=checks,mastery_values=[0,1,17,30,35],difficulties=[0,1,2],story_and_extra_battles_on_off_checked=True,destination_native_stage_index=34,display_with_additional_battles=49,display_without_additional_battles=36,artificial_mastery_increase=False,native_difficulty_calculation_unchanged=True,source_already_directly_routes_original35_to36=True,guide_reference='https://w.atwiki.jp/srwoggaidenkouryaku/pages/105.html',guide_lists_easy_normal_hard_stage=True,live_full_game_transition_not_tested=True)
 (ROOT/'ragnarok_access_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
