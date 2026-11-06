"""Reorder a guarded scene without rebuilding native gameplay commands."""
import struct
from story_scripts_25 import records,text_at,wrap,encode,decode
from inspect_iso import u32

def guarded_block(blob,flag):
 rs=records(blob)
 start=next(i for i,r in enumerate(rs) if r[0]==0x93 and r[2:5]==[0x100c1,*flag])
 end=next(i for i in range(start+1,len(rs)) if rs[i][0]==0xba and rs[i][2:5]==[0x100c1,*flag])+1
 return start,end

def move_guarded(blob,flag,before_sid=None,after_sid=None):
 assert (before_sid is None)!=(after_sid is None)
 rs=records(blob);start,end=guarded_block(blob,flag);sid=before_sid if before_sid is not None else after_sid;dest=next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==sid)+(after_sid is not None)
 assert not start<=dest<=end
 assert not any(rs[i][0]==0x25 for i in range(min(start,dest),max(end,dest))), 'Do not move a scene across event-return boundaries'
 order=[i for i in range(len(rs)) if not start<=i<end];at=order.index(dest);order[at:at]=range(start,end);positions={old:new for new,old in enumerate(order)};positions[len(rs)]=len(rs)
 def target(origin,index):
  if start<=origin<end and index==end:return at+end-start
  if not start<=origin<end and start<=index<end:
   assert index==start,('native jump into scene body',origin,index)
   return positions[end]
  return positions[index]
 out=[]
 for i in order:
  r=rs[i].copy()
  if r[0] in [0x90,0x91]:
   for j in ([6,7] if r[0]==0x90 else [7]):
    if r[j]<0x80000000:r[j]=(target(i,i+r[j])-positions[i])&0xffffffff
  out.append(r)
 b=bytearray(blob);co=u32(b,44);b[co:co+len(out)*96]=b''.join(struct.pack('<24I',*r) for r in out)
 ds=[struct.unpack_from('<4I',blob,u32(blob,52)+i*16) for i in range(u32(blob,48))];kinds={ds[r[2]][0] for r in rs if r[0]==0x2f and r[2]<len(ds)}-{0};assert len(kinds)==1
 for i,d in enumerate(ds):
  if d[0] in kinds:struct.pack_into('<I',b,u32(b,52)+i*16+8,target(-1,d[2]))
 prefix=u32(b,32)
 for i in range(u32(b,56)):
  p=u32(b,60)+i*4;v=u32(b,p)
  if v>=prefix:struct.pack_into('<I',b,p,prefix+positions[v-prefix])
 # Every native record survives; only relative branch operands can change.
 for i,r in enumerate(rs):
  x=out[positions[i]];ignore=[6,7] if r[0]==0x90 else [7] if r[0]==0x91 else []
  assert all(r[j]==x[j] for j in range(24) if j not in ignore)
 return bytes(b),{'old_range':[start,end],'new_range':[at,at+end-start],'before_sid':before_sid,'after_sid':after_sid,'row_permutation':order}

def normalized(s):return s.replace('　',' ').replace('@',' ')

def replace_string(blob,sid,text):
 raw=encode(text);old=text_at(blob,sid);assert decode(raw)==text
 assert len(raw)<128,(sid,len(raw));assert len(raw)<=len(old),('box budget',sid,len(raw),len(old),text)
 pool=u32(blob,76);p=pool+u32(blob,u32(blob,68)+sid*4);b=bytearray(blob)
 for k in range(u32(blob,64)+u32(blob,80)):
  if k!=sid:assert pool+u32(blob,u32(blob,68)+k*4)!=p,('aliased string',sid,k)
 b[p:p+len(old)+1]=raw+b'\0'*(len(old)+1-len(raw))
 assert text_at(b,sid)==raw
 return bytes(b),{'string_id':sid,'before_bytes':len(old),'after_bytes':len(raw),'text':text}

def replace_box(blob,who,needle,new,speaker_key):
 found=[r for r in records(blob) if r[0]==0x30 and r[4]==speaker_key and needle in normalized(decode(text_at(blob,r[2])))]
 assert len(found)==1,(who,needle,len(found));parts=wrap(who,new);assert len(parts)==1,(who,new,parts)
 return replace_string(blob,found[0][2],parts[0])
