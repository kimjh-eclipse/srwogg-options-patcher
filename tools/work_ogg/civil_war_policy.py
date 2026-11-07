"""Five native LOGO battles with automatic pair encounters and temporary splits."""
import struct
from regional_five_policy import Logo,stage_base,append_strings
from story_scripts_25 import command,NONE,DEAD,records
from catalog import Master,u16,u32,encode
from civil_war_content import PAIRS,PERSUASION,pair_lines

RELAY_KEYS=[1993,1994,1995]
HOSTAGE_KEY=1996
ORDINARY_KEYS=list(range(1997,2025))
GUARD='경비대 — 레피나 측'
INFIL='구출대 잠입조'
REBELS='경비대 반란조'

def availability(a,members,team,value):
 for name,x in members.items():
  if x['team']==team and x['pilot'] is not None:a.emit(0x4a,0x100a8,x['pilot'],value)

def segments(lines,members):
 out=[]
 for who,text in lines:
  kind='story' if members.get(who,{}).get('added') else 'common'
  if out and out[-1][0]==kind:out[-1][1].append((who,text))
  else:out.append((kind,[(who,text)]))
 return out

def say(a,lines,members):
 for kind,part in segments(lines,members):a.story(part) if kind=='story' else a.say(part)

def started(a,name):
 a.emit(0x93,0x10071,0,0,0x800f,NONE,NONE,NONE);i=a.emit(0x91,0x800f,0x8000,1,DEAD,DEAD,0);a.fix.append((i,name+'_exit'))

def mission(template,scene,members,speakers,private,mapkey,targets,nextindex):
 a=Logo(template,speakers);key=scene['key'];pairs=[]
 a.function('defeat',28);started(a,'defeat');a.emit(0x7a,0x100ad,0,0);a.emit(0xa1,0xffffffff,0);a.end('defeat')
 a.function('hostage_loss',28);started(a,'hostage_loss');a.emit(0x7a,0x100bd,HOSTAGE_KEY,0);a.say([('테츠야','수송편과의 연결이 끊겼다. 이번 작전은 실패다. 철수한다.')]);a.emit(0xa1,0xffffffff,0);a.end('hostage_loss')
 a.function('map',2);a.emit(0xb0,60,0x10014);a.emit(0xbd,mapkey);a.emit(0x79,0x10049,NONE,NONE);a.emit(0xba,0x10071,4,7);a.end('map')
 a.function('opening',27,0,0);a.emit(0xb0,1,0x10012);a.emit(0xaf,1,0x10014);a.emit(0xaf,60,0x10012)
 if key==2044:availability(a,members,INFIL,1)
 say(a,scene['pre'],members);a.emit(0x7b,0x100ef,0x10086,0x10041);a.emit(0xb0,1,0x10012)
 a.emit(0xca,0,250);a.emit(0xca,1,250);a.emit(0xc3,12);a.emit(0x6c,30,0);a.emit(0x68,53);a.emit(0xbc,53);a.emit(0xaf,60,0x10012)
 say(a,scene['opening'],members);a.emit(0x7b,0x100ef,0x10086,0x10041)
 for sel,text in [(0x100ed,'반란 지휘부 제압' if key==2045 else '제어 중계기 제압'),(0x10072,'아군 전멸 또는 인질 수송기 격파'),(0x100b7,'없음')]:a.emit(0x5a,sel,a.string(text))
 a.emit(0x5b,0x1ff);a.emit(0xd1,0);a.end('opening',0)
 a.function('ending',27,1,2);started(a,'ending')
 a.emit(0x96,0x100bd,HOSTAGE_KEY,0x800e);i=a.emit(0x91,0x800e,0x8000,1,DEAD,DEAD,0);a.fix.append((i,'ending_exit'))
 for target in targets:a.emit(0x7a,0x100bd,target,0)
 a.emit(0x6d);a.emit(0x67);say(a,scene['post'],members);a.emit(0x7b,0x100ef,0x10086,0x10041)
 if key==2041:availability(a,members,INFIL,0)
 if key==2044:
  availability(a,members,GUARD,1);availability(a,members,INFIL,1)
 if key==2045:
  for team in [GUARD,INFIL,REBELS]:availability(a,members,team,1)
  a.emit(0xba,0x100c1,36,1)
 a.emit(0xa1,nextindex,0);a.end('ending',2)
 # Same native 2A dispatcher used by original boss encounter conversations.
 a.function('encounters',27,2);started(a,'encounters')
 dispatch=[]
 for index in scene['pairs']:
  left,right=PAIRS[index]
  def actor(who):
   item=members[who]
   enemy=(item['team']==GUARD and key<2045) or (item['team']==REBELS) or (item['team']==INFIL and key in [2042,2043])
   return private[who] if enemy else item['pilot']
  dispatch.append((a.emit(0x2a,0x8000,0x100a8,actor(left),0x100a8,actor(right),0x10018,0),index,left,right,actor(left),actor(right)))
 a.end('encounters')
 for row,index,left,right,lp,rp in dispatch:
  name='pair_'+str(index);a.label(name);a.funcs.append(name);a.rows[row][8]=len(a.funcs)
  a.flagguard(1,index,name+'_exit') if index<8 else a.flagguard(2,index-8,name+'_exit')
  say(a,pair_lines(key,index),members);a.emit(0x7b,0x100ef,0x10086,0x10041);a.emit(0xba,0x10071,1 if index<8 else 2,index if index<8 else index-8)
  a.label(name+'_exit');a.emit(0x3e)
  pairs.append(dict(index=index,left=left,right=right,left_key=lp,right_key=rp,function=name,dispatcher_row=row,flag=[1 if index<8 else 2,index if index<8 else index-8]))
 blob,note=a.finish();note.update(pairs=pairs,targets=targets,hostage=HOSTAGE_KEY,next_index=nextindex,auto_encounter=True)
 return blob,note

