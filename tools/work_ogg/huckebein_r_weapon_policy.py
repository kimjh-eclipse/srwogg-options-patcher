"""Private copies of the R model's five default weapons, each +200 power."""
import struct
from catalog import Master,u16,u32
from apply_balance_25 import get_record,logical_strings
UNIT_KEY=1209
POWER_DELTA=200

def rebuild(old):
 m=Master(old);ui,body=get_record(m,'Unit','UTbl',UNIT_KEY,100);body=bytearray(body)
 fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))}
 parts[0x88].extend(bytes((-len(parts[0x88]))%4))
 free=iter(k for k in range(0xe00,4096) if u16(parts[0x20],12+k*2)==65535);count=m.tables['Weap'][2];notes=[]
 for slot,wk in enumerate(struct.unpack_from('<16H',body,0x24)):
  if wk==65535:continue
  wi,row=get_record(m,'Weap','WTbl',wk,36);new=bytearray(row);power=u16(row,8);assert 0<power<65000
  struct.pack_into('<H',new,8,power+POWER_DELTA);nk=next(free);idx=count;count+=1
  parts[0x24].extend(new);struct.pack_into('<H',parts[0x20],12+nk*2,idx);struct.pack_into('<H',body,0x24+slot*2,nk)
  notes.append({'slot':slot,'source_key':wk,'private_key':nk,'name':m.text(u16(row,4)),'before_power':power,'after_power':power+POWER_DELTA,'before_weapon_hex':row.hex(),'after_weapon_hex':new.hex()})
 assert len(notes)==5
 at=12+ui*100;before=bytes(parts[0x1c][at:at+100]);parts[0x1c][at:at+100]=body
 struct.pack_into('<II',parts[0x24],4,12+count*36,count)
 out=bytearray(old[:starts[0]])
 for field in fields:struct.pack_into('<I',out,field,len(out));out.extend(parts[field])
 used=len(out);assert used<=len(old);out.extend(bytes(len(old)-used));n=Master(out)
 for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
  for i in range(m.tables[tag][2]):
   if tag=='Unit' and i==ui:continue
   a=m.tables[tag][0]+12+i*stride;b=n.tables[tag][0]+12+i*stride;assert old[a:a+stride]==out[b:b+stride],(tag,i)
 for tag in ['Strg','Sent','Expl']:assert logical_strings(m,tag)==logical_strings(n,tag)
 for tag in m.tables:
  if tag in ['UTbl','Unit','Weap','WTbl']:continue
  a,size,_=m.tables[tag];b=n.tables[tag][0];assert old[a:a+size]==out[b:b+size],tag
 assert parts[0x18]==old[starts[0]:starts[1]]
 assert all(before[i]==body[i] for i in range(100) if not 0x24<=i<0x44)
 return bytes(out),{'unit_key':UNIT_KEY,'before_unit_hex':before.hex(),'after_unit_hex':body.hex(),'weapons':notes,'capacity':len(old),'used_bytes':used,'original_weapon_rows_and_other_units_preserved':True}
