"""Append the 25-character arc to OGG LOGO and UNTD payloads in memory."""
from audit_story_layout import *
from story_content_25 import ARRIVALS,JOINS,FOLLOWUPS,ALIASES
from build_patch import command
from collections import Counter
from apply_balance_25 import get_record

CHAPTER_KEYS={1:2001,2:2002,3:2003,4:2050,5:2004,6:2005,7:2006,8:2007,9:2008,
 15:2014,16:2015,17:2056,18:2016,**{i:2000+i-2 for i in range(19,37)}}
WAVE={3:5,4:5,5:0,8:1,9:3,15:1,19:5,20:10,21:7,22:5,23:3,
      24:0,25:6,26:6,27:6,28:0,29:7,30:2,31:8,34:0,35:1}
DEAD=0xdeaddead
NONE=0xdeaddeed

def records(b):return [list(struct.unpack_from('<24I',b,u32(b,44)+i*96)) for i in range(u32(b,40))]
def text_at(b,sid):
 p=u32(b,76)+u32(b,u32(b,68)+sid*4);end=b.find(0,p);assert p<=len(b)
 return b[p:end if end>=0 else len(b)]

def wrap(speaker,text):
 text=(speaker+'：'+text).replace(' ','　');lines=[]
 while len(text)>20:
  cut=text.rfind('　',7,21)
  if cut<0:cut=20
  lines.append(text[:cut]);text=text[cut:].lstrip('　')
 lines.append(text)
 # Long speeches continue in a second box, each under the native 128-byte buffer.
 out=['@'.join(lines[i:i+3]) for i in range(0,len(lines),3)]
 for t in out:
  assert not any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in t)
  assert len(encode(t))<128 and decode(encode(t))==t
 return out

