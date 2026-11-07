"""Prepare five real native stages and prerequisite intermission insertions."""
from pathlib import Path
import sys,json,struct,hashlib,base64,zlib
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT/('option_intermission' if (ROOT/'option_intermission').exists() else 'option_release'))]
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32,inventory,lice
from build_options import rawmaster
from catalog import Master,u16,decode
from story_scripts_25 import records,command
from intermission_six_policy import extend
from civil_war_content import SCENES,POLITICAL,PROLOGUE_AFTER
from civil_war_policy import *
DEST=ROOT/'analysis/civil_war'

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('civil_war_applied');audit=json.loads((ROOT/'civil_war_audit.json').read_text(encoding='utf8'));members=audit['members'];DEST.mkdir(exist_ok=True)
 combat=[n for n,x in members.items() if x['unit'] and x['team'] in [GUARD,INFIL,REBELS]];assert len(combat)==32;private={n:1961+i for i,n in enumerate(combat)}
 speakers=audit['speakers'].copy();speakers.update({n:x['pilot'] for n,x in members.items()});speakers.update({'위원회 연락관':1994,'정치 세력 연락관':1994,'경비 참모장':1995,'경비 참모부':1995,'감찰관':1996})
 gaps=[list(g) for g in audit['zero_map_gaps']];edits=[];scenes=[];bridges=[]
 with TARGET.open('rb') as f:
  entries=inventory(f);mapfile=next(e for e in entries if e['name']=='MAP.BIN;1');outer=lice(f,mapfile['offset'],mapfile['size']);ua,us=loadarc(f,13);la,ls=loadarc(f,14);_,original=rawmaster(f,'SHARED.BIN')
  def get(es,key):
   _,at,n=next(e for e in es if key in e[0]);return read(f,at,n)
  def edit(at,b,label):
   a=read(f,at,len(b));file='edit_%03d.bin'%len(edits);(DEST/file).write_bytes(b);edits.append(dict(offset=at,size=len(b),file=file,label=label,before_zlib_base64=base64.b64encode(zlib.compress(a,9)).decode('ascii'),after_sha256=hashlib.sha256(b).hexdigest()))
  def alloc(file,b):
   for gap in gaps:
    at=(gap[0]+2047)&~2047
    if at+len(b)<=gap[1]:break
   else:raise AssertionError(('no zero MAP space',len(b)))
   assert not any(read(f,at,len(b)));gap[0]=(at+len(b)+2047)&~2047;(DEST/file).write_bytes(b);edit(at,b,file);return dict(file=file,offset=at,size=len(b))
  masterblob,mnote=master(original.b,members,private);(DEST/'SHARED.BIN.master').write_bytes(masterblob);me,_=rawmaster(f,'SHARED.BIN');edit(me['offset'],masterblob,'Private civil-war bodies/pilots and titles')
  # IM also needs the same independent identities during preparation.
  im_e,im_m=rawmaster(f,'IM.BIN');im_blob,imnote=master(im_m.b,members,private,original);(DEST/'IM.BIN.master').write_bytes(im_blob);edit(im_e['offset'],im_blob,'Preparation identities and faction copies')
  vm_master=Master(masterblob)
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);_,ter=loadarc(f,12);tdata=read(f,ter[0][1],ter[0][2]);terrain={i:decode(tdata[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  tilekeys={k:read(f,at,n) for ks,at,n in mt for k in ks};tiles={}
  for ks,at,n in mi:
   info=read(f,at,n)
   if u32(info,12) in tilekeys:
    for k in ks:tiles[k]=tilekeys[u32(info,12)]
  selection=get(us,2035)[44:44+336];enemy=get(us,2035)[44+12*336:44+13*336];template=get(ls,2040)
  for i,s in enumerate(SCENES):
   source=get(us,s['map_from']);mk=u32(source,8);tile=tiles[mk];w,h=u32(tile,8),u32(tile,12)
   def valid(x,y):
    name=terrain.get(u32(tile,32+(y*w+x)*8)&65535,'');return name not in ['','영역 밖'] and not any(t in name for t in ['바다','수중','호수'])
   cells=[(x,y) for y in range(1,h-1) for x in range(1,w-1) if valid(x,y)];assert len(cells)>=60
   ally=sorted(cells,key=lambda c:abs(c[0]-w//2)+abs(c[1]-(h-5)))[:12];hp=min((c for c in cells if c not in ally),key=lambda c:abs(c[0]-(w//2-4))+abs(c[1]-(h-4)))
   ec=sorted((c for c in cells if c not in ally and c!=hp and min(abs(c[0]-x)+abs(c[1]-y) for x,y in ally)>=8),key=lambda c:abs(c[0]-w//2)+abs(c[1]-5));assert len(ec)>=32
   guards=[n for n in combat if members[n]['team']==GUARD];spies=[n for n in combat if members[n]['team']==INFIL];rebels=[n for n in combat if members[n]['team']==REBELS]
   names=rebels if s['key']==2045 else guards+(spies if s['key'] in [2042,2043] else [])
   target=([private[n] for n in rebels] if s['key']==2045 else RELAY_KEYS[:3 if s['key']==2043 else 2]);keys=[private[n] for n in names]+([] if s['key']==2045 else target)
   keys+=ORDINARY_KEYS[:32-len(keys)];assert len(keys)==32 and len(set(keys))==32
   rows=[];spawn=[]
   for x,y in ally:
    row=bytearray(selection)
    for at,v in [(4,30),(12,0),(16,x),(20,y)]:struct.pack_into('<I',row,at,v)
    rows.append(row)
   for j,(key,(x,y)) in enumerate(zip(keys,ec)):
    row=bytearray(enemy);who=next((n for n,k in private.items() if k==key),None);pk=key if who else 1029
    for at,v in [(0,key),(4,0),(8,2),(12,0),(16,x),(20,y),(28,0),(32,pk)]:struct.pack_into('<I',row,at,v)
    for at in [36,40,44]:struct.pack_into('<I',row,at,0xffffffff)
    for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,8)
    for at in [0x50,0x54,0x58]:struct.pack_into('<I',row,at,(54+i)*500)
    for at in [0x60,0x74,0x88]:struct.pack_into('<I',row,at,0xffff0000|pk)
    rows.append(row);spawn.append(dict(row=len(rows)-1,key=key,pilot=pk,who=who,base_grade=6,position=[x,y]))
   row=bytearray(enemy)
   for at,v in [(0,HOSTAGE_KEY),(4,1),(8,1),(12,0),(16,hp[0]),(20,hp[1]),(28,0),(32,1993)]:struct.pack_into('<I',row,at,v)
   for at in [36,40,44]:struct.pack_into('<I',row,at,0xffffffff)
   for at in [0x60,0x74,0x88]:struct.pack_into('<I',row,at,0xffff0000|1993)
   for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,6)
   rows.append(row)
   ub=bytearray(source[:44]);struct.pack_into('<4I',ub,8,mk,0xffffffff,0xffffffff,0xffffffff);ub[24:40]=str(s['key']).encode('ascii')+bytes(12);struct.pack_into('<I',ub,40,len(rows));ub.extend(b''.join(rows));un=alloc(str(s['key'])+'.untd',ub)
   lo,note=mission(template,s,members,speakers,private,mk,target,s['key']-1999 if i<4 else 34);logo=alloc(str(s['key'])+'.logo',lo);scenes.append(dict(key=s['key'],number=s['number'],title=s['title'],map_key=mk,dimensions=[w,h],untd=un,logo=logo,spawn=spawn,hostage_position=list(hp),**note))
  # Prerequisites are spread through the existing optional campaign, not dumped at one battle.
  for key,part in PROLOGUE_AFTER.items():
   old=get(ls,key);segs=segments(POLITICAL[part],members)
   if key==2040:
    extra=[command(0x4a,0x100a8,x['pilot'],0) for x in members.values() if x['team'] in [GUARD,REBELS] and x['pilot'] is not None];extra+=[command(0xba,0x100c1,36,0)];segs.append(('commands',extra))
   new,note=extend(old,{'post':segs},speakers);new=bytearray(new);rs=records(new)
   route=next(i for i,r in enumerate(rs) if r[0]==0xa1 and r[2]!=0xffffffff)
   if key==2040:struct.pack_into('<I',new,u32(new,44)+route*96+8,41)
   lo=alloc(str(key)+'_political.logo',new);ix=next(e['index'] for e in la['entries'] if key in e['keys']);edit(la['directory']+8+ix*8,struct.pack('<II',lo['offset']-la['directory'],lo['size']),'Political bridge '+str(key));bridges.append(dict(key=key,logo=lo,route_row=route,**note))
  for slot,arc,kind in [(13,ua,'untd'),(14,la,'logo')]:
   count=arc['count'];assert not any(read(f,arc['directory']+8+count*8,5*8))
   edit(arc['offset']+8,struct.pack('<I',count+5),'LICE count '+str(slot));edit(arc['directory']+4,struct.pack('<I',count+5),'Wpbb count '+str(slot))
   for i,s in enumerate(scenes):
    k=s['key'];r=s[kind];assert read(f,arc['offset']+16+k*2,2)==b'\xff\xff';edit(arc['offset']+16+k*2,struct.pack('<H',count+i),kind+' key '+str(k));edit(arc['directory']+8+(count+i)*8,struct.pack('<II',r['offset']-arc['directory'],r['size']),kind+' pointer '+str(k))
   end=max([at+n for ks,at,n in (us if slot==13 else ls)]+[s[kind]['offset']+s[kind]['size'] for s in scenes]+([b['logo']['offset']+b['logo']['size'] for b in bridges] if slot==14 else []));parent=outer['entries'][slot];span=max(parent['size'],end-parent['offset']);edit(outer['directory']+8+slot*8+4,struct.pack('<I',span),'MAP parent span '+str(slot))
  # Alias the existing voices. Same face/name/recording, independent battle pilot identity.
  battle=next(e for e in entries if e['name']=='BATTLE.BIN;1');root=lice(f,battle['offset'],battle['size']);ch=root['entries'][5];speech=lice(f,ch['offset'],ch['size'])
  from prepare_beowulf_stage import Plan as ResourcePlan
  vp=ResourcePlan(f);vp.find_free('BATTLE',root,battle);additions=[];retagged=0
  for who,newkey in list(private.items())+[(None,k) for k in [1993,1994,1995,1996]]:
   source=members[who]['pilot'] if who else 1029;entry=next(e for e in speech['entries'] if source in e['keys']);blob=bytearray(read(f,entry['offset'],entry['size']));h=struct.unpack_from('<16H',blob)
   for at in range(h[12],h[13],2):
    word=u16(blob,at)
    if word&2047==source:struct.pack_into('<H',blob,at,(word&0xf800)|newkey);retagged+=1
   additions.append((newkey,blob))
  vp.extend(root,5,speech,additions);assert not vp.directory_proofs[0]['relocated_original_entries']
  for at,old,new,label in vp.edits:edit(at,new,label)
  for who,pk in speakers.items():
   if who in members or who in ['위원회 연락관','정치 세력 연락관','경비 참모장','경비 참모부','감찰관']:assert u16(masterblob,vm_master.tables['PTbl'][0]+12+pk*2)!=65535,who
 result=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],scenes=scenes,bridges=bridges,edits=edits,private=private,members=members,speakers=speakers,master=mnote,retagged_voice_speakers=retagged,option_count=12,new_battles=5,total_extra_battles=11,final_display_chapter=47,automatic_encounter_pairs=sum(len(s['pairs']) for s in scenes),new_dialogue_boxes=sum(len(s['messages']) for s in scenes)+sum(len(s['messages']) for s in bridges))
 (ROOT/'civil_war_prepared.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['scenes','bridges','edits','members','speakers','master','private']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
