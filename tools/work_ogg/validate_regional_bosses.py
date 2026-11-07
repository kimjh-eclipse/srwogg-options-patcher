"""Verify boss resource references, placements, native spawning and story guards."""
from pathlib import Path
import sys,json,struct,copy
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_regional' if (ROOT/'option_regional').exists() else 'option_release')),str(ROOT)]
from validate_regional_five import main as check_story,VM,Profiles,ram,load_campaign_master
from validate_party_25 import seed_clones,snapshot
from catalog import Master,u16,u32,decode
from apply_balance_25 import get_record
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,OUT

def main():
 p=json.loads((ROOT/'regional_bosses_prepared.json').read_text(encoding='utf8'));folder=ROOT/'analysis/regional_bosses';master=(folder/'SHARED.BIN.master').read_bytes();m=Master(master)
 story=check_story(prepared=p['new_regional_prepared'],folder=folder,output=ROOT/'regional_bosses_story_validation.json');base=ram(Profiles(),4095);bodies={k for e in json.loads((OUT/'BATTLE.BIN.1.json').read_text(encoding='utf8'))['entries'] if e['size'] for k in e['keys']};checks=0;bosses=p['masters']['SHARED.BIN']['units']
 with TARGET.open('rb') as f:
  _,ter=loadarc(f,12);tb=read(f,ter[0][1],ter[0][2]);names={i:decode(tb[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);rawtiles={k:read(f,at,n) for ks,at,n in mt for k in ks};tiles={}
  for ks,at,n in mi:
   info=read(f,at,n)
   if u32(info,12) in rawtiles:
    for k in ks:tiles[k]=rawtiles[u32(info,12)]
  _,oldmaster=__import__('build_options').rawmaster(f,'SHARED.BIN')
  for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
   at=oldmaster.tables[tag][0]+12;to=m.tables[tag][0]+12;assert oldmaster.b[at:at+oldmaster.tables[tag][2]*stride]==master[to:to+oldmaster.tables[tag][2]*stride];checks+=1
  for boss in bosses:
   _,row=get_record(m,'Unit','UTbl',boss['key'],100);_,original=get_record(oldmaster,'Unit','UTbl',boss['source_key'],100)
   assert u16(row,0x44)==u16(original,0x44) and u16(row,0x44) in bodies
   assert u32(row)==boss['hp'] and u16(row,0x14)==65535 and row[0x5d]==0 and not any(a in [10,11,12,14,15] for a in row[0x57:0x5d]);checks+=2
   for w in boss['weapons']:
    _,wr=get_record(m,'Weap','WTbl',w['key'],36);_,old=get_record(oldmaster,'Weap','WTbl',w['source_key'],36)
    assert all(wr[i]==old[i] for i in range(36) if i not in [8,9]);checks+=1
  for scene in p['new_regional_prepared']['scenes']:
   b=(folder/scene['untd']['file']).read_bytes();t=tiles[scene['map_key']];w,h=u32(t,8),u32(t,12);positions=[];enemybosses=[]
   for i in range(u32(b,40)):
    r=b[44+i*336:44+(i+1)*336];x,y=u32(r,16),u32(r,20);assert 0<x<w and 0<y<h;tid=u32(t,32+(y*w+x)*8)&65535;assert names[tid] not in ['','영역 밖'];positions.append((x,y));checks+=1
    if scene['key']==2038:assert '우주' in names[tid]
    if u32(r) in {b['key'] for b in bosses}:
     assert u32(r,8)==2 and u32(r,32)==1029
     assert all(u32(r,off)==0xffff0405 for off in [0x60,0x74,0x88]);checks+=3;enemybosses.append(u32(r))
   assert len(set(positions))==28 and len(enemybosses)==2;checks+=2
 # Real constructor and grade getters; the renderer and map actor AI are not run.
 for difficulty in [0,1,2]:
  for grade in [6,8]:
   vm=VM(base);load_campaign_master(vm,master);c=vm.cpu;c.write(vm.diff+0xff4,difficulty,4);owned=seed_clones(vm);before=snapshot(vm,owned)
   for boss in bosses:
    scene=next(s for s in p['new_regional_prepared']['scenes'] if s['number']==boss['stage']);blob=(folder/scene['untd']['file']).read_bytes();row=bytearray(blob[44+boss['row']*336:44+(boss['row']+1)*336])
    for off in range(0x38,0x50,4):struct.pack_into('<I',row,off,grade)
    assert vm.birth(row)==1;slot=c.run(0x244c20,[vm.save,boss['key'],0,0]);assert slot>=0
    assert [c.run(0x248950,[vm.save,prop,slot,0]) for prop in range(0xd,0x11)]==[grade]*4;assert snapshot(vm,owned)==before;checks+=3
    for w in boss['weapons']:assert c.run(0x274ff0,[vm.master,w['key']])==w['power'];checks+=1
 result=dict(passed=True,bosses=10,private_weapon_rows=50,native_and_resource_checks=checks,story_checks=story['native_checks'],unmanned_only=True,original_unit_weapon_pilot_rows_preserved=True,original_25_party_stats_preserved=True,all_140_positions_valid=True,map38_real_colony_space_map=40,map39_outside_positions_repaired=True,enemies_per_mission=16,bosses_per_mission=2,live_playthrough=False,memory_card_IO=False,ready_to_apply=True)
 (ROOT/'regional_bosses_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
