"""Prepare incremental dialogue-only edits; original missions/resources remain."""
from pathlib import Path
import sys,json,struct,hashlib,base64,zlib
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT/('option_intermission' if (ROOT/'option_intermission').exists() else 'option_release'))]
from build_options import rawmaster
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32,inventory,lice
from catalog import u16
from intermission_six_content import SCENES
from intermission_six_policy import extend
DEST=ROOT/'analysis/intermission_six';START=0x1b032000;LIMIT=0x1b080000

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('intermission_six_applied');DEST.mkdir(exist_ok=True)
 speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers'];speakers.update({'알피미':1347,'레피나':1209,'베오울프':1930,'에이타':1071,'숀':1119,'윤':1181})
 cursor=START;edits=[];scenes=[]
 with TARGET.open('rb') as f:
  la,ls=loadarc(f,14);_,us=loadarc(f,13);_,m=rawmaster(f,'SHARED.BIN');root=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,root['offset'],root['size'])
  for who in {who for c in SCENES.values() for phase in c.values() if isinstance(phase,list) for kind,lines in phase for who,text in lines}:
   assert who in speakers,who;k=speakers[who];ix=u16(m.b,m.tables['PTbl'][0]+12+k*2);assert ix!=65535
   expected={'아라도':'아라드','액셀렌':'엑셀렌','제올라':'제오라'}.get(who,who)
   assert m.text(u16(m.b,m.tables['Plot'][0]+12+ix*148+4))==expected,(who,k)
  def edit(at,after,label):
   before=read(f,at,len(after));file='edit_%02d.bin'%len(edits);(DEST/file).write_bytes(after);edits.append(dict(offset=at,size=len(after),file=file,label=label,before_zlib_base64=base64.b64encode(zlib.compress(before,9)).decode('ascii'),after_sha256=hashlib.sha256(after).hexdigest()))
  for key,content in SCENES.items():
   _,at,n=next(e for e in ls if key in e[0]);old=read(f,at,n);b,note=extend(old,content,speakers);cursor=(cursor+2047)&~2047
   assert cursor+len(b)<=LIMIT and not any(read(f,cursor,len(b)))
   assert all(cursor+len(b)<=p or cursor>=p+n for ks,p,n in us+ls)
   file=str(key)+'.logo';(DEST/file).write_bytes(b);new=dict(offset=cursor,size=len(b),file=file);edit(cursor,b,'Intermission '+str(key))
   ix=next(e['index'] for e in la['entries'] if key in e['keys']);edit(la['directory']+8+ix*8,struct.pack('<II',cursor-la['directory'],len(b)),'LOGO pointer '+str(key))
   scenes.append(dict(key=key,title=content['title'],old_logo=dict(offset=at,size=n),logo=new,**note));cursor+=len(b)
  parent=outer['entries'][14];span=max(parent['size'],cursor-parent['offset']);assert parent['offset']+span<=root['offset']+root['size'];edit(outer['directory']+8+14*8+4,struct.pack('<I',span),'LOGO parent span')
 p=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],scenes=scenes,edits=edits,allocation_start=START,allocation_end=cursor,speakers=speakers,new_lines=sum(sum(n['lines'] for n in s['phases'].values()) for s in scenes),new_boxes=sum(len(s['messages']) for s in scenes),option_count=12,shared_stage_bit=11,story_bit=0,gameplay_resources_preserved=True)
 (ROOT/'intermission_six_prepared.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in p.items() if k not in ['scenes','edits','speakers']},ensure_ascii=False))
if __name__=='__main__':main()