def master(old,members,private,names_from=None):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields];parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))}
 from civil_war_content import SCENES
 canonical=names_from or m
 def unitname(key):
  ix=u16(canonical.b,canonical.tables['UTbl'][0]+12+key*2);return canonical.text(u16(canonical.b,canonical.tables['Unit'][0]+12+ix*100+12))
 newstrings=[s['title'] for s in SCENES]+['제어 중계기','인질 수송기','위원회 연락관','경비 참모장','민간 감찰관','수송반']+[unitname(members[n]['unit']) for n in private]+list(private)
 sid=m.tables['Strg'][2];parts[0x80]=append_strings(parts[0x80],[encode(t) for t in newstrings]);uc=m.tables['Unit'][2];pc=m.tables['Plot'][2];notes=[]
 def record(tag,lookup,key,stride):
  ix=u16(old,m.tables[lookup][0]+12+key*2);assert ix!=65535;at=m.tables[tag][0]+12+ix*stride;return bytearray(old[at:at+stride]),at
 def unit(key,row):
  nonlocal uc
  assert u16(parts[0x18],12+key*2)==65535;struct.pack_into('<H',parts[0x18],12+key*2,uc);parts[0x1c].extend(row);uc+=1
 def pilot(key,row):
  nonlocal pc
  assert u16(parts[0x28],12+key*2)==65535;struct.pack_into('<H',parts[0x28],12+key*2,pc);parts[0x2c].extend(row);pc+=1
 for j,(who,key) in enumerate(private.items()):
  item=members[who];b,at=record('Unit','UTbl',item['unit'],100)
  if b[0x5d]:at+=struct.unpack_from('<h',b,0x62)[0];b=bytearray(old[at:at+100])
  b[0x5d]=0;struct.pack_into('<h',b,0x62,0);struct.pack_into('<H',b,0x14,65535);struct.pack_into('<H',b,12,sid+11+j)
  hp=80000 if who=='레피나' else 70000 if who in ['빈델','웬드로'] else 35000 if who in ['아치볼드','이글렛'] else min(36000,max(18000,int(u32(b)*1.2)))
  struct.pack_into('<I',b,0,hp);unit(key,b);p,_=record('Plot','PTbl',item['pilot'],148);struct.pack_into('<3H',p,4,*([sid+11+len(private)+j]*3));pilot(key,p);notes.append(dict(who=who,key=key,source_unit=item['unit'],source_pilot=item['pilot'],hp=hp))
 byname={m.text(u16(row,12)):key for key in range(m.tables['UTbl'][2]) if u16(old,m.tables['UTbl'][0]+12+key*2)!=65535 for row,at in [record('Unit','UTbl',key,100)]}
 transport=1388;assert u16(old,m.tables['UTbl'][0]+12+transport*2)!=65535
 for i,key in enumerate(RELAY_KEYS+[HOSTAGE_KEY]):
  src=transport if key==HOSTAGE_KEY else 1191;b,_=record('Unit','UTbl',src,100);struct.pack_into('<I',b,0,30000 if key==HOSTAGE_KEY else 20000);struct.pack_into('<H',b,12,sid+6 if key==HOSTAGE_KEY else sid+5);struct.pack_into('<H',b,0x14,65535);b[0x5d]=0;struct.pack_into('<h',b,0x62,0);unit(key,b)
 for i,key in enumerate(ORDINARY_KEYS):
  source=[1204,1092,1191,1054][i%4];ix=u16(old,m.tables['UTbl'][0]+12+source*2);assert u16(parts[0x18],12+key*2)==65535;struct.pack_into('<H',parts[0x18],12+key*2,ix)
 for key,nameindex in [(1993,10),(1994,7),(1995,8),(1996,9)]:
  p,_=record('Plot','PTbl',1029,148);struct.pack_into('<3H',p,4,*([sid+nameindex]*3));pilot(key,p)
 for field,count,stride in [(0x1c,uc,100),(0x2c,pc,148)]:struct.pack_into('<II',parts[field],4,12+count*stride,count)
 for field,table in [(0x18,0x1c),(0x28,0x2c)]:struct.pack_into('<I',parts[field],4,u32(parts[table],4))
 if names_from is None:
  sb=stage_base(m)-m.tables['Stag'][0]
  for i,s in enumerate(SCENES):
   at=sb+(s['key']-2000)*12;assert parts[0x58][at:at+2]==b'\xff\xff';r=bytearray(parts[0x58][sb+40*12:sb+41*12]);struct.pack_into('<Hhh',r,0,sid+i,-1,-1);r[6]=s['number'];parts[0x58][at:at+12]=r
  parts[0x58][sb+34*12+6]=47
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old),(used,len(old));out.extend(bytes(len(old)-used));n=Master(out)
 for tag,stride in [('Unit',100),('Plot',148),('Weap',36)]:
  a=m.tables[tag][0]+12;b=n.tables[tag][0]+12;assert old[a:a+m.tables[tag][2]*stride]==out[b:b+m.tables[tag][2]*stride]
 return bytes(out),dict(named=notes,used_bytes=used,transport_source=transport,new_titles=newstrings[:5])
