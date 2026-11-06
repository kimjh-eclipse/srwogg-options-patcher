"""Guaranteed native hidden rewards and the requested chapter-three supplies."""
from story_scripts_25 import *

EARLY=[(0x64,3513,'시시오 블레이드'),(0x64,3530,'부스트 해머'),
       (0x60,33,'강철의 혼'),(0x60,32,'용자의 인'),(0x60,31,'고성능 전자두뇌'),
       (0x60,35,'메가 제네레이터'),(0x60,1,'부스터'),(0x60,2,'메가 부스터')]

def insert_commands(old,point,added):
 rs=records(old);co=u32(old,44);prefix=u32(old,32);amount=len(added)
 ds=[struct.unpack_from('<4I',old,u32(old,52)+i*16) for i in range(u32(old,48))]
 kinds={ds[r[2]][0] for r in rs if r[0]==0x2f and r[2]<len(ds)}-{0};assert len(kinds)==1
 def moved(i):return i+amount if i>=point else i
 out=[]
 for i,r in enumerate(rs):
  if i==point:out.extend(added)
  r=r.copy()
  if r[0] in [0x90,0x91]:
   for j in ([6,7] if r[0]==0x90 else [7]):
    if r[j]<0x80000000:r[j]=moved(i+r[j])-moved(i)
  out.append(r)
 end=co+len(rs)*96;extra=amount*96
 b=bytearray(old[:co])+bytearray(b''.join(struct.pack('<24I',*r) for r in out))+bytearray(old[end:])
 struct.pack_into('<I',b,40,len(out))
 for p in [52,60,68,76,84,92]:assert u32(old,p)>=end;struct.pack_into('<I',b,p,u32(old,p)+extra)
 for i,d in enumerate(ds):
  if d[0] in kinds:struct.pack_into('<I',b,u32(b,52)+i*16+8,moved(d[2]))
 for i in range(u32(old,56)):
  p=u32(old,60)+i*4;v=u32(old,p);struct.pack_into('<I',b,u32(b,60)+i*4,prefix+moved(v-prefix) if v>=prefix else v)
 for p in [4,108]:struct.pack_into('<I',b,p,len(b))
 # Every old record and every old string survives, apart from jump relocation.
 check=records(b)
 for i,r in enumerate(rs):
  row=check[moved(i)];ignore=[6,7] if r[0]==0x90 else [7] if r[0]==0x91 else []
  assert all(row[j]==r[j] for j in range(24) if j not in ignore)
 for i in range(u32(old,64)+u32(old,80)-1):assert text_at(b,i)==text_at(old,i)
 return bytes(b)

