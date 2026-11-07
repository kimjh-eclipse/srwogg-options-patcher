"""Prepare the sixth battle and import the user's own OGs assets read-only."""
from audit_beowulf_resources import *
from beowulf_stage_policy import *
from beowulf_stage_content import BRIDGE,FLAG
from catalog import decode
from story_scripts_25 import rebuild_logo,records
from apply_regional_five import pack
import hashlib,base64,zlib,copy

DEST=ROOT/'analysis/beowulf_stage'

class Plan:
 def __init__(self,f):self.f=f;self.edits=[];self.resources=[];self.free={};self.directory_proofs=[]
 def set(self,at,b,label):
  b=bytes(b);lo=at;hi=at+len(b);over=[r for r in self.edits if r[0]<hi and lo<r[0]+len(r[1])]
  if over:
   lo=min([lo]+[r[0] for r in over]);hi=max([hi]+[r[0]+len(r[1]) for r in over]);new=bytearray(read(self.f,lo,hi-lo))
   for p,a,x,l in over:new[p-lo:p-lo+len(x)]=x;self.edits.remove((p,a,x,l))
   new[at-lo:at-lo+len(b)]=b;at=lo;b=bytes(new);label='; '.join([r[3] for r in over]+[label])
  old=read(self.f,at,len(b))
  if old!=b:self.edits.append((at,old,b,label))
 def find_free(self,name,root,e):
  cs=children(self.f,root);spans=[(root['offset'],root['directory']+8+root['count']*8)]
  for a in cs.values():spans.append((a['offset'],a['directory']+8+a['count']*8));spans.extend((x['offset'],x['offset']+x['size']) for x in a['entries'])
  spans.sort();end=e['offset'];gaps=[]
  for lo,hi in spans:
   if lo>end:gaps.append((end,lo))
   end=max(end,hi)
  gaps.append((end,e['offset']+e['size']));runs=[]
  for lo,hi in gaps:
   if hi-lo<32768:continue
   start=(lo+2047)&~2047;finish=hi&~2047;active=None;raw=read(self.f,start,max(0,finish-start))
   for at in range(start,finish,2048):
    if not any(raw[at-start:at-start+2048]):
     if active is None:active=at
    elif active is not None:
     if at-active>=32768:runs.append([active,at])
     active=None
   if active is not None and finish-active>=32768:runs.append([active,finish])
  self.free[name]=runs;return cs
 def alloc(self,name,b,label):
  sizes=[(hi-lo,i,lo,hi) for i,(lo,hi) in enumerate(self.free[name]) if hi-lo>=len(b)];assert sizes,('insufficient verified zero padding',name,len(b))
  _,ix,at,end=min(sizes);assert not any(read(self.f,at,len(b)));self.free[name][ix][0]=(at+len(b)+2047)&~2047;self.set(at,b,label);self.resources.append(dict(offset=at,size=len(b),label=label,sha256=hashlib.sha256(b).hexdigest()));return at
 def extend(self,root,index,a,additions,aliases=None):
  aliases=aliases or {};mapping=[65535]*a['slots'];es=[(e['offset'],e['size']) for e in a['entries']]
  for e in a['entries']:
   for k in e['keys']:mapping[k]=e['index']
  length=max([len(mapping)]+[k+1 for k,b in additions]+[k+1 for k in aliases]);mapping.extend([65535]*(length-len(mapping)))
  newdi=max(a['directory']-a['offset'],(16+length*2+2047)&~2047);prefix_end=newdi+8+(len(es)+len(additions))*8
  # Extending the face mapping can cover its old first payload. Preserve it
  # byte-for-byte elsewhere and rebase every original directory pointer.
  moved=[]
  for i,(at,n) in enumerate(es):
   if at<a['offset']+prefix_end:
    assert at>=a['directory']+8+a['count']*8;newat=self.alloc('GRAPHIC',read(self.f,at,n),'Relocated unchanged original face '+str(i));es[i]=(newat,n);moved.append(i)
  for k,b in additions:
   assert mapping[k]==65535;mapping[k]=len(es);at=self.alloc('BATTLE' if root['offset']>0x20000000 else 'GRAPHIC',b,f'Imported child{index} key{k}');es.append((at,len(b)))
  for k,target in aliases.items():assert mapping[k]==65535 and mapping[target]!=65535;mapping[k]=mapping[target]
  h=bytearray(read(self.f,a['offset'],prefix_end));struct.pack_into('<III',h,4,newdi,len(es),len(mapping));struct.pack_into('<%dH'%len(mapping),h,16,*mapping);h[newdi:newdi+8]=b'Wpbb'+struct.pack('<I',len(es))
  for i,(at,n) in enumerate(es):assert at>=a['offset']+prefix_end;struct.pack_into('<II',h,newdi+8+i*8,at-a['offset']-newdi,n)
  self.set(a['offset'],h,f'Extended child{index} mapping/directory');span=max(at+n for at,n in es)-a['offset'];self.set(root['directory']+8+index*8+4,struct.pack('<I',max(root['entries'][index]['size'],span)),f'Child{index} parent span')
  self.directory_proofs.append(dict(root=root['offset'],child=index,old_count=a['count'],new_count=len(es),old_slots=a['slots'],new_slots=len(mapping),relocated_original_entries=moved))

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('beowulf_stage_applied');DEST.mkdir(parents=True,exist_ok=True)
 from build_options import source_image
 with TARGET.open('rb') as f,OGsBeowulfImage() as source,source_image() as vanilla:
  p=Plan(f);be,br=archive(f,'BATTLE.BIN');bc=p.find_free('BATTLE',br,be);ge,gr=archive(f,'GRAPHIC.BIN');gc=p.find_free('GRAPHIC',gr,ge)
  _,sbr=archive(source,'BATTLE.BIN');sbc=children(source,sbr);_,sgr=archive(source,'GRAPHIC.BIN');sgc=children(source,sgr)
  oldrow=data(source,sbc[7],0)[BANK*144:(BANK+1)*144];oldmotions=struct.unpack_from('<70H',data(source,sbc[7],0),42*144+4);newmotions=struct.unpack_from('<70H',oldrow,4);ggmotions=struct.unpack_from('<70H',data(f,bc[7],0),42*144+4)
  assert not any(BANK in e['keys'] for e in bc[1]['entries']);p.extend(br,1,bc[1],[(BANK,data(source,sbc[1],BANK))])
  pairs={n:(o,g) for o,n,g in zip(oldmotions,newmotions,ggmotions) if n!=65535};remap={};attacks=[];equivalence=[];meta=entry(bc[8],0)
  for k,(old,gg) in sorted(pairs.items()):
   assert gg!=65535;native_source=data(source,sbc[2],old);native_target=data(f,bc[2],gg);assert u16(native_source,4)==u16(native_target,4),('incompatible animation format',old,gg)
   b=data(source,sbc[2],k)
   if b==native_target:remap[k]=gg
   else:remap[k]=bc[2]['slots']+len(attacks);attacks.append((remap[k],b));srcmeta=data(source,sbc[8],0)[k*16:(k+1)*16];assert any(srcmeta);p.set(meta['offset']+remap[k]*16,srcmeta,'Imported animation display metadata')
   equivalence.append(dict(source_key=k,native_OGs_key=old,native_OGG_key=gg,new_key=remap[k],native_programs_identical=native_source==native_target,compatible_native_format=True,reused=b==native_target,sha256=hashlib.sha256(b).hexdigest()))
  p.extend(br,2,bc[2],attacks);row=bytearray(oldrow)
  for i,k in enumerate(newmotions):
   if k!=65535:struct.pack_into('<H',row,4+i*2,remap[k])
  p.set(entry(bc[7],0)['offset']+BANK*144,row,'Private Beowulf animation bank')
  cutrow=bytearray(data(source,sbc[9],0)[223*60:224*60]);cutkeys=sorted(set(struct.unpack_from('<20H',cutrow))-{65535});cm={k:bc[3]['slots']+i for i,k in enumerate(cutkeys)};p.extend(br,3,bc[3],[(cm[k],data(source,sbc[3],k)) for k in cutkeys])
  assert data(f,bc[9],0)[FACE*60:FACE*60+40]==b'\xff'*40
  for i in range(20):
   k=u16(cutrow,i*2)
   if k!=65535:struct.pack_into('<H',cutrow,i*2,cm[k])
  p.set(entry(bc[9],0)['offset']+FACE*60,cutrow,'Private Beowulf pilot cut-in list')
  speech=bytearray(data(f,bc[5],1094));h=struct.unpack_from('<16H',speech);retagged=0
  for at in range(h[12],h[13],2):
   k=u16(speech,at)
   if k&2047==1094:struct.pack_into('<H',speech,at,(k&0xf800)|PILOT);retagged+=1
  assert retagged;p.extend(br,5,bc[5],[(PILOT,speech)])
  large=[data(source,sgc[1],223*32+i) for i in [0,1]];p.extend(gr,1,gc[1],[(FACE*32+i,b) for i,b in enumerate(large)],{FACE*32+i:FACE*32+i%2 for i in range(2,32)})
  p.extend(gr,2,gc[2],[(FACE*10,data(source,sgc[2],2230))],{FACE*10+i:FACE*10 for i in range(1,10)})
  expr=entry(gc[4],0);oldexpr=read(f,expr['offset']+58*760,760);newexpr=bytearray(oldexpr);assert not any(read(f,expr['offset']+FACE*760,760))
  for i in range(32):struct.pack_into('<H',newexpr,i*2,u16(oldexpr,(18+i%2)*2))
  p.set(expr['offset']+FACE*760,newexpr,'Beowulf scenario face expression table')
  se=next(e for e in inventory(source) if e['name']=='SHARED.BIN;1');sm=Master(read(source,se['offset']+0x11e800,0x190000-0x11e800));masters={}
  for name in ['SHARED.BIN','IM.BIN']:
   e,m=rawmaster(f,name);b,note=master_additions(m.b,sm,name=='SHARED.BIN');(DEST/(name+'.master')).write_bytes(b);p.set(e['offset'],b,name+' private Beowulf records');masters[name]=dict(offset=e['offset'],size=e['size'],file=name+'.master',**note)
  ua,us=loadarc(f,13);la,ls=loadarc(f,14)
  def get(es,k):_,at,n=next(e for e in es if k in e[0]);return read(f,at,n)
  _,terrain=loadarc(f,12);tb=read(f,terrain[0][1],terrain[0][2]);names={i:decode(tb[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);ts={k:read(f,at,n) for ks,at,n in mt for k in ks};info=next(read(f,at,n) for ks,at,n in mi if MAP_KEY in ks);t=ts[u32(info,12)];w,h=u32(t,8),u32(t,12)
  def valid(x,y):return 0<x<w and 0<y<h and names[u32(t,32+(y*w+x)*8)&65535]=='아인스트 공간'
  cells=[(x,y) for y in range(h) for x in range(w) if valid(x,y)];assert len(cells)>1000
  selection=get(us,2032);sel=next(selection[44+i*336:44+(i+1)*336] for i in range(u32(selection,40)) if u32(selection,44+i*336+8)==6)
  allies=sorted(cells,key=lambda c:abs(c[0]-w//2)+abs(c[1]-(h-7)))[:12];occupied=set(allies)
  boss=min((c for c in cells if min(abs(c[0]-x)+abs(c[1]-y) for x,y in allies)>=20),key=lambda c:abs(c[0]-w//2)+abs(c[1]-6));occupied.add(boss)
  enemies=[]
  for i in range(31):
   available=[c for c in cells if c not in occupied and min(abs(c[0]-x)+abs(c[1]-y) for x,y in allies)>=10 and min(abs(c[0]-x)+abs(c[1]-y) for x,y in occupied)>=2]
   pos=min(available,key=lambda c:abs(c[0]-(w//2+(-9 if i%2 else 9)))+abs(c[1]-(11+i%5*2)));occupied.add(pos);enemies.append(pos)
  templates={}
  for ks,at,n in us:
   b=read(f,at,n)
   if len(b)==44+u32(b,40)*336:
    for i in range(u32(b,40)):
     r=b[44+i*336:44+(i+1)*336]
     if u32(r,8)==2:templates.setdefault(u32(r),r)
  rows=[];spawn=[]
  for x,y in allies:
   r=bytearray(sel)
   for at,v in [(4,30),(12,0),(16,x),(20,y)]:struct.pack_into('<I',r,at,v)
   rows.append(r)
  for i,(model,pos) in enumerate(zip(MINIONS+[1050,UNIT],enemies+[boss])):
   r=bytearray(templates[model if model!=UNIT else 1050]);pilot=(1002 if model==1045 else 1003 if model==1046 else 1004 if model==1047 else 1005 if model==1048 else 1006 if model==1050 else PILOT);key=FIRST_MINION+i if i<30 else model;level=54 if i<30 else 55 if model==1050 else 56;grade=10 if model==UNIT else 8
   for at,v in [(0,key),(4,0),(12,0),(16,pos[0]),(20,pos[1]),(28,0),(32,pilot)]:struct.pack_into('<I',r,at,v)
   for at in range(0x38,0x50,4):struct.pack_into('<I',r,at,grade)
   for at in [0x50,0x54,0x58]:struct.pack_into('<I',r,at,level*500)
   for at in [0x60,0x74,0x88]:struct.pack_into('<I',r,at,0xffff0000|pilot)
   rows.append(r);spawn.append(dict(row=12+i,key=key,source=model,pilot=pilot,level=level,base_grade=grade-2,position=list(pos),respawns=i<30))
  un=bytearray(selection[:44]);struct.pack_into('<4I',un,8,MAP_KEY,0xffffffff,0xffffffff,0xffffffff);un[24:40]=b'2040'+bytes(12);struct.pack_into('<I',un,40,len(rows));un.extend(b''.join(rows))
  cursor=0x1af00000;limit=0x1b000000;map_resources=[]
  def allocmap(name,b):
   nonlocal cursor
   cursor=(cursor+2047)&~2047;assert cursor+len(b)<=limit and not any(read(f,cursor,len(b)));assert all(cursor+len(b)<=at or cursor>=at+n for ks,at,n in us+ls);p.set(cursor,b,name);(DEST/name).write_bytes(b);item=dict(file=name,offset=cursor,size=len(b));map_resources.append(item);cursor+=len(b);return item
  speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers'];speakers.update({'베오울프':PILOT,'알피미':1347,'레피나':1209})
  lo,note=mission_logo(get(ls,2033),speakers);untd=allocmap('2040.untd',un);logo=allocmap('2040.logo',lo);bridge=[]
  for mode in ['story','native']:
   if mode=='story':b=get(ls,2033)
   else:_,vls=loadarc(vanilla,14);_,at,n=next(e for e in vls if 2033 in e[0]);b=read(vanilla,at,n)
   route=next(i for i,r in enumerate(records(b)) if r[0]==0xa1 and r[2]==34);point=max(i for i,r in enumerate(records(b)[:route]) if r[0]==0x30)+1;new,bnote=rebuild_logo(b,point,BRIDGE,speakers,FLAG);rs=records(new);route=next(i for i,r in enumerate(rs) if r[0]==0xa1 and r[2]==34);new=bytearray(new);struct.pack_into('<I',new,u32(new,44)+route*96+8,40);item=allocmap('2033_'+mode+'.logo',new);bridge.append(dict(mode=mode,route_row=route,**item,**bnote))
  maproot=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');mr=lice(f,maproot['offset'],maproot['size'])
  for slot,a,res in [(13,ua,untd),(14,la,logo)]:
   count=a['count'];assert not any(read(f,a['directory']+8+count*8,8));assert read(f,a['offset']+16+KEY*2,2)==b'\xff\xff';p.set(a['offset']+8,struct.pack('<I',count+1),'Mission LICE count');p.set(a['offset']+16+KEY*2,struct.pack('<H',count),'Mission key2040');p.set(a['directory']+4,struct.pack('<I',count+1),'Mission Wpbb count');p.set(a['directory']+8+count*8,struct.pack('<II',res['offset']-a['directory'],res['size']),'Mission resource pointer')
  ix=next(e['index'] for e in la['entries'] if 2033 in e['keys']);item=bridge[0];p.set(la['directory']+8+ix*8,struct.pack('<II',item['offset']-la['directory'],item['size']),'Chapter35 bridge story pointer')
  edits=[]
  for i,(at,b,new,label) in enumerate(sorted(p.edits)):
   filename=f'edit_{i:03d}.bin';(DEST/filename).write_bytes(new);edits.append(dict(offset=at,size=len(new),file=filename,before_zlib_base64=pack(b),after_sha256=hashlib.sha256(new).hexdigest(),label=label))
  report=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],single_option_bit=11,option_count=12,source_pack_sha256=source.pack_sha256,source_profile_sha256=source.profile_sha256,unit=UNIT,pilot=PILOT,face=FACE,bank=BANK,map_key=MAP_KEY,dimensions=[w,h],valid_open_tiles=len(cells),title=TITLE,key=KEY,number=41,final_display_chapter=42,untd=untd,logo=logo,bridge=bridge,masters=masters,spawn=spawn,selection_slots=12,enemy_count=32,endless_minions=30,subbosses=1,bosses=1,resources=p.resources,directory_proofs=p.directory_proofs,animation_equivalence=equivalence,cutins=len(cutkeys),retagged_battle_subtitles=retagged,map_resources=map_resources,edits=edits,live_playthrough=False,extra_full_ISOs_created=0,**note)
  (ROOT/'beowulf_stage_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k in ['prepared','title','enemy_count','endless_minions','dimensions','valid_open_tiles','cutins','retagged_battle_subtitles','option_count']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
