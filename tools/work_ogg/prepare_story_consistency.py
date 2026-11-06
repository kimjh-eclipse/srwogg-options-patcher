"""Prepare targeted story edits; do not modify the game image."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_consistency' if (ROOT/'option_consistency').exists() else 'option_release')),str(ROOT)]
from audit_story_layout import loadarc
from inspect_iso import read,u32,inventory,lice
from story_scripts_25 import records,text_at,rebuild_logo,wrap
from story_consistency_logo import replace_box,replace_string,move_guarded
from story_consistency_policy import *

def prepare():
 story=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'));state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));speakers=story['speakers'];out=ROOT/'analysis/consistency_prepared';out.mkdir(exist_ok=True);result=[];errors=[]
 with Path(state['canonical_iso']).open('rb') as f:
  a,es=loadarc(f,14)
  for ch in story['chapters']:
   chapter=ch['chapter']
   if chapter not in REPLACEMENTS and chapter not in MOVES and chapter!=36:continue
   _,at,n=next(e for e in es if ch['key'] in e[0]);old=read(f,at,n);b=old;notes=[]
   for who,needle,new in REPLACEMENTS.get(chapter,[]):
    try:b,note=replace_box(b,who,needle,new,speakers[who]);note['speaker']=who;notes.append(note)
    except Exception as e:errors.append([chapter,who,str(e)])
   for sid,(who,new) in NATIVE_TEXT.get(chapter,{}).items():
    try:
     parts=wrap(who,new.split('：',1)[1]);assert len(parts)==1
     b,note=replace_string(b,sid,parts[0]);note['native']=True;note['speaker']=who;notes.append(note)
    except Exception as e:errors.append([chapter,who,str(e)])
   movement=None;new_scene=None
   if chapter in MOVES:
    spec=MOVES[chapter];b,movement=move_guarded(b,ch['flag'],before_sid=spec.get('before_native_sid'),after_sid=spec.get('after_native_sid'));movement['reason']=spec['reason']
   if chapter==36:
    point=next(i for i,r in enumerate(records(b)) if r[0]==0x30 and r[2]==FINAL_RESPONSE_BEFORE_SID)
    b,new_scene=rebuild_logo(b,point,FINAL_RESPONSE,speakers,FINAL_RESPONSE_FLAG)
   (out/f'{ch["key"]}.logo').write_bytes(b)
   # Later appended payloads may overlap older logical archive spans, but the
   # live payloads themselves must never overlap. Respect every live entry.
   live=[]
   for slot in [13,14]:
    _,items=loadarc(f,slot);live.extend((p,size) for ks,p,size in items if p>at)
   # Reserve optional chapter-three and no-story chapter28 allocations too.
   limits=[p for p,size in live]+[p for p in [0x1b400000,0x1b480000,0x1b530000,0x1b594000] if p>at]
   limit=min(limits);assert at+len(b)<=limit,(chapter,hex(at),len(b),hex(limit))
   entry=next(e for e in a['entries'] if ch['key'] in e['keys']);dp=a['directory']+8+entry['index']*8
   result.append({'chapter':chapter,'key':ch['key'],'offset':at,'old_size':n,'new_size':len(b),'allocation_limit':limit,'directory_pointer':dp,'replacements':notes,'movement':movement,'new_scene':new_scene})
 report={'passed':not errors,'before_sha256':state['current_sha256'],'chapters':result,'errors':errors,'extra_full_ISOs_created':0,'stage':3}
 (ROOT/'story_consistency_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'passed':not errors,'chapters':len(result),'replacements':sum(len(c['replacements']) for c in result),'errors':errors},ensure_ascii=False,indent=2),flush=True)
 return report

if __name__=='__main__':prepare()
