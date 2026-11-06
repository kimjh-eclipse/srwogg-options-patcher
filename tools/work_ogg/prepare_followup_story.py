"""Prepare five dialogue-only scenes in verified unused MAP padding."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_support' if (ROOT/'option_support').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles
from build_options import rawmaster
from inspect_iso import inventory,lice,read,u32
from audit_story_layout import loadarc
from story_scripts_25 import records,rebuild_logo
from story_consistency_logo import guarded_block
from followup_story_content import SCENES

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('followup_story_applied');speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'))['speakers'];out=ROOT/'analysis/followup_prepared';out.mkdir(exist_ok=True);profile=Profiles();result=[];cursor=0x1ad00000;limit=0x1b000000
 with Path(state['canonical_iso']).open('rb') as f:
  entry=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,entry['offset'],entry['size']);nonstory=[e['offset']+e['size'] for e in outer['entries'] if e['index'] not in [13,14]];assert cursor>=max(nonstory)
  archive,scripts=loadarc(f,14);_,units=loadarc(f,13);leaf=[(p,p+n) for ks,p,n in scripts+units];used_flags=set()
  for ks,at,n in scripts:
   blob=read(f,at,n)
   for r in records(blob):
    if r[0] in [0x93,0xba] and r[2]==0x100c1:used_flags.add(tuple(r[3:5]))
  assert len({tuple(s['flag']) for s in SCENES})==len(SCENES);assert all(tuple(s['flag']) not in used_flags for s in SCENES)
  for scene in SCENES:
   _,old_at,n=next(e for e in scripts if scene['key'] in e[0]);old=read(f,old_at,n);rs=records(old)
   if 'before_flag' in scene:point=guarded_block(old,scene['before_flag'])[0]
   else:
    sid=scene.get('before_sid',scene.get('after_sid'));point=next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==sid)+int('after_sid' in scene)
   new,note=rebuild_logo(old,point,scene['lines'],speakers,scene['flag']);cursor=(cursor+2047)&~2047;end=cursor+len(new);assert end<=limit
   assert not any(read(f,cursor,len(new)))
   assert all(end<=lo or cursor>=hi for lo,hi in leaf)
   assert all(end<=at or cursor>=at+len(b) for at,b in profile.regions), 'Do not reuse optional/legacy managed resources'
   e=next(e for e in archive['entries'] if scene['key'] in e['keys']);dp=archive['directory']+8+e['index']*8
   (out/f'{scene["key"]}.logo').write_bytes(new)
   result.append({'chapter':scene['chapter'],'key':scene['key'],'title':scene['title'],'old_offset':old_at,'old_size':n,'offset':cursor,'size':len(new),'pointer_offset':dp,'pointer_hex':struct.pack('<II',cursor-archive['directory'],len(new)).hex(),'flag':scene['flag'],'source_lines':len(scene['lines']),**note});cursor=end
 report={'prepared':True,'before_sha256':state['current_sha256'],'scenes':result,'scene_count':len(result),'source_lines':sum(s['source_lines'] for s in result),'boxes':sum(len(s['messages']) for s in result),'allocation_start':0x1ad00000,'allocation_end':cursor,'allocation_limit':limit,'no_gameplay_or_roster_commands_added':True,'extra_full_ISOs_created':0}
 (ROOT/'followup_story_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='scenes'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
