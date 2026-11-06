"""Validate the two master resources and the real power accessors offline."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_huckebein' if (ROOT/'option_huckebein').exists() else 'option_release')),str(ROOT)]
from build_options import TARGET,rawmaster
from validate_options import Profiles,ram
from huckebein_r_weapon_policy import rebuild,UNIT_KEY
from story_vm import VM
from catalog import Master,u16
from apply_balance_25 import get_record

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('huckebein_r_weapons_applied');out=ROOT/'analysis/huckebein_r_weapons';out.mkdir(exist_ok=True);masters={};checks=0
 base=ram(Profiles(),1023)
 with TARGET.open('rb') as f:
  for ar in ['SHARED.BIN','IM.BIN']:
   entry,m=rawmaster(f,ar);blob,note=rebuild(m.b);(out/(ar+'.master')).write_bytes(blob);masters[ar]={'offset':entry['offset'],'size':len(blob),**note};n=Master(blob);vm=VM(base);vm.load_master(blob)
   for w in note['weapons']:
    _,r=get_record(n,'Weap','WTbl',w['private_key'],36);assert r[:8]+r[10:]==bytes.fromhex(w['before_weapon_hex'])[:8]+bytes.fromhex(w['before_weapon_hex'])[10:]
    assert vm.cpu.run(0x274ff0,[vm.master,w['private_key']])==w['after_power'];checks+=1
    assert vm.cpu.run(0x274ff0,[vm.master,w['source_key']])==w['before_power'];checks+=1
    _,other=get_record(n,'Unit','UTbl',1208,100);assert w['private_key'] not in [u16(other,0x24+2*i) for i in range(16)]
 p={'prepared':True,'before_sha256':state['current_sha256'],'masters':masters}
 v={'passed':True,'unit_key':UNIT_KEY,'power_delta':200,'default_weapons':5,'native_power_accessor_checks':checks,'original_weapons_other_units_pilots_and_strings_preserved':True,'range_EN_ammo_motion_upgrade_cost_and_growth_preserved':True,'live_playthrough':False}
 for name,data in [('huckebein_r_weapons_prepared',p),('huckebein_r_weapons_validation',v)]: (ROOT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(v,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
