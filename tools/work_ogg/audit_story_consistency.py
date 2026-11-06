"""Read-only dialogue/context audit of the current single game image."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/('option_consistency' if (ROOT/'option_consistency').exists() else 'option_release')))
from build_options import rawmaster,source_image
from audit_story_layout import loadarc,decode
from story_scripts_25 import records,text_at
from inspect_iso import read,u32
from catalog import u16

def dump():
 report=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'));out=ROOT/'analysis/story_consistency';out.mkdir(exist_ok=True)
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f,source_image() as original:
  _,m=rawmaster(f,'SHARED.BIN');a,es=loadarc(f,14);summary=[]
  def name(key):
   if key>=m.tables['PTbl'][2]:return hex(key)
   idx=u16(m.b,m.tables['PTbl'][0]+12+key*2)
   return m.text(u16(m.b,m.tables['Plot'][0]+12+idx*148+4)) if idx<m.tables['Plot'][2] else hex(key)
  for chapter in report['chapters']:
   key=chapter['key'];_,at,n=next(e for e in es if key in e[0]);blob=read(f,at,n);rs=records(blob);lines=[];messages=[]
   entry=next(e for e in a['entries'] if key in e['keys']);dp=a['directory']+8+entry['index']*8;ptr=read(original,dp,8);p=u32(ptr);size=u32(ptr,4);native=read(original,a['directory']+p,size);nr=records(native)
   for i,r in enumerate(rs):
    if r[0]==0x30:
     t=decode(text_at(blob,r[2]));msg={'row':i,'speaker':name(r[4]),'key':r[4],'sid':r[2],'label':r[1],'text':t};messages.append(msg);lines.append(f"{i} [{r[2]}] {name(r[4])}: {t}")
    elif r[0] in [0x25,0xca,0x93,0xba,0x2f,0x23,0x24,0x7b]:lines.append(f"{i} OP {hex(r[0])} "+' '.join(hex(v) for v in r[2:7]))
   (out/f'{chapter["chapter"]:02d}_{key}.txt').write_text('\n'.join(lines),encoding='utf-8')
   (out/f'{chapter["chapter"]:02d}_{key}.json').write_text(json.dumps(messages,ensure_ascii=False,indent=2),encoding='utf-8')
   start=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,*chapter['flag']]);end=next(i for i in range(start+1,len(rs)) if rs[i][0]==0xba and rs[i][2:5]==[0x100c1,*chapter['flag']])+1
   near=[msg for msg in messages if start-25<=msg['row']<=end+15]
   summary.append({'chapter':chapter['chapter'],'key':key,'arrivals':chapter['arrivals'],'joins':[r['name'] for r in chapter['recruits']],'block':[start,end],'native_last_message':max(i for i,r in enumerate(nr) if r[0]==0x30),'context':near})
  (out/'contexts.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Audited',len(summary),'current chapter scripts:',out)

if __name__=='__main__':dump()
