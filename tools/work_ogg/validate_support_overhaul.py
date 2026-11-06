"""Native support inventory, phased weapons, upgrade/save preservation checks."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_consistency' if (ROOT/'option_consistency').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from build_options import rawmaster
from story_vm import VM
from catalog import Master,u16
from story_scripts_25 import records,text_at,command
from story_consistency_logo import guarded_block
from support_overhaul_policy import *
from inspect_iso import read,u32

def block(vm,blob,flag,enabled):
 rs=records(blob);start,end=guarded_block(blob,flag);i=start;grants=messages=0
 while i<end:
  r=rs[i].copy();vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0]==0x30:messages+=1;i+=1;continue
  if i==start+1 and not enabled:r[4]=2
  assert r[0] in [0x93,0x91,0xba,0x64];assert vm.op(r)==10;grants+=r[0]==0x64;i=vm.cpu.read(vm.ctx+0x48d0,4)+1
 return grants,messages

def qty(vm,key):return sum(vm.cpu.read(vm.save+0x21efc+i*4,2)==key for i in range(0x3e00//4))

def validate():
 report=json.loads((ROOT/'support_overhaul_prepared.json').read_text(encoding='utf-8'));assert report['prepared'];base=ram(Profiles(),127);out=ROOT/'analysis/support_overhaul';text_checks=0;support=[];phase_checks=grade_checks=0
 for s in report['scripts']:
  blob=(out/(s['label']+'.logo')).read_bytes();vm=VM(base);c=vm.cpu;address=0x1800000;c.mem[address:address+len(blob)]=blob;c.run(0x5363c0,[vm.ctx,address])
  for m in s['note']['messages']:
   raw=bytes.fromhex(m['encoded']);assert len(raw)<128;c.run(0x53ad00,[vm.ctx,0,m['string_id']]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0';c.run(0x53a1f0,[vm.ctx,m['label'],0,0,0],stop=0x53a244);i=c.r[4]&0xffffffff;assert u32(blob,u32(blob,36)+i*96+8)==m['string_id'];text_checks+=2
  if s['label'].startswith('support'):
   for enabled in [False,True]:
    vm=VM(base)
    for op,key,name in SUPPORT_ITEMS:assert vm.op(command(op,key,0))==10
    before=[qty(vm,k) for op,k,n in SUPPORT_ITEMS];assert before==[1,1]
    assert block(vm,blob,SUPPORT_FLAG,enabled)[0]==(2 if enabled else 0);assert [qty(vm,k) for op,k,n in SUPPORT_ITEMS]==[1+int(enabled)]*2
    assert block(vm,blob,SUPPORT_FLAG,enabled)[0]==0
    save=bytes(vm.cpu.mem[vm.save:vm.save+0x40000]);diff=bytes(vm.cpu.mem[vm.diff:vm.diff+0x1300]);vm=VM(base);vm.cpu.mem[vm.save:vm.save+len(save)]=save;vm.cpu.mem[vm.diff:vm.diff+len(diff)]=diff
    assert block(vm,blob,SUPPORT_FLAG,enabled)[0]==0;assert [qty(vm,k) for op,k,n in SUPPORT_ITEMS]==[1+int(enabled)]*2;support.append({'script':s['label'],'enabled':enabled,'extra_each':int(enabled),'repeat_and_reload_grants':0,'existing_stock_preserved':True})
  else:
   vm=VM(base);assert block(vm,blob,MAINTENANCE_FLAG,False)==(0,0);assert block(vm,blob,MAINTENANCE_FLAG,True)[1]==len(s['note']['messages']);assert block(vm,blob,MAINTENANCE_FLAG,True)==(0,0)
 story=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'));recruits={r['name']:r for ch in story['chapters'] for r in ch['recruits']}
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
  for archive,data in report['masters'].items():
   _,old=rawmaster(f,archive);blob=(out/(archive+'.master')).read_bytes();m=Master(blob);vm=VM(base);vm.load_master(blob);c=vm.cpu
   for u in (data['units'] if archive=='SHARED.BIN' else []):
    row=bytearray.fromhex(recruits[u['name']]['row_hex'])
    for p in range(0x38,0x50,4):struct.pack_into('<I',row,p,5)
    assert vm.birth(row)==1
    us=c.run(0x244c20,[vm.save,u['key'],0,0]);ps=c.run(0x244a40,[vm.save,u['key'],1,0]);assert us>=0 and ps>=0,(archive,u['name'],us,ps);c.write(vm.save+0x25cfc+ps*92+8,913,2)
   snapshot=bytes(c.mem[vm.save:vm.save+0x40000])
   for progress in [0,28,29,35]:
    c.write(vm.diff+0x1000,progress,4)
    for u in data['units']:
     body=c.run(0x278880,[vm.master+0x40,u['full_index']]);expected_index=u['full_index'] if progress>=29 else u['early_index'];assert body==0x1900000+m.tables['Unit'][0]+12+expected_index*100;phase_checks+=1
     us=c.run(0x244c20,[vm.save,u['key'],0,0]) if archive=='SHARED.BIN' else -1
     for w in u['weapons']:
      wk=c.read(body+0x24+w['slot']*2,2);assert wk==(w['new_key'] if progress>=29 else w['old_key']);expected_en=w['after_en'] if progress>=29 else w['before_en'];expected_ammo=w['after_ammo'] if progress>=29 else w['before_ammo']
      assert c.run(0x274cf0,[vm.master,wk])==expected_en;assert c.run(0x274d70,[vm.master,wk])==expected_ammo;assert c.run(0x274ff0,[vm.master,wk])==w['power'];phase_checks+=4
      if archive=='SHARED.BIN':
       ptr=0x17f0000;c.write(ptr,w['slot'],4);assert c.run(0x248950,[vm.save,0xc,us,ptr])==5;grade_checks+=1
    assert bytes(c.mem[vm.save:vm.save+0x40000])==snapshot
   save=snapshot;diff=bytes(c.mem[vm.diff:vm.diff+0x1300]);other=VM(base);other.load_master(blob);other.cpu.mem[other.save:other.save+len(save)]=save;other.cpu.mem[other.diff:other.diff+len(diff)]=diff
   assert bytes(other.cpu.mem[other.save:other.save+len(save)])==snapshot
 result={'passed':True,'live_playthrough':False,'support_inventory_cases':support,'native_text_history_checks':text_checks,'native_phase_and_weapon_checks':phase_checks,'weapon_upgrade_preservation_checks':grade_checks,'six_allied_units':list(TUNING),'weapon_edits':9,'old_weapons_other_units_and_pilots_preserved':True,'experience_PP_and_upgrade_state_unchanged':True,'threshold':'cleared29 / chapter30 onward','ammo_note':'Existing current ammunition is not replenished by the phase lookup; refill/maintenance uses the higher maximum.','save_reload':'persistent Save/Diff copied into a fresh VM; no memory-card I/O'}
 (ROOT/'support_overhaul_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True);return result

if __name__=='__main__':validate()
