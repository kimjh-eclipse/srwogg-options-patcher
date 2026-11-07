"""Insert ordered ship communications around native selection/result commands.

No gameplay commands are replaced. Existing branches, descriptors and dialogue
history are relocated; the 1st option controls only new-story segments.
"""
import struct
from story_scripts_25 import records,text_at,wrap,encode,NONE,DEAD,command
from inspect_iso import u32

def extend(old,content,speakers):
 rs=records(old);prefix=u32(old,32);nc=u32(old,64);kc=u32(old,80);hc=u32(old,56)
 descriptors=[list(struct.unpack_from('<4I',old,u32(old,52)+16*i)) for i in range(u32(old,48))]
 funcs={}
 for i,d in enumerate(descriptors):
  if d[0]==1 and d[2]<len(rs):funcs[d[2]]=i
 def function_at(i):return max(x for x in funcs if x<=i)
 pre=next(i for i,r in enumerate(rs) if r[0]==0xca)
 post=next(i for i,r in enumerate(rs) if r[0]==0xa1 and r[2]!=0xffffffff)
 # The report callback is the one-time scene2 function containing old dialogue.
 report=next(start for start in sorted(funcs) if any(r[0]==0x79 and r[2:4]==[0x10018,2] for r in rs[start:start+4]) and any(r[0]==0x30 for r in rs[start:next((j for j in sorted(funcs) if j>start),len(rs))]))
 mid=next(i for i in range(report,len(rs)) if rs[i][0]==0x7b)
 assert function_at(pre)!=function_at(post)!=report
 template=next(r.copy() for r in rs if r[0]==0x30 and r[13]==0x100a8 and r[3]==NONE)
 strings=[];messages=[];blocks={};notes={}
 for phase,point in [('pre',pre),('tactical',mid),('post',post)]:
  added=[];gates=[]
  if phase=='pre':added.append(command(0xaf,60,0x10012))
  for kind,lines in content[phase]:
   assert kind in ['common','story']
   if kind=='story':
    added.append(command(0x9a,0,0x800e));gate=len(added);added.append(command(0x91,0x800e,0x8000,0,DEAD,DEAD,0));gates.append(gate)
   for who,text in lines:
    for wrapped in wrap(who,text):
     r=template.copy();r[1]=hc+len(messages);r[2]=nc+kc-1+len(strings);r[4]=speakers[who];r[5]=0
     strings.append(encode(wrapped));messages.append(dict(phase=phase,kind=kind,who=who,text=wrapped,sid=r[2],label=r[1]));added.append(r)
   if kind=='story':added[gate][7]=len(added)-gate
  added.append(command(0x7b,0x100ef,0x10086,0x10041))
  if phase=='pre':added.append(command(0xb0,1,0x10012))
  blocks[point]=added;notes[phase]=dict(before_old_row=point,gates=gates,lines=sum(len(lines) for _,lines in content[phase]))
 out=[];positions={};starts={}
 for i,r in enumerate(rs):
  starts[i]=len(out)
  if i in blocks:out+=blocks[i]
  positions[i]=len(out);out.append(r.copy())
 starts[len(rs)]=positions[len(rs)]=len(out)
 for i,r in enumerate(rs):
  x=out[positions[i]]
  if r[0] in [0x90,0x91]:
   for k in ([6,7] if r[0]==0x90 else [7]):
    if r[k]<0x80000000:
     assert i+r[k]<=len(rs);x[k]=(starts[i+r[k]]-positions[i])&0xffffffff
 gates=[]
 for phase,note in notes.items():
  start=starts[note['before_old_row']];note['start']=start;note['end']=positions[note['before_old_row']]
  note['gates']=[start+i for i in note['gates']];gates+=note['gates']
 for d in descriptors:
  if d[0]==1:d[2]=starts[d[2]]
 history=[u32(old,u32(old,60)+i*4) for i in range(hc)]
 history=[prefix+positions[v-prefix] if v>=prefix else v for v in history]
 newhist={r[1]:prefix+i for i,r in enumerate(out) if r[0]==0x30 and r[1]>=hc}
 history+=[newhist[i] for i in range(hc,hc+len(messages))]
 allstrings=[text_at(old,i) for i in range(nc+kc-1)]+strings+[b'']
 assert not any(r[0]==0x30 and r[2]==nc+kc-1 for r in rs)
 b=bytearray(old[:192])
 def append(raw):at=len(b);b.extend(raw);return at
 def rows(rows):return b''.join(struct.pack('<24I',*r) for r in rows)
 for countfield,offsetfield,count,raw in [
  (16,20,u32(old,16),old[u32(old,20):u32(old,20)+u32(old,16)*96]),
  (24,28,u32(old,24),old[u32(old,28):u32(old,28)+u32(old,24)*96]),
  (32,36,prefix,old[u32(old,36):u32(old,36)+prefix*96]),
  (40,44,len(out),rows(out)),
  (48,52,len(descriptors),b''.join(struct.pack('<4I',*d) for d in descriptors)),
  (56,60,len(history),struct.pack('<%dI'%len(history),*history))]:
  struct.pack_into('<II',b,countfield,count,append(raw))
 pointers=[];pool=bytearray()
 for s in allstrings:pointers.append(len(pool));pool.extend(s+b'\0')
 table=append(struct.pack('<%dI'%len(pointers),*pointers));poolat=append(pool);b.extend(bytes((-len(b))%4))
 struct.pack_into('<II',b,64,nc,table);struct.pack_into('<I',b,76,poolat)
 struct.pack_into('<III',b,80,kc+len(strings),table+nc*4,u32(old,88)+len(strings));struct.pack_into('<II',b,92,len(b),u32(old,96))
 struct.pack_into('<I',b,4,len(b));struct.pack_into('<I',b,108,len(b))
 # Prefix references are history indices; their existing history rows survive.
 for i,r in enumerate(rs):
  n=out[positions[i]];ignore=[6,7] if r[0]==0x90 else [7] if r[0]==0x91 else []
  assert all(r[j]==n[j] for j in range(24) if j not in ignore)
 for i in range(nc+kc-1):assert text_at(b,i)==text_at(old,i)
 for m in messages:assert text_at(b,m['sid'])==encode(m['text'])
 for i,r in enumerate(out):
  if r[0]==0x30:assert u32(b,u32(b,60)+r[1]*4)==prefix+i
 return bytes(b),dict(phases=notes,new_story_gates=gates,old_story_gates=[positions[i] for i,r in enumerate(rs) if r[0]==0x91 and i>0 and rs[i-1][0]==0x9a and rs[i-1][2:4]==[0,0x800e]],messages=messages,old_rows=len(rs),new_rows=len(out),old_row_positions=positions)