def rebuild_logo(old,point,lines,speakers,flag,group=None):
 rs=records(old);count=len(rs);co=u32(old,44);prefix=u32(old,32)
 nc,kc,hc=(u32(old,k) for k in [64,80,56]);assert 0<point<count
 descriptors=[struct.unpack_from('<4I',old,u32(old,52)+i*16) for i in range(u32(old,48))]
 active_kinds={descriptors[r[2]][0] for r in rs if r[0]==0x2f and r[2]<len(descriptors)}-{0}
 assert len(active_kinds)==1,('ambiguous current script sheet',active_kinds)
 # Ordinary portrait dialogue; avoid reusing camera/actor movement commands.
 template=next(r for r in rs if r[0]==0x30 and r[13]==0x100a8 and r[3]==NONE)
 body=[];messages=[]
 for who,text in lines:
  for t in wrap(who,text):
   r=template.copy();r[1]=hc+len(messages);r[2]=nc+kc-1+len(messages);r[4]=speakers[who];r[5]=0
   body.append(r);messages.append(dict(speaker=who,key=speakers[who],text=t,encoded=encode(t).hex(),label=r[1],string_id=r[2]))
 if group is not None:body.append(command(0xca,group,250,DEAD))
 g,bit=flag;body.append(command(0xba,0x100c1,g,bit))
 added=[command(0x93,0x100c1,g,bit,0x800f,NONE,NONE,NONE),command(0x91,0x800f,0x8000,0,DEAD,DEAD,len(body)+1)]+body
 def moved(i):return i+len(added) if i>=point else i
 outrows=[];labels={}
 for i,r in enumerate(rs):
  if i==point:
   for a in added:
    if a[0]==0x30:labels[a[1]]=prefix+len(outrows)
    outrows.append(a)
  r=r.copy()
  if r[0] in [0x90,0x91]:
   for field in ([6,7] if r[0]==0x90 else [7]):
    if r[field]<0x80000000:
     assert 0<=i+r[field]<=count,(i,field,r[field],count)
     r[field]=moved(i+r[field])-moved(i)
  outrows.append(r)
 extra=len(added)*96;endcode=co+count*96
 b=bytearray(old[:co])+bytearray(b''.join(struct.pack('<24I',*r) for r in outrows))+bytearray(old[endcode:])
 struct.pack_into('<I',b,40,len(outrows))
 for field in [52,60,68,76,84,92]:
  assert u32(old,field)>=endcode,(field,u32(old,field),endcode)
  struct.pack_into('<I',b,field,u32(old,field)+extra)
 desc=u32(b,52)
 for i in range(u32(old,48)):
  p=desc+i*16;kind=u32(b,p);target=u32(b,p+8)
  if kind in active_kinds:struct.pack_into('<I',b,p+8,moved(target))
 history=[u32(old,u32(old,60)+i*4) for i in range(hc)]
 history=[prefix+moved(i-prefix) if i>=prefix else i for i in history]
 history.extend(labels[i] for i in range(hc,hc+len(messages)))
 assert u32(old,84)==u32(old,68)+nc*4
 pointers=list(struct.unpack_from('<%dI'%(nc+kc),old,u32(old,68)))[:-1];pool=u32(b,76)
 b.extend(b'\0')  # Safely terminate the existing unused tail string in chapter 25.
 assert all(r[2]!=nc+kc-1 for r in rs if r[0]==0x30)
 for msg in messages:pointers.append(len(b)-pool);b.extend(bytes.fromhex(msg['encoded'])+b'\0')
 pointers.append(len(b)-pool);b.extend(bytes((-len(b))%4));table=len(b);b.extend(struct.pack('<%dI'%len(pointers),*pointers))
 struct.pack_into('<I',b,68,table);struct.pack_into('<I',b,84,table+nc*4)
 struct.pack_into('<I',b,80,kc+len(messages));struct.pack_into('<I',b,88,u32(old,88)+len(messages))
 hist=len(b);b.extend(struct.pack('<%dI'%len(history),*history));struct.pack_into('<II',b,56,len(history),hist)
 struct.pack_into('<I',b,4,len(b));struct.pack_into('<I',b,108,len(b))
 # Preserve every original row, descriptor, history entry and logical string.
 check=records(b)
 for i,r in enumerate(rs):
  n=check[moved(i)];allowed=[6,7] if r[0]==0x90 else [7] if r[0]==0x91 else []
  assert all(r[j]==n[j] for j in range(24) if j not in allowed),(i,'original command')
  for j in allowed:
   if r[j]<0x80000000:assert moved(i)+n[j]==moved(i+r[j])
 for i in range(nc+kc-1):assert text_at(old,i)==text_at(b,i),('original string',i)
 for msg in messages:assert text_at(b,msg['string_id'])==bytes.fromhex(msg['encoded'])
 for i,d in enumerate(descriptors):
  a=struct.unpack_from('<4I',b,u32(b,52)+i*16)
  assert a==(d[0],d[1],moved(d[2]) if d[0] in active_kinds else d[2],d[3])
 return bytes(b),dict(before_record=point,active_script_sheets=sorted(active_kinds),inserted_records=len(added),flag=list(flag),group=group,messages=messages,
                      original_records_preserved=count,original_strings_preserved=nc+kc-1,
                      inserted_rows=added,entry_index=point,end_index=point+len(added))

def find_point(old,ch):
 rs=records(old)
 if ch==36:return max(i for i,r in enumerate(rs) if r[0]==0x30)+1
 wave=WAVE[ch];start=next(i for i,r in enumerate(rs) if r[0]==0xca and r[2]==wave)
 # Finish the native reinforcement conversation, before its dialogue-close command.
 end=next(i for i in range(start+1,len(rs)) if rs[i][0]==0x25)
 closes=[i for i in range(start+1,end) if rs[i][0]==0x7b]
 point=closes[0] if closes else max(i for i in range(start+1,end) if rs[i][0]==0x30)+1
 assert any(r[0]==0x30 for r in rs[start+1:point]),(ch,'no reinforcement conversation')
 return point

