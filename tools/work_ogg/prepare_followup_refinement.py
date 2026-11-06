"""Seventeen text-only edits, preserving message IDs, rows and event placement."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_huckebein' if (ROOT/'option_huckebein').exists() else 'option_release')),str(ROOT)]
from build_options import TARGET
from validate_options import Profiles,ram
from audit_story_layout import loadarc
from inspect_iso import read,u32
from story_scripts_25 import records,text_at,wrap,encode
from story_consistency_logo import replace_box
from followup_refinement_policy import REPLACEMENTS
from story_vm import VM

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('followup_refinement_applied');base=ram(Profiles(),1023);out=ROOT/'analysis/followup_refinement';out.mkdir(exist_ok=True);scenes=[];checks=0
 with TARGET.open('rb') as f:
  _,es=loadarc(f,14)
  for ch,changes in REPLACEMENTS.items():
   key=ch+1998;_,at,size=next(e for e in es if key in e[0]);old=read(f,at,size);b=old;messages=[]
   for who,needle,text in changes:
    b,note=replace_box(b,who,needle,text,next(r[4] for r in records(old) if r[0]==0x30 and text_at(old,r[2])==encode(wrap(who,needle)[0])))
    note['speaker']=who;note['source_text']=text;messages.append(note)
   assert len(b)==len(old) and records(b)==records(old)
   changed={m['string_id'] for m in messages}
   for sid in range(u32(old,64)+u32(old,80)-1):
    if sid not in changed:assert text_at(b,sid)==text_at(old,sid)
   vm=VM(base);c=vm.cpu;address=0x1800000;c.mem[address:address+len(b)]=b;c.run(0x5363c0,[vm.ctx,address])
   for m in messages:
    raw=encode(m['text']);sid=m['string_id'];c.run(0x53ad00,[vm.ctx,0,sid]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0';r=next(r for r in records(b) if r[0]==0x30 and r[2]==sid);c.run(0x53a1f0,[vm.ctx,r[1],0,0,0],stop=0x53a244);assert u32(b,u32(b,36)+(c.r[4]&0xffffffff)*96+8)==sid;checks+=2
   (out/f'{key}.logo').write_bytes(b);scenes.append({'chapter':ch,'key':key,'offset':at,'size':size,'before_sha256':hashlib.sha256(old).hexdigest(),'messages':messages})
 p={'prepared':True,'before_sha256':state['current_sha256'],'scenes':scenes,'changed_boxes':sum(len(s['messages']) for s in scenes)}
 v={'passed':True,'chapters':list(REPLACEMENTS),'changed_boxes':p['changed_boxes'],'native_text_history_checks':checks,'record_order_flags_dialogue_history_and_other_strings_preserved':True,'gameplay_changes':False,'live_playthrough':False}
 for name,data in [('followup_refinement_prepared',p),('followup_refinement_validation',v)]: (ROOT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(v,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
