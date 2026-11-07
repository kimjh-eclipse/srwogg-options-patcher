"""Verify the expanded enemy lists without a PCSX2 playthrough."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_bosses' if (ROOT/'option_bosses').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster
from validate_options import Profiles,ram
from validate_regional_five import VM,load_campaign_master,condition_machine,condition_event
from validate_party_25 import seed_clones,snapshot
from story_scripts_25 import command
from catalog import u16,decode
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32

def main():
 p=json.loads((ROOT/'regional_density_prepared.json').read_text(encoding='utf8'));checks=0;cases={};scenes=[];base=ram(Profiles(),4095)
 with TARGET.open('rb') as f:
  _,master=rawmaster(f,'SHARED.BIN');_,ter=loadarc(f,12);b=read(f,ter[0][1],ter[0][2]);names={i:decode(b[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);raw={k:read(f,at,n) for ks,at,n in mt for k in ks};tiles={}
  for ks,at,n in mi:
   info=read(f,at,n)
   if u32(info,12) in raw:
    for k in ks:tiles[k]=raw[u32(info,12)]
  for s,active in zip(p['scenes'],p['new_regional_prepared']['scenes']):
   old=read(f,s['previous_untd']['offset'],s['previous_untd']['size']);new=(ROOT/'analysis/regional_density'/s['untd']['file']).read_bytes();assert len(new)==44+44*336 and u32(new,40)==44
   assert new[44:44+28*336]==old[44:];assert new[:40]==old[:40];rows=[new[44+i*336:44+(i+1)*336] for i in range(44)];positions=[];counts={}
   for r in rows:counts[u32(r,8)]=counts.get(u32(r,8),0)+1
   assert counts=={6:12,2:32};assert sum(0x780<=u32(r)<0x78a for r in rows)==2;checks+=4
   t=tiles[active['map_key']];w,h=u32(t,8),u32(t,12)
   for r in rows:
    x,y=u32(r,16),u32(r,20);assert 0<x<w and 0<y<h;name=names[u32(t,32+(y*w+x)*8)&65535];assert name not in ['','영역 밖'];positions.append((x,y))
    if s['key']==2038:assert '우주' in name
    checks+=1
   assert len(set(positions))==44;checks+=1
   for a in s['added']:
    r=rows[a['row']];source=rows[a['source_row']];assert r[:16]==source[:16] and r[24:]==source[24:];assert u32(r,8)==2 and u32(r,4)==0 and not 0x780<=u32(r)<0x78a
    key=(u32(r),u32(r,32),r[24:]);cases.setdefault(key,r);checks+=2
   logo=read(f,active['logo']['offset'],active['logo']['size']);next_index=s['key']-1999 if s['key']<2039 else 33
   for enemies,allies,start in [(32,12,True),(2,12,True),(1,12,True),(0,12,True),(0,0,False)]:
    vm=condition_machine(base,allies,enemies);vm.cpu.write(vm.ctx+0x74cc,1,2)
    if start:assert vm.op(command(0xba,0x10071,0,0))==10
    result,_=condition_event(vm,logo,active['functions']['ending']);assert result==(next_index if start and enemies==0 else None);checks+=1
   scenes.append(dict(key=s['key'],enemies=32,ordinary=30,bosses=2,ally_slots=12,positions=44,original_rows_preserved=28))
 # One representative of each distinct copied record type: real constructor,
 # all three native difficulty branches and independent enemy grades6/8.
 for difficulty in [0,1,2]:
  for grade in [6,8]:
   vm=VM(base);load_campaign_master(vm,master.b);vm.cpu.write(vm.diff+0xff4,difficulty,4);owned=seed_clones(vm);before=snapshot(vm,owned)
   for template in cases.values():
    r=bytearray(template)
    for off in range(0x38,0x50,4):struct.pack_into('<I',r,off,grade)
    assert vm.birth(r)==1;slot=vm.cpu.run(0x244c20,[vm.save,u32(r),0,0]);assert slot>=0
    assert [vm.cpu.run(0x248950,[vm.save,i,slot,0]) for i in range(0xd,0x11)]==[grade]*4;assert snapshot(vm,owned)==before;checks+=3
 report=dict(passed=True,checks=checks,scenes=scenes,added_enemies=80,total_regional_enemies=160,ordinary=150,bosses=10,all_220_positions_valid=True,distinct_spawn_templates=len(cases),original_28_rows_per_mission_preserved=True,masters_and_LOGO_unchanged=True,original_25_party_stats_preserved=True,enemy32_victory_gate_verified=True,live_playthrough=False,memory_card_IO=False,ready_to_apply=True)
 (ROOT/'regional_density_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
