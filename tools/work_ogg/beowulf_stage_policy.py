"""Shared mission option: wide arena and native per-unit endless reinforcements."""
from regional_five_policy import Logo,append_strings,stage_base
from story_scripts_25 import NONE,DEAD,command
from beowulf_stage_content import *
from catalog import Master,u16,u32,encode
import struct

FIRST_MINION=1931
MAP_KEY=135
MINIONS=[1045]*10+[1046]*8+[1047]*6+[1048]*6

def mission_logo(template,speakers):
 a=Logo(template,speakers)
 def started(name):
  a.emit(0x93,0x10071,0,0,0x800f,NONE,NONE,NONE)
  i=a.emit(0x91,0x800f,0x8000,1,DEAD,DEAD,0);a.fix.append((i,name+'_exit'))
 def boss_alive(name):
  a.emit(0x96,0x100bd,UNIT,0x800e)
  i=a.emit(0x91,0x800e,0x8000,1,DEAD,DEAD,0);a.fix.append((i,name+'_exit'))
 a.function('defeat',28);started('defeat');a.emit(0x7a,0x100ad,0,0);a.emit(0xa1,0xffffffff,0);a.end('defeat')
 a.function('map',2);a.emit(0xb0,60,0x10014);a.emit(0xbd,MAP_KEY);a.emit(0x79,0x10049,NONE,NONE);a.emit(0xba,0x10071,4,7);a.end('map')
 a.function('opening',27,0,0);a.emit(0xb0,1,0x10012);a.emit(0xaf,1,0x10014);a.emit(0xca,0,250);a.emit(0xc3,12);a.emit(0x6c,30,0);a.emit(0x68,53);a.emit(0xbc,53);a.emit(0xaf,60,0x10012)
 a.say(SCENARIO['opening']);a.story(SCENARIO['story_opening']);a.emit(0x7b,0x100ef,0x10086,0x10041)
 for sel,text in [(0x100ed,'베오울프 격파'),(0x10072,'아군 전멸'),(0x100b7,'없음')]:a.emit(0x5a,sel,a.string(text))
 a.emit(0x5b,0x1ff);a.emit(0xd1,0);a.end('opening',0)
 # Ending checks every battle callback, including a boss kill with minions alive.
 # Register before respawns; every respawn also independently requires the boss.
 a.function('ending',27,bit=2);started('ending');a.emit(0x7a,0x100bd,UNIT,0)
 a.say(SCENARIO['ending']);a.story(SCENARIO['story_ending']);a.emit(0x7b,0x100ef,0x10086,0x10041);a.emit(0x6d);a.emit(0x67);a.emit(0xa1,34,0);a.end('ending',2)
 a.function('report',27,2,1);started('report');boss_alive('report');a.say(SCENARIO['mid']);a.story(SCENARIO['story_mid']);a.emit(0x7b,0x100ef,0x10086,0x10041);a.end('report',1)
 # One logical ID per ordinary enemy avoids confusing equal models. The native
 # unit-count predicate reads map actors, and CC creates the original UNTD row.
 # No wave counter or persistent reward/recruitment commands are involved.
 respawns=[];a.function('reinforcements',27,2);started('reinforcements');boss_alive('reinforcements')
 for i in range(30):
  name='respawn_'+str(i)+'_next';a.emit(0x96,0x100bd,FIRST_MINION+i,0x800f)
  ix=a.emit(0x91,0x800f,0x8000,0,DEAD,DEAD,0);a.fix.append((ix,name));a.emit(0xcc,12+i,250);a.label(name)
  respawns.append(dict(key=FIRST_MINION+i,row=12+i,function='reinforcements'))
 a.end('reinforcements')
 blob,note=a.finish();note.update(respawns=respawns,enemy_limit=32,endless_until_boss_defeated=True,victory='Beowulf defeated; remaining enemies receive no forced kill rewards')
 return blob,note

def record(m,table,lookup,key,stride):
 ix=u16(m.b,m.tables[lookup][0]+12+key*2);assert ix!=65535
 return ix,bytes(m.b[m.tables[table][0]+12+ix*stride:m.tables[table][0]+12+(ix+1)*stride])

