"""Prepare small mission resources and a reviewable script; never writes an ISO."""
from pathlib import Path
import sys,json,struct,collections
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/('option_huckebein' if (ROOT/'option_huckebein').exists() else 'option_release')))
from build_options import rawmaster,source_image
from inspect_iso import read,u32,inventory,lice
from audit_story_layout import TARGET,loadarc
from regional_five_policy import *
from story_scripts_25 import rebuild_logo

DEST=ROOT/'analysis/regional_five';START=0x1ade0000;LIMIT=0x1b000000

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('regional_five_applied')
 DEST.mkdir(parents=True,exist_ok=True)
 speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers'];speakers['알피미']=0x543;speakers['레피나']=0x4b9
 cursor=START;resources=[];scenes=[];masters={}
 with TARGET.open('rb') as f,source_image() as source:
  root=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,root['offset'],root['size'])
  ua,us=loadarc(f,13);la,ls=loadarc(f,14)
  def get(es,k):
   _,p,n=next(e for e in es if k in e[0]);return read(f,p,n)
  def alloc(name,b):
   nonlocal cursor
   cursor=(cursor+2047)&~2047;assert cursor+len(b)<=LIMIT and not any(read(f,cursor,len(b)))
   assert all(cursor+len(b)<=p or cursor>=p+n for _,p,n in us+ls)
   (DEST/name).write_bytes(b);r=dict(file=name,offset=cursor,size=len(b));resources.append(r);cursor+=len(b);return r
  templates={}
  for ks,p,n in us:
   b=read(f,p,n)
   if len(b)!=44+u32(b,40)*336:continue
   for i in range(u32(b,40)):
    row=b[44+i*336:44+(i+1)*336]
    if u32(row,8)==2:templates.setdefault(u32(row),row)
  late=get(us,2032);selection=next(late[44+i*336:44+(i+1)*336] for i in range(u32(late,40)) if u32(late,44+i*336+8)==6)
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);tilesbyid={k:read(f,p,n) for keys,p,n in mt for k in keys};tiles={}
  for keys,p,n in mi:
   info=read(f,p,n);tk=u32(info,12)
   if tk in tilesbyid:
    for k in keys:tiles[k]=tilesbyid[tk]
  template=get(ls,2032)
  for index,s in enumerate(SCENARIOS):
   src=get(us,s['map_source']);mapkey=u32(src,8+s['map_slot']*4);tb=tiles[mapkey];w,h=u32(tb,8),u32(tb,12)
   # Use actual occupied, traversable surfaces from this source battlefield.
   native=[src[44+i*336:44+(i+1)*336] for i in range(u32(src,40))]
   coords=[(u32(r,16),u32(r,20)) for r in native if u32(r,16)<w and u32(r,20)<h and (u32(r,16),u32(r,20))!=(0,0)]
   safe={tb[32+(y*w+x)*8:36+(y*w+x)*8] for x,y in coords};safe.discard(bytes(4));assert safe
   candidates=[(x,y) for y in range(2,h-2) for x in range(2,w-2) if tb[32+(y*w+x)*8:36+(y*w+x)*8] in safe]
   assert len(candidates)>=60,(mapkey,w,h,len(candidates))
   ally=sorted(candidates,key=lambda c:abs(c[0]-w//2)+abs(c[1]-(h-5)))[:12]
   enemy=sorted((c for c in candidates if c not in ally and min(abs(c[0]-x)+abs(c[1]-y) for x,y in ally)>=8),key=lambda c:abs(c[0]-w//2)+abs(c[1]-5))[:16]
   assert len(enemy)==16 and len(set(ally+enemy))==28
   rows=[]
   for i,(x,y) in enumerate(ally):
    row=bytearray(selection)
    for p,v in [(4,30),(12,0),(16,x),(20,y)]:struct.pack_into('<I',row,p,v)
    rows.append(row)
   enote=[]
   for i,(uk,(x,y)) in enumerate(zip(ENEMIES[index],enemy)):
    assert uk in templates,('enemy template missing',uk)
    row=bytearray(templates[uk])
    # Use anonymous pilots: early source rows may contain named boss occupants.
    # Do not turn the allied Igret/Echidna into duplicate enemy characters.
    pilot=[1029,1023,1029,1029,1237][index]
    for p,v in [(4,0),(12,0),(16,x),(20,y),(28,0),(32,pilot)]:struct.pack_into('<I',row,p,v)
    # Fixed, ordinary late-game opponents. Original masters remain untouched.
    for p in range(0x38,0x50,4):struct.pack_into('<I',row,p,8) # base6 + existing optional enemy2
    for p in [0x50,0x54,0x58]:struct.pack_into('<I',row,p,(48+index)*500)
    rows.append(row);enote.append(dict(unit=uk,pilot=u32(row,32),position=[x,y],base_grade=6,level=48+index))
   b=bytearray(src[:44]);struct.pack_into('<4I',b,8,mapkey,0xffffffff,0xffffffff,0xffffffff);b[24:40]=str(s['key']).encode('ascii')+bytes(12);struct.pack_into('<I',b,40,len(rows));b.extend(b''.join(rows))
   un=alloc(f'{s["key"]}.untd',bytes(b));logo,note=mission_logo(template,s,speakers,mapkey,36+index if index<4 else 33);lo=alloc(f'{s["key"]}.logo',logo)
   scenes.append(dict(number=s['number'],key=s['key'],title=s['title'],location=s['location'],map_source=s['map_source'],map_slot=s['map_slot'],map_key=mapkey,dimensions=[w,h],focus=s['focus'],enemy_theme=s['enemy_theme'],enemies=enote,selection_slots=12,untd=un,logo=lo,**note))
  # Bridge variants preserve each native/story script and only append new boxes.
  bridge=[]
  for mode in ['story','native']:
   if mode=='story':old=get(ls,2032)
   else:
    ix=next(e['index'] for e in la['entries'] if 2032 in e['keys']);rel,n=struct.unpack('<II',read(source,la['directory']+8+ix*8,8));old=read(source,la['directory']+rel,n)
   route=next(i for i,r in enumerate(records(old)) if r[0]==0xa1 and r[2]==33)
   point=max(i for i,r in enumerate(records(old)[:route]) if r[0]==0x30)+1
   new,note=rebuild_logo(old,point,BRIDGE,speakers,(58,0));rs=records(new);route=next(i for i,r in enumerate(rs) if r[0]==0xa1 and r[2]==33);new=bytearray(new);struct.pack_into('<I',new,u32(new,44)+route*96+8,35)
   item=alloc(f'2032_{mode}.logo',bytes(new));bridge.append(dict(mode=mode,route_row=route,**item,**note))
  for name in ['SHARED.BIN']:
   e,m=rawmaster(f,name);b,note=master_titles(m.b);(DEST/(name+'.master')).write_bytes(b);masters[name]=dict(offset=e['offset'],size=e['size'],file=name+'.master',**note)
 report=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],scenes=scenes,bridge=bridge,masters=masters,resources=resources,allocation_start=START,allocation_end=cursor,allocation_limit=LIMIT,slot_counts={13:ua['count'],14:la['count']},playthrough_verified=False,status='prototype; native battle completion and checkpoint reload must be verified before image application')
 (ROOT/'regional_five_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(dict(prepared=True,missions=len(scenes),new_boxes=sum(len(s['messages']) for s in scenes)+len(bridge[0]['messages']),allocation_end=hex(cursor),image_modified=False),ensure_ascii=False))

if __name__=='__main__':main()
