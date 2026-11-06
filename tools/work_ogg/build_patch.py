"""Guarded OG Gaiden Korean patch builder. Source ISO is always read-only."""
from catalog import Master,u16
from inspect_iso import *
import argparse,shutil,os

EXPECTED='a9f7f03c4cb722f9e0709860a1cf5a16fc52d8bf116a9458403ffc5a67fd7f63'
DEAD=0xdeaddead
UNIT=PILOT=0x700
GROUP=32
def put(b,p,v):struct.pack_into('<I',b,p,v)
def arc(name):return json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
def command(op,*args):return [op,DEAD,*args]+[DEAD]*(22-len(args))

class Plan:
 def __init__(self,f):self.f=f;self.edits=[]
 def add(self,at,new,label):
  old=read(self.f,at,len(new))
  if old!=new:self.edits.append((at,old,bytes(new),label))
 def empty(self,at,new,label):
  assert not any(read(self.f,at,len(new))),label
  self.add(at,new,label)
 def validate(self):
  self.edits.sort()
  for a,b in zip(self.edits,self.edits[1:]):assert a[0]+len(a[1])<=b[0],(a[3],b[3])

def master_patch(old,cost):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 # Preserve the full string area and its padding; grow the containing child.
 parts={k:bytearray(old[p:(starts[i+1] if i+1<len(starts) else len(old))]) for i,(k,p) in enumerate(zip(fields,starts))}
 details={}
 for table,lookup,key,source,stride in [(0x1c,0x18,UNIT,0x23,100),(0x2c,0x28,PILOT,0x3e,148)]:
  t,l=parts[table],parts[lookup];count=u32(t,8);src=u16(l,12+source*2)
  assert u16(l,12+key*2)==65535 and src<count
  row=bytearray(t[12+src*stride:12+(src+1)*stride])
  if table==0x1c:
   assert u32(row)==160000
   put(row,0,8300);struct.pack_into('<HH',row,0x18,250,2100);struct.pack_into('<H',row,0x22,1)
  t.extend(row);put(t,4,u32(t,4)+stride);put(t,8,count+1);put(l,4,u32(l,4)+stride)
  struct.pack_into('<H',l,12+key*2,count)
  details['unit' if table==0x1c else 'pilot']=dict(source_key=source,new_key=key,source_index=src,new_index=count)
 if cost is not None:
  t=parts[0x2c]
  for i in range(u32(t,8)):
   p=12+i*148
   for rel in [*range(0x72,0x78),0x7f]:
    if t[p+rel]>0:t[p+rel]=cost
 new=bytearray(old[:starts[0]])
 for k in fields:put(new,k,len(new));new.extend(parts[k])
 # All original units and weapon records must survive exactly.
 n=Master(new)
 for tag in ['Unit','Weap']:
  a=m.tables[tag][0];b=n.tables[tag][0];stride=100 if tag=='Unit' else 36;count=m.tables[tag][2]
  assert old[a+12:a+12+count*stride]==new[b+12:b+12+count*stride]
 for i in range(m.tables['Plot'][2]):
  a=m.tables['Plot'][0]+12+i*148;b=n.tables['Plot'][0]+12+i*148
  allowed=set([*range(0x72,0x78),0x7f]) if cost is not None else set()
  assert {j for j in range(148) if old[a+j]!=new[b+j]}<=allowed
 # Existing text pointers and text bytes are unchanged, merely relocated.
 for tag in ['Strg','Expl','Sent']:
  a=m.tables[tag][0];b=n.tables[tag][0];idx=starts.index(a);end=starts[idx+1] if idx+1<len(starts) else len(old)
  assert old[a:end]==new[b:b+end-a]
 return bytes(new),details

