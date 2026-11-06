"""Prepare two independent optional features without another ISO."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_consistency' if (ROOT/'option_consistency').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster,source_image
from support_overhaul_policy import *
from story_scripts_25 import records,find_point
from inspect_iso import read
from audit_story_layout import loadarc

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert not state.get('support_overhaul_applied');speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'))['speakers'];cast={r['pilot_name']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf-8'))['cast']};out=ROOT/'analysis/support_overhaul';out.mkdir(exist_ok=True);masters={};scripts=[]
 with Path(state['canonical_iso']).open('rb') as f,source_image() as source:
  for archive in ['SHARED.BIN','IM.BIN']:
   e,m=rawmaster(f,archive);b,note=rebuild_master(m.b,cast);(out/(archive+'.master')).write_bytes(b);masters[archive]={'offset':e['offset'],'size':e['size'],**note}
  a,entries=loadarc(f,14)
  for ks,at,size in entries:
   b=read(f,at,size)
   if b[:4]==b'LOGO':assert not any(r[0] in [0x93,0xba] and r[2:5] in [[0x100c1,*SUPPORT_FLAG],[0x100c1,*MAINTENANCE_FLAG]] for r in records(b))
  def dp(key):return a['directory']+8+next(e['index'] for e in a['entries'] if key in e['keys'])*8
  _,at,size=next(e for e in entries if 2050 in e[0]);b=read(f,at,size);point=next(i for i,r in enumerate(records(b)) if r[0]==0x93 and r[2:5]==[0x100c1,60,1]);gift,note=support_script(b,point,speakers)
  pointer=read(source,dp(2050),8);rel,n=struct.unpack('<II',pointer);stock=read(source,a['directory']+rel,n);native,nnote=support_script(stock,find_point(stock,4),speakers)
  _,at,size=next(e for e in entries if 2027 in e[0]);late,lnote=maintenance_script(read(f,at,size),speakers)
  for key,at,blob,note,label,limit in [(2050,SUPPORT_STORY,gift,note,'support_story',0x1b400000),(2027,MAINTENANCE_STORY,late,lnote,'maintenance_story',SUPPORT_NATIVE),(2050,SUPPORT_NATIVE,native,nnote,'support_native',0x1b500000)]:
   assert at+len(blob)<=limit and not any(read(f,at,len(blob))),(label,len(blob));(out/(label+'.logo')).write_bytes(blob);scripts.append({'key':key,'offset':at,'size':len(blob),'pointer_offset':dp(key),'pointer_hex':struct.pack('<II',at-a['directory'],len(blob)).hex(),'label':label,'note':note})
 report={'prepared':True,'before_sha256':state['current_sha256'],'masters':masters,'scripts':scripts,'extra_full_ISOs_created':0,'support_chapter':4,'overhaul_from_chapter':30,'lineups':6,'weapons':9}
 (ROOT/'support_overhaul_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'prepared':True,'scripts':[(s['label'],s['size']) for s in scripts],'masters':{k:v['used_bytes'] for k,v in masters.items()},'units':[u['name'] for u in masters['SHARED.BIN']['units']]},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
