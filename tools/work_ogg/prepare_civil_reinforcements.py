"""Incremental preparation over the published five-part campaign."""
from pathlib import Path
import sys,json,struct,hashlib,zlib,base64
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_civil_war' if (ROOT/'option_civil_war').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32,inventory,lice
from catalog import u16
from civil_reinforcement_policy import *
DEST=ROOT/'analysis/civil_reinforcements'

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert state['civil_war_applied'] and not state.get('civil_reinforcements_applied');p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));DEST.mkdir(exist_ok=True);edits=[];scenes=[]
 with TARGET.open('rb') as f:
  ua,us=loadarc(f,13);la,ls=loadarc(f,14);file=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,file['offset'],file['size']);blocked=[(at,at+n) for ks,at,n in us+ls]
  start=0x1ac39800;end=0x1b480000;raw=read(f,start,end-start);gaps=[];first=None
  for i in range(0,len(raw),2048):
   at=start+i;empty=not any(raw[i:i+2048]) and all(at+2048<=a or at>=b for a,b in blocked)
   if empty and first is None:first=at
   if not empty and first is not None:gaps.append([first,at]);first=None
  if first is not None:gaps.append([first,end])
  def edit(at,data,label):
   old=read(f,at,len(data));fn='edit_%03d.bin'%len(edits);(DEST/fn).write_bytes(data);edits.append(dict(offset=at,size=len(data),file=fn,label=label,before_zlib_base64=base64.b64encode(zlib.compress(old,9)).decode('ascii'),after_sha256=hashlib.sha256(data).hexdigest()))
  def alloc(fn,data):
   for gap in gaps:
    at=(gap[0]+2047)&~2047
    if at+len(data)<=gap[1]:break
   else:raise AssertionError(('no safe MAP allocation',len(data)))
   assert not any(read(f,at,len(data)));gap[0]=(at+len(data)+2047)&~2047;(DEST/fn).write_bytes(data);edit(at,data,fn);return dict(offset=at,size=len(data),file=fn)
  for archive in ['SHARED.BIN','IM.BIN']:
   e,m=rawmaster(f,archive);b=bytearray(m.b);at=m.tables['UTbl'][0]+12
   for j,key in enumerate(KEYS):
    assert u16(b,at+key*2)==65535;source=SOURCES[j%6];ix=u16(b,at+source*2);assert ix!=65535;struct.pack_into('<H',b,at+key*2,ix)
   (DEST/(archive+'.master')).write_bytes(b);edit(e['offset'],b,'Reserved wave aliases '+archive)
  for old in p['scenes']:
   key=old['key'];_,at,n=next(e for e in us if key in e[0]);units=read(f,at,n);assert u32(units,40)==45;new=bytearray(units);spawn=[]
   for j,key2 in enumerate(KEYS):
    row=bytearray(units[44+12*336:44+13*336]);wave=j//6;dx,dy=OFFSETS[j%6]
    for off,val in [(0,key2),(4,2+wave),(8,2),(12,0),(16,dx),(20,dy),(28,0),(32,1029),(36,-1),(40,-1),(44,-1)]:struct.pack_into('<I',row,off,val&0xffffffff)
    for off in range(0x38,0x50,4):struct.pack_into('<I',row,off,8)
    for off in [0x60,0x74,0x88]:struct.pack_into('<I',row,off,0xffff0000|1029)
    new.extend(row);spawn.append(dict(row=45+j,key=key2,pilot=1029,source=SOURCES[j%6],turn=wave+2,group=wave+2,offset=[dx,dy],base_grade=6))
   struct.pack_into('<I',new,40,63);un=alloc(str(key)+'.untd',new);_,at,n=next(e for e in ls if key in e[0]);logo=read(f,at,n);changed,note=append_waves(logo);lo=alloc(str(key)+'.logo',changed)
   for arc,kind,item in [(ua,'untd',un),(la,'logo',lo)]:
    index=next(e['index'] for e in arc['entries'] if key in e['keys']);edit(arc['directory']+8+index*8,struct.pack('<II',item['offset']-arc['directory'],item['size']),kind+' pointer '+str(key))
   scenes.append(dict(key=key,number=old['number'],title=old['title'],logo=lo,untd=un,old_logo=old['logo'],old_untd=old['untd'],spawn=spawn,**note))
  for slot,arc,kind,leaves in [(13,ua,'untd',us),(14,la,'logo',ls)]:
   parent=outer['entries'][slot];end=max([at+n for ks,at,n in leaves]+[s[kind]['offset']+s[kind]['size'] for s in scenes]);edit(outer['directory']+8+slot*8+4,struct.pack('<I',max(parent['size'],end-parent['offset'])),'MAP parent span '+str(slot))
 edits.sort(key=lambda e:e['offset']);assert all(a['offset']+a['size']<=b['offset'] for a,b in zip(edits,edits[1:]))
 result=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],scenes=scenes,edits=edits,per_wave=6,turns=[2,3,4],total_added_per_stage=18,initial_enemies=32,maximum_total_enemies=50,master_rows_unchanged=True,aliases=KEYS,shared_option=12)
 (ROOT/'civil_reinforcements_prepared.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['edits','scenes']},indent=2))
if __name__=='__main__':main()
