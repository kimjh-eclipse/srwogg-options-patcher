from apply_balance_25 import get_record,logical_strings
from catalog import *

# Native allied profiles at level one. Small role changes, no boss stat curves.
# six values are melee, ranged, skill, evasion, accuracy, defence (0x65..0x6a).
PROFILES={
 '잉그램':(1065,[1,1,2,0,1,0]),'린':(1202,[0,0,0,0,0,0]),
 '레몬':(1073,[1,1,2,0,1,2]),'메키보스':(1204,[2,0,1,-1,0,3]),
 '비가지':(1091,[3,-2,1,-5,0,5]),'비안':(1090,[1,2,3,-3,2,3]),
 '빈델':(47,[-1,-1,-2,-3,-1,-1]),'스리사즈':(1195,[2,-1,0,0,0,1]),
 '시카로그':(1129,[0,-2,0,-5,-2,5]),'아기하':(1073,[-2,1,1,2,0,-2]),
 '아치볼드':(1205,[-3,2,1,-3,0,2]),'아타드':(1065,[-4,-1,0,-3,-1,0]),
 '안사즈':(1195,[-1,2,0,0,1,0]),'에키드나':(1188,[-1,0,-1,0,0,0]),
 '오우카':(1187,[2,0,1,-1,0,4]),'울즈':(1187,[0,0,2,0,1,3]),
 '워단':(1129,[0,0,1,-1,0,2]),'웬드로':(1090,[1,2,3,-4,3,4]),
 '유리아':(1205,[0,1,1,-1,1,3]),'이글렛':(1091,[-7,-2,1,-8,0,0]),
 '지벨':(1091,[-5,0,0,-8,-1,4]),'텐잔':(1195,[-3,0,-2,-5,-1,2]),
 '템페스트':(1090,[-3,1,0,-3,0,3]),'토머스':(1091,[-4,1,0,-2,1,1]),
 '가루인':(1090,[2,0,3,-2,1,4])
}

def rebuild_master(old,cast,reference=None):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 reference=reference or m
 parts={k:bytearray(old[p:(starts[i+1] if i+1<len(starts) else p+u32(old,p+4))]) for i,(k,p) in enumerate(zip(fields,starts))}
 parts[0x88].extend(bytes((-len(parts[0x88]))%4))
 names=logical_strings(m,'Strg');notes=[];allowedplot=set();allowedunit=set()
 assert all(r[0x5d]==0 for i,p,r in m.rows('Unit')),'Phase marker byte must be unused'
 for name,(ref,delta) in PROFILES.items():
  pi,pilot=get_record(m,'Plot','PTbl',cast[name]['new_key'],148)
  _,native=get_record(reference,'Plot','PTbl',ref,148);r=bytearray(pilot)
  r[0x65:0x6b]=bytes(a+b for a,b in zip(native[0x65:0x6b],delta))
  r[0x64]=min(60,max(40,pilot[0x64]));r[0x1a:0x1c]=native[0x1a:0x1c]
  if name=='이글렛':
   # Previously a non-combat NPC with zero stats: an ordinary support spirit set.
   r[0x6b:0x7e]=native[0x6b:0x7e]
   for i in range(0x72,0x78):
    if r[i]:r[i]=1
  assert 43 not in r[0x7e:0x84]
  p=12+pi*148;parts[0x2c][p:p+148]=r;allowedplot.add(pi)
  notes.append(dict(name=name,key=cast[name]['new_key'],native_reference=ref,
                    before=list(pilot[0x64:0x6b]),after=list(r[0x64:0x6b]),growth=u16(r,0x1a)))
 locks=[]
 for name,threshold,slot in [('린',14,1),('워단',18,3)]:
  ui,full=get_record(m,'Unit','UTbl',cast[name]['new_key'],100);assert full[0x5d]==0 and not any(full[0x62:])
  full=bytearray(full);weak=bytearray(full);wk=u16(full,0x24+slot*2)
  _,wr=get_record(m,'Weap','WTbl',wk,36);locked=bytearray(wr);locked[0x1b]=255
  text=m.text(u16(wr,4))+'（정비중）';newstring=len(names);names.append(encode(text)+b'\0');struct.pack_into('<H',locked,4,newstring)
  free=next(k for k in range(0xe00,4096) if u16(parts[0x20],12+k*2)==65535)
  wi=u32(parts[0x24],8);parts[0x24].extend(locked);struct.pack_into('<H',parts[0x20],12+free*2,wi)
  struct.pack_into('<II',parts[0x24],4,12+(wi+1)*36,wi+1)
  struct.pack_into('<H',weak,0x24+slot*2,free)
  weakidx=u32(parts[0x1c],8);parts[0x1c].extend(weak)
  struct.pack_into('<II',parts[0x1c],4,12+(weakidx+1)*100,weakidx+1)
  struct.pack_into('<I',parts[0x18],4,12+(weakidx+1)*100)
  full[0x5d]=threshold;struct.pack_into('<h',full,0x62,(weakidx-ui)*100)
  parts[0x1c][12+ui*100:12+(ui+1)*100]=full;allowedunit.add(ui)
  locks.append(dict(name=name,key=cast[name]['new_key'],unlocks_chapter=threshold+1,cleared_threshold=threshold,slot=slot,full_weapon=wk,locked_weapon=free,weak_unit_index=weakidx,full_unit_index=ui))
 # Rebuild just Strg; IDs of every old name remain unchanged.
 p=bytearray(b'Strg'+bytes(8+4*len(names)))
 for i,s in enumerate(names):struct.pack_into('<I',p,12+i*4,len(p));p.extend(s)
 p.extend(bytes((-len(p))%4));struct.pack_into('<II',p,4,len(p),len(names));parts[0x80]=p
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old),(used,len(old));out.extend(bytes(len(old)-used));new=Master(out)
 for tag,stride,allowed in [('Unit',100,allowedunit),('Plot',148,allowedplot),('Weap',36,set())]:
  for i in range(m.tables[tag][2]):
   if i in allowed:continue
   a=m.tables[tag][0]+12+i*stride;b=new.tables[tag][0]+12+i*stride;assert old[a:a+stride]==out[b:b+stride],(tag,i)
 assert logical_strings(new,'Strg')[:m.tables['Strg'][2]]==logical_strings(m,'Strg')
 for tag in ['Expl','Sent']:assert logical_strings(new,tag)==logical_strings(m,tag)
 for tag in m.tables:
  if tag in ['UTbl','Unit','WTbl','Weap','Plot','Strg']:continue
  a,size,_=m.tables[tag];b=new.tables[tag][0];assert old[a:a+size]==out[b:b+size],tag
 return bytes(out),dict(pilots=notes,locks=locks,used_bytes=used,capacity=len(old),original_enemy_records_preserved=True)
