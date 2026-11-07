"""Append three native turn callbacks without relocating existing main rows."""
import struct
from story_scripts_25 import command,records,text_at,encode,wrap,NONE,DEAD
from inspect_iso import u32

KEYS=list(range(2025,2043))
SOURCES=[1204,1092,1191,1054,1204,1092]
OFFSETS=[(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2)]
SHIPS=[1188,1215]
SHIP_PILOTS=[1137,1209]
FALLBACK=1996
FALLBACK_PILOT=1993

def append_waves(old,first_row=45,alert_pilot=1071):
 oldrows=records(old);rows=[r.copy() for r in oldrows];prefix=u32(old,32)
 descriptors=[list(struct.unpack_from('<4I',old,u32(old,52)+i*16)) for i in range(u32(old,48))]
 events=[list(struct.unpack_from('<24I',old,u32(old,28)+i*96)) for i in range(u32(old,24))]
 history=[u32(old,u32(old,60)+i*4) for i in range(u32(old,56))]
 nc=u32(old,64);kc=u32(old,80);strings=[text_at(old,i) for i in range(nc+kc-1)];oldstrings=len(strings)
 template=next(r.copy() for r in oldrows if r[0]==0x30 and r[13]==0x100a8 and r[3]==NONE)
 labels={};fix=[];waves=[];messages=[]
 def emit(op,*args):rows.append(command(op,*args));return len(rows)-1
 def label(name):labels[name]=len(rows)
 def eq(reg,value,target):
  i=emit(0x91,reg,0x8000,value,DEAD,DEAD,0);fix.append((i,target))
 def jump(target):emit(0x9a,0,0x800d);eq(0x800d,1,target)
 def count(key,reg):emit(0x96,0x100bd,key,reg)
 for wave,turn in enumerate([2,3,4]):
  name='wave_'+str(turn);start=len(rows);desc=len(descriptors);descriptors.append([1,0,start,0]);events.append(command(0x42,27,desc,turn,0))
  emit(0x26);emit(0x79,0x10018,0,NONE)
  emit(0x93,0x10071,0,0,0x800f,NONE,NONE,NONE);eq(0x800f,1,name+'_exit')
  emit(0x93,0x10071,3,wave,0x800f,NONE,NONE,NONE);eq(0x800f,0,name+'_exit')
  emit(0x9a,0x8014,0x800e);eq(0x800e,turn,name+'_exit')
  count(FALLBACK,0x800e);eq(0x800e,1,name+'_exit')
  # A completed objective must not gain a new wave during a callback transition.
  targets=sorted({r[3] for r in oldrows if r[0]==0x7a and r[2]==0x100bd and r[3]!=FALLBACK})
  assert 2<=len(targets)<=4
  for key in targets:count(key,0x800e);eq(0x800e,0,name+'_active')
  jump(name+'_exit');label(name+'_active')
  for text in wrap('에이타','후방에 적 증원 확인! 함선과 수송편 주변을 경계하십시오!'):
   sid=len(strings);strings.append(encode(text))
   r=template.copy();r[1]=len(history);r[2]=sid;r[4]=alert_pilot;r[5]=0;history.append(prefix+len(rows));rows.append(r);messages.append(dict(turn=turn,text=text,sid=sid,label=r[1],who='윤' if alert_pilot==1181 else '에이타'))
  emit(0x7b,0x100ef,0x10086,0x10041)
  count(SHIPS[0],0x800a);eq(0x800a,1,name+'_no_hagane')
  count(SHIPS[1],0x800b);eq(0x800b,1,name+'_hagane_only')
  for i in range(6):emit(0xcb,SHIP_PILOTS[i%2],first_row+wave*6+i)
  jump(name+'_spawned');label(name+'_hagane_only')
  for i in range(6):emit(0xcb,SHIP_PILOTS[0],first_row+wave*6+i)
  jump(name+'_spawned');label(name+'_no_hagane')
  count(SHIPS[1],0x800b);eq(0x800b,1,name+'_fallback')
  for i in range(6):emit(0xcb,SHIP_PILOTS[1],first_row+wave*6+i)
  jump(name+'_spawned');label(name+'_fallback')
  for i in range(6):emit(0xcb,FALLBACK_PILOT,first_row+wave*6+i)
  label(name+'_spawned');emit(0xba,0x10071,3,wave);label(name+'_exit');emit(0x3e);emit(0x25)
  waves.append(dict(turn=turn,phase=0,function=start,event_descriptor=desc,local_flag=[3,wave],rows=list(range(first_row+wave*6,first_row+(wave+1)*6))))
 for i,target in fix:rows[i][7]=labels[target]-i
 b=bytearray(old[:192])
 def append(data):at=len(b);b.extend(data);return at
 def packrows(rs):return b''.join(struct.pack('<24I',*r) for r in rs)
 for cf,pf,count,raw in [(16,20,u32(old,16),old[u32(old,20):u32(old,20)+u32(old,16)*96]),(24,28,len(events),packrows(events)),(32,36,prefix,old[u32(old,36):u32(old,36)+prefix*96]),(40,44,len(rows),packrows(rows)),(48,52,len(descriptors),b''.join(struct.pack('<4I',*d) for d in descriptors)),(56,60,len(history),struct.pack('<%dI'%len(history),*history))]:struct.pack_into('<II',b,cf,count,append(raw))
 pointers=[];pool=bytearray()
 for text in strings+[b'']:pointers.append(len(pool));pool.extend(text+b'\0')
 table=append(struct.pack('<%dI'%len(pointers),*pointers));poolat=append(pool);b.extend(bytes((-len(b))%4));struct.pack_into('<II',b,64,nc,table);struct.pack_into('<I',b,76,poolat);struct.pack_into('<III',b,80,len(strings)+1-nc,table+nc*4,u32(old,88)+len(strings)-oldstrings);struct.pack_into('<I',b,4,len(b));struct.pack_into('<I',b,108,len(b))
 assert records(b)[:len(oldrows)]==oldrows
 assert all(text_at(old,i)==text_at(b,i) for i in range(oldstrings))
 return bytes(b),dict(waves=waves,messages=messages,old_main_rows=len(oldrows),new_main_rows=len(rows),existing_rows_and_dialogue_preserved=True)