def master_additions(old,source,add_stage=True):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))}
 _,body=record(source,'Unit','UTbl',1540,100);_,sp=record(source,'Plot','PTbl',1539,148)
 weapons=[(k,record(source,'Weap','WTbl',k,36)[1]) for k in struct.unpack_from('<16H',body,0x24) if k!=65535];assert len(weapons)==6
 names=[TITLE,source.text(u16(body,12)),'베오울프']+[source.text(u16(w,4)) for k,w in weapons]
 sid=m.tables['Strg'][2];parts[0x80]=append_strings(parts[0x80],[encode(n) for n in names]);uc=m.tables['Unit'][2];pc=m.tables['Plot'][2];wc=m.tables['Weap'][2]
 assert u16(parts[0x18],12+UNIT*2)==u16(parts[0x28],12+PILOT*2)==65535
 b=bytearray(body);struct.pack_into('<H',b,12,sid+1);struct.pack_into('<H',b,0x14,65535);struct.pack_into('<h',b,0x62,0)
 wn=[]
 for i,(oldkey,w) in enumerate(weapons):
  key=3762+i;assert u16(parts[0x20],12+key*2)==65535;r=bytearray(w);struct.pack_into('<H',r,4,sid+3+i);parts[0x24].extend(r);struct.pack_into('<H',parts[0x20],12+key*2,wc+i);struct.pack_into('<H',b,0x24+i*2,key);wn.append(dict(key=key,source_key=oldkey,name=names[3+i],power=u16(r,8),row=r.hex()))
 parts[0x1c].extend(b);struct.pack_into('<H',parts[0x18],12+UNIT*2,uc)
 _,native=record(m,'Plot','PTbl',1094,148);p=bytearray(native);struct.pack_into('<3H',p,4,sid+2,sid+2,sid+2);struct.pack_into('<H',p,0x48,FACE);p[0x65:0x6b]=sp[0x65:0x6b];parts[0x2c].extend(p);struct.pack_into('<H',parts[0x28],12+PILOT*2,pc)
 aliases=[]
 for i,original in enumerate(MINIONS):
  key=FIRST_MINION+i;assert u16(parts[0x18],12+key*2)==65535;ix=u16(parts[0x18],12+original*2);assert ix!=65535;struct.pack_into('<H',parts[0x18],12+key*2,ix);aliases.append(dict(key=key,source=original,record=ix))
 for field,count,stride in [(0x1c,uc+1,100),(0x24,wc+6,36),(0x2c,pc+1,148)]:struct.pack_into('<II',parts[field],4,12+count*stride,count)
 for field,table in [(0x18,0x1c),(0x20,0x24),(0x28,0x2c)]:struct.pack_into('<I',parts[field],4,u32(parts[table],4))
 if add_stage:
  sb=stage_base(m)-m.tables['Stag'][0];assert parts[0x58][sb+40*12:sb+40*12+2]==b'\xff\xff';r=bytearray(parts[0x58][sb+33*12:sb+34*12]);struct.pack_into('<Hhh',r,0,sid,-1,-1);r[6]=41;r[7]=r[10]=0;parts[0x58][sb+40*12:sb+41*12]=r;parts[0x58][sb+34*12+6]=42
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old);out.extend(bytes(len(old)-used));n=Master(out)
 for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
  a=m.tables[tag][0]+12;q=n.tables[tag][0]+12;assert old[a:a+m.tables[tag][2]*stride]==out[q:q+m.tables[tag][2]*stride]
 assert all(m.text(i)==n.text(i) for i in range(m.tables['Strg'][2]))
 return bytes(out),dict(unit=UNIT,pilot=PILOT,face=FACE,bank=BANK,hp=u32(b),en=u16(b,0x20),armor=u16(b,0x1a),pilot_base_stats=list(p[0x65:0x6b]),weapons=wn,aliases=aliases,title_id=sid,used_bytes=used,source_unit_row=body.hex(),new_unit_row=b.hex(),new_pilot_row=p.hex())