def insert_commands(old,point,added):
 count,co,prefix=u32(old,0x28),u32(old,0x2c),u32(old,0x20)
 rows=[list(struct.unpack_from('<24I',old,co+i*96)) for i in range(count)]
 def moved(i):return i+len(added) if i>=point else i
 newrows=[]
 for i,r in enumerate(rows):
  if i==point:newrows.extend(added)
  if r[0] in (0x90,0x91):
   for j in ((6,7) if r[0]==0x90 else (7,)):
    if r[j]<0x80000000:r[j]=moved(i+r[j])-moved(i)
  newrows.append(r)
 delta=len(added)*96;end=co+count*96
 b=bytearray(old[:co])+bytearray(b''.join(struct.pack('<24I',*r) for r in newrows))+bytearray(old[end:])
 put(b,0x28,len(newrows))
 for k in (0x34,0x3c,0x44,0x4c,0x54,0x5c):
  assert u32(old,k)>=end;put(b,k,u32(old,k)+delta)
 for i in range(u32(b,0x30)):
  p=u32(b,0x34)+i*16
  if u32(b,p):put(b,p+8,moved(u32(b,p+8)))
 for i in range(u32(b,0x38)):
  p=u32(b,0x3c)+i*4;v=u32(b,p)
  if v>=prefix:put(b,p,prefix+moved(v-prefix))
 put(b,4,len(b));put(b,0x6c,len(b))
 # Independently verify every control-flow target still refers to the same original row.
 for i in range(count):
  oldrow=struct.unpack_from('<24I',old,co+i*96);newrow=newrows[moved(i)]
  assert newrow[0]==oldrow[0]
  for j in ((6,7) if oldrow[0]==0x90 else (7,) if oldrow[0]==0x91 else ()):
   if oldrow[j]<0x80000000:assert moved(i)+newrow[j]==moved(i+oldrow[j])
 return bytes(b)