def hidden_plan(target):
 edits=[];notes={'early_items':[n for op,key,n in EARLY],'conditions_removed':[],'scripts':[]};cursor=0x1b400000
 speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers']
 with target.open('rb') as f:
  a,entries=loadarc(f,14);blobs={ks[0]:(p,read(f,p,n)) for ks,p,n in entries}
  # Fixed-sized changes preserve original reward events, messages and schedules.
  removes={2005:[(745,0x2b,'6화 고성능 전자두뇌 위치 조건')],
           2023:[(750,0x91,'25화 시시오 블레이드 레벨 합계'),(757,0x91,'25화 용자의 인 레벨 합계')],
           2028:[(722,0x91,'30화 부스트 해머 격추수'),(729,0x91,'30화 강철의 혼 레벨'),(733,0x91,'30화 강철의 혼 격추수')]}
  for key,changes in removes.items():
   p,old=blobs[key];b=bytearray(old);rs=records(old)
   for index,op,label in changes:
    assert rs[index][0]==op,(key,index,rs[index][0]);off=u32(old,44)+index*96
    new=struct.pack('<24I',*command(0x8a));edits.append((p+off,old[off:off+96],new,label));notes['conditions_removed'].append(label)
  def relocate(key,blob,label):
   nonlocal cursor
   cursor=(cursor+2047)&~2047;assert cursor+len(blob)<=0x1b594000
   before=read(f,cursor,len(blob));assert not any(before)
   e=next(e for e in a['entries'] if key in e['keys']);dp=a['directory']+8+e['index']*8
   edits.extend([(cursor,before,blob,label),(dp,read(f,dp,8),struct.pack('<II',cursor-a['directory'],len(blob)),label+' directory')])
   (OUT/f'bonus_{key}.logo').write_bytes(blob);notes['scripts'].append(dict(key=key,offset=cursor,size=len(blob)));cursor+=len(blob)
  p,old=blobs[2003];rs=records(old)
  point=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,60,0])
  lines=[('카이','보급품을 인계한다. 시시오 블레이드와 부스트 해머는 각 한 개다.'),
         ('카이','강철의 혼, 용자의 인, 고성능 전자두뇌도 한 개씩 지급한다.'),
         ('카이','메가 제네레이터와 부스터, 메가 부스터도 각각 하나다. 정비할 때 활용해라.')]
  new,n=rebuild_logo(old,point,lines,speakers,(63,7));rows=records(new)
  stop=next(i for i,r in enumerate(rows) if r[0]==0xba and r[2:5]==[0x100c1,63,7])
  new=insert_commands(new,stop,[command(op,key,0) for op,key,name in EARLY]);relocate(2003,new,'chapter 3 eight supplies once')
  notes['early_block']=dict(start=point,flag=[63,7],items=[dict(op=op,key=key,name=name) for op,key,name in EARLY],messages=n['messages'])
  # Ground route: keep the existing recovery conversation and set its result.
  p,old=blobs[2012];b=bytearray(old);rs=records(old)
  assert rs[872][0]==0x93 and rs[872][2:5]==[0x100c1,57,3] and rs[898][0]==0x91
  for idx,row in [(872,command(0xba,0x100c1,57,3)),(898,command(0x8a))]:struct.pack_into('<24I',b,u32(b,44)+idx*96,*row)
  # Its native grant is idempotent if later original acquisition code also runs.
  new=insert_commands(b,980,[command(0x5f,1410,NONE,NONE,NONE)]);relocate(2012,new,'ground chapter 13 Mironga guaranteed')
  p,old=blobs[2054]
  new,n=rebuild_logo(old,890,[('카이','지상 부대에서 미롱가를 회수했다. 수송편으로 넘길 테니 기체 목록을 확인해라.')],speakers,(63,6))
  stop=next(i for i,r in enumerate(records(new)) if r[0]==0xba and r[2:5]==[0x100c1,63,6])
  new=insert_commands(new,stop,[command(0xba,0x100c1,57,3),command(0x5f,1410,NONE,NONE,NONE)]);relocate(2054,new,'space chapter 13 Mironga guaranteed')
  notes['space_messages']=n['messages'];notes['mironga_key']=1410;notes['mironga_flag']=[57,3]
  dp=0x11a94800+8+14*8+4;old=read(f,dp,4);new=struct.pack('<I',max(u32(old),cursor-a['directory']))
  if old!=new:edits.append((dp,old,new,'MAP script archive span'))
 edits.sort();return edits,notes

def enemy_upgrade_plan(target):
 edits=[];notes=[]
 with target.open('rb') as f:
  _,es=loadarc(f,13)
  for ks,p,n in es:
   if not any(2001<=k<=2070 for k in ks):continue
   old=read(f,p,n);assert len(old)==44+336*u32(old,40)
   changed=0
   for i in range(u32(old,40)):
    pos=44+i*336
    if u32(old,pos+8) not in [2,3,4]:continue
    before=old[pos+0x38:pos+0x50];values=struct.unpack('<6I',before)
    assert all(v<=15 for v in values),(ks,i,values)
    after=struct.pack('<6I',*(min(v+2,15) for v in values))
    if before!=after:edits.append((p+pos+0x38,before,after,f'enemy spawn +2: {ks[0]} row {i}'));changed+=1
   if changed:notes.append(dict(keys=ks,enemy_rows=changed))
 return edits,notes