def resolve_speakers(m,cast,allunits):
 names=set(who for d in [ARRIVALS,JOINS,FOLLOWUPS] for lines in d.values() for who,text in lines)
 result={};native=[]
 for raw in allunits:
  if len(raw)!=44+u32(raw,40)*336:continue  # legacy OG1/OG2 records use another stride
  for i in range(u32(raw,40)):
   row=raw[44+i*336:44+(i+1)*336];key=u32(row,32)
   if key<2048:
    idx=u16(m.b,m.tables['PTbl'][0]+12+key*2)
    if idx<m.tables['Plot'][2]:native.append((key,m.text(u16(m.b,m.tables['Plot'][0]+12+idx*148+4))))
 for name in names:
  if name in cast:result[name]=cast[name]['new_key'];continue
  options=[name]+ALIASES.get(name,[]);candidates=[k for k,n in native if n in options and 1000<=k<1792]
  if not candidates:candidates=[k for k,n in native if n in options]
  assert candidates,('speaker missing',name);result[name]=Counter(candidates).most_common(1)[0][0]
 return result

def join_units(old,names,templates,cast,grade,group,tiles):
 n=u32(old,40);assert len(old)==44+n*336
 oldrows=[old[44+i*336:44+(i+1)*336] for i in range(n)]
 assert all(u32(r,4)!=group for r in oldrows)
 # Match an existing allied ground surface near this chapter's reinforcement wave.
 wave=WAVE[grade['chapter']];anchors=[r for r in oldrows if u32(r,4)==wave and u32(r,8)==0]
 if not anchors:anchors=[r for r in oldrows if u32(r,4)==255 and u32(r,8)==0]
 assert anchors,(grade['chapter'],'no allied wave anchor')
 preferred=[r for r in anchors if u32(r,32) not in [1136,1209]]
 anchor=(preferred or anchors)[0];ax,ay=u32(anchor,16),u32(anchor,20)
 maps=[u32(old,k) for k in [8,12,16,20] if u32(old,k)!=0xffffffff]
 # Later maps may use a second UNTD map slot (notably chapter 31).
 choices=[(k,tiles[k]) for k in maps if k in tiles and ax<u32(tiles[k],8) and ay<u32(tiles[k],12)]
 assert choices,(maps,ax,ay)
 mk,tb=choices[0];w,h=u32(tb,8),u32(tb,12);surface=tb[32+(ay*w+ax)*8:40+(ay*w+ax)*8]
 occupied={(u32(r,16),u32(r,20)) for r in oldrows}
 allies=[(u32(r,16),u32(r,20)) for r in oldrows if u32(r,8)==0 and 0<u32(r,16)<w and 0<u32(r,20)<h]
 safe={tb[32+(b*w+a)*8:36+(b*w+a)*8]:tb[32+(b*w+a)*8:40+(b*w+a)*8] for a,b in allies}
 safe.pop(bytes(4),None)
 candidates=[(abs(x-ax)+abs(y-ay),x,y) for y in range(1,h-1) for x in range(1,w-1)
             if (x,y) not in occupied and min(abs(x-a)+abs(y-b) for a,b in allies)>=4
             and tb[32+(y*w+x)*8:36+(y*w+x)*8] in safe]
 candidates.sort();assert len(candidates)>=len(names),(grade['chapter'],len(candidates),names,mk,ax,ay,surface.hex())
 out=bytearray(old);notes=[]
 for name,(_,x,y) in zip(names,candidates):
  row=bytearray(templates[cast[name]['new_key']]);g=grade[name]
  for p,value in [(4,group),(16,x),(20,y)]:struct.pack_into('<I',row,p,value)
  for p in [0x38,0x3c,0x40,0x44,0x48,0x4c]:struct.pack_into('<I',row,p,g)
  for p in [0x50,0x54,0x58]:struct.pack_into('<I',row,p,0xffffffff)
  assert u32(row)==cast[name]['new_key'] and u32(row,32)==cast[name]['new_key'] and u32(row,8)==0
  tile=tb[32+(y*w+x)*8:40+(y*w+x)*8]
  assert abs(x-ax)+abs(y-ay)<=16,('reinforcement too far away',name,x,y,ax,ay)
  out.extend(row);notes.append(dict(name=name,key=cast[name]['new_key'],group=group,position=[x,y],initial_upgrade=g,experience='owned-pilot mean; level 6 if none',map_info=mk,map_dimensions=[w,h],surface=tile.hex(),native_reference_surface=safe[tile[:4]].hex(),row_hex=row.hex()))
 struct.pack_into('<I',out,40,n+len(names));assert out[44:44+n*336]==old[44:]
 return bytes(out),notes