def make_plan(f,stage,cost):
 p=Plan(f);detail={};inventory_data=json.loads((OUT/'iso_inventory.json').read_text(encoding='utf-8'))
 for name in ['SHARED.BIN','IM.BIN']:
  root=arc(name);outer=root['entries'][3];nested=arc(name+'.3');e=nested['entries'][0]
  old=read(f,e['offset'],e['size']);new,note=master_patch(old,cost)
  assert e['offset']+len(new)<=outer['offset']+outer['size']
  assert not any(read(f,e['offset']+len(old),len(new)-len(old)))
  p.add(e['offset'],new,name+' unit/pilot clone and optional SP cost')
  p.add(nested['directory']+12,struct.pack('<I',len(new)),name+' master payload length');detail[name]=note
 # Duplicate the original voice data and retag its internal pilot references.
 root=arc('BATTLE.BIN');a=arc('BATTLE.BIN.5');e=next(e for e in a['entries'] if 0x3e in e['keys']);voice=bytearray(read(f,e['offset'],e['size']))
 h=struct.unpack_from('<16H',voice);retagged=0
 for o in range(h[12],h[13],2):
  v=u16(voice,o)
  if v&0x7ff==0x3e:struct.pack_into('<H',voice,o,(v&0xf800)|PILOT);retagged+=1
 assert retagged
 at=0x99000000;file=next(x for x in inventory_data['files'] if x['name']=='BATTLE.BIN;1')
 assert at+len(voice)<=file['offset']+file['size'];p.empty(at,voice,'cloned Ingram voice')
 mapping=list(struct.unpack('<%dH'%a['slots'],read(f,a['offset']+16,a['slots']*2)))
 mapping.extend([65535]*(PILOT+1-len(mapping)));assert mapping[PILOT]==65535;mapping[PILOT]=a['count']
 assert 16+len(mapping)*2<=a['directory']-a['offset']
 d=b'Wpbb'+struct.pack('<I',a['count']+1)+b''.join(struct.pack('<II',e['offset']-a['directory'],e['size']) for e in a['entries'])+struct.pack('<II',at-a['directory'],len(voice))
 assert a['directory']+len(d)<=min(e['offset'] for e in a['entries'])
 p.add(a['offset']+8,struct.pack('<II',a['count']+1,len(mapping)),'voice archive counts')
 p.add(a['offset']+16,struct.pack('<%dH'%len(mapping),*mapping),'voice raw-key map')
 p.add(a['directory'],d,'voice archive directory')
 p.add(root['directory']+8+5*8+4,struct.pack('<I',at+len(voice)-a['offset']),'voice archive span')
 # A native ally template supplies all flags not explicitly changed here.
 a=arc('MAP.BIN.13');e=next(e for e in a['entries'] if stage in e['keys']);old=read(f,e['offset'],e['size']);count=u32(old,40)
 rows=[old[44+i*336:44+(i+1)*336] for i in range(count)];assert all(u32(r,4)!=GROUP for r in rows)
 template=next(r for r in rows if u32(r,8)==0 and u32(r,28)==1 and u32(r,32)!=0xffff)
 row=bytearray(template);occupied={(u32(r,16),u32(r,20)) for r in rows};xy=(15,32) if stage==2001 else (u32(template,16)+1,u32(template,20))
 while xy in occupied:xy=(xy[0]+1,xy[1])
 for o,v in [(0,UNIT),(4,GROUP),(8,0),(16,xy[0]),(20,xy[1]),(28,1),(32,PILOT),(0x38,0),(0x3c,0),(0x40,0)]:put(row,o,v)
 for o in (0x60,0x74,0x88):put(row,o,0xffff0000|PILOT)
 new=bytearray(old+row);put(new,40,count+1);dest=0x1b000000
 p.empty(dest,new,'scenario ally roster')
 p.add(a['directory']+8+e['index']*8,struct.pack('<II',dest-a['directory'],len(new)),'scenario roster entry')
 maproot=arc('MAP.BIN');p.add(maproot['directory']+8+13*8+4,struct.pack('<I',dest+len(new)-a['offset']),'roster archive span')
 a=arc('MAP.BIN.14');e=next(e for e in a['entries'] if stage in e['keys']);old=read(f,e['offset'],e['size'])
 # Test spawn immediately after native ally deployment. Production uses the same native mechanism.
 co=u32(old,0x2c);point=next(i+1 for i in range(u32(old,0x28)) if u32(old,co+i*96)==0xca and u32(old,co+i*96+8)==0)
 new=insert_commands(old,point,[command(0xca,GROUP,0xffffffff)]);dest=0x1b020000
 p.empty(dest,new,'scenario recruitment command')
 p.add(a['directory']+8+e['index']*8,struct.pack('<II',dest-a['directory'],len(new)),'scenario script entry')
 p.add(maproot['directory']+8+14*8+4,struct.pack('<I',dest+len(new)-a['offset']),'script archive span')
 p.validate();detail.update(stage=stage,insert_before=point,position=xy,voice_retagged=retagged,SP_cost=cost,live_verified=False)
 return p,detail

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',type=int,default=2001);ap.add_argument('--sp-cost',type=int,choices=[1,5]);ap.add_argument('--write',action='store_true');args=ap.parse_args()
 target=ROOT/('SRWOGG_INGRAM_TEST.iso' if args.stage==2001 else 'SRWOGG_INGRAM_CH6.iso')
 with SOURCE.open('rb') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==EXPECTED,'Different source ISO'
  p,detail=make_plan(f,args.stage,args.sp_cost)
 report=dict(source=str(SOURCE),source_sha256=EXPECTED,target=str(target),details=detail,edits=[dict(offset=o,before=a.hex(),after=b.hex(),label=label) for o,a,b,label in p.edits])
 if args.write:
  assert not target.exists(),'Output already exists; choose a new filename'
  shutil.copyfile(SOURCE,target)
  with target.open('r+b') as f:
   for o,a,b,label in p.edits:
    assert read(f,o,len(a))==a;f.seek(o);f.write(b)
   f.flush();os.fsync(f.fileno())
  # Restore every edited range in the hash stream to prove all unrelated bytes are intact.
  h=hashlib.sha256();inverse=hashlib.sha256();pos=0
  with target.open('rb') as f:
   for o,a,b,label in p.edits:
    while pos<o:
     raw=f.read(min(4<<20,o-pos));h.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;h.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(4<<20):h.update(raw);inverse.update(raw)
  assert inverse.hexdigest()==EXPECTED;report.update(target_sha256=h.hexdigest(),all_other_bytes_preserved=True)
 (ROOT/('manifest_test.json' if args.stage==2001 else 'manifest_ch6.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='edits'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
