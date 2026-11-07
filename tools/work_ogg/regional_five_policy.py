"""Source for five optional regional missions; no image writes on import.

Native operation numbers and deployment records are taken from the supplied
game.  MAP geometry/model archives are referenced, never copied or rewritten.
The prototype is deliberately separate from the released eleven-option pack.
"""
import struct
from catalog import Master,u16,u32,encode,decode
from story_scripts_25 import command,records,text_at,wrap,NONE,DEAD
from regional_five_content import SCENARIOS,BRIDGE

ENEMIES=[
 [1204]*5+[1443]*5+[1092]*4+[1415]*2,
 [1092]*5+[1191]*4+[1259]*3+[1386]*4,
 [1233]*8+[1204]*4+[1092]*4,
 [1332]*6+[1138]*6+[1204]*4,
 [1054]*6+[1246]*4+[1355]*4+[1374]*2]

def stage_base(m):
 p=m.tables['Stag'][0]
 counts=struct.unpack_from('<3H',m.b,p+12)
 assert counts[2]>=40
 return p+32+sum(counts[:2])*12

class Logo:
 def __init__(self,template,speakers):
  self.old=template;self.speakers=speakers;self.rows=[];self.labels={};self.fix=[];self.funcs=[];self.events=[];self.gates=[];self.messages=[]
  self.nc=u32(template,64)
  self.common=[text_at(template,i) for i in range(self.nc)]
  self.prefix=[list(struct.unpack_from('<24I',template,u32(template,36)+i*96)) for i in range(u32(template,32))]
  self.history=[u32(template,u32(template,60)+i*4) for i in range(u32(template,56)) if u32(template,u32(template,60)+i*4)<len(self.prefix)]
  assert all(r[1]<len(self.history) for r in self.prefix if r[0]==0x19)
  self.strings=[]
  self.dialogue=next(r.copy() for r in records(template) if r[0]==0x30 and r[13]==0x100a8 and r[3]==NONE)
 def emit(self,op,*args):self.rows.append(command(op,*args));return len(self.rows)-1
 def string(self,s):
  raw=encode(s);assert decode(raw)==s and len(raw)<128
  self.strings.append(raw);return self.nc+len(self.strings)-1
 def say(self,lines):
  for who,text in lines:
   for t in wrap(who,text):
    r=self.dialogue.copy();r[1]=len(self.history);r[2]=self.string(t);r[4]=self.speakers[who];r[5]=0
    self.history.append(len(self.prefix)+len(self.rows));self.messages.append(dict(who=who,text=t,sid=r[2],label=r[1]));self.rows.append(r)
 def label(self,name):assert name not in self.labels;self.labels[name]=len(self.rows)
 def flagguard(self,group,bit,target):
  self.emit(0x93,0x10071,group,bit,0x800f,NONE,NONE,NONE)
  i=self.emit(0x91,0x800f,0x8000,0,DEAD,DEAD,0);self.fix.append((i,target))
 def story(self,lines):
  # A literal comparison is independently switched by the original story option.
  self.emit(0x9a,0,0x800e);i=self.emit(0x91,0x800e,0x8000,0,DEAD,DEAD,0);self.gates.append(i)
  self.say(lines);self.rows[i][7]=len(self.rows)-i
 def function(self,name,event,scene=None,bit=None):
  self.label(name);self.funcs.append(name);self.events.append((event,len(self.funcs)))
  self.emit(0x26)
  if scene is not None:self.emit(0x79,0x10018,scene,NONE)
  if bit is not None:self.flagguard(0,bit,name+'_exit')
 def end(self,name,bit=None):
  if bit is not None:self.emit(0xba,0x10071,0,bit)
  self.label(name+'_exit');self.emit(0x3e);self.emit(0x25)
 def finish(self):
  for i,target in self.fix:self.rows[i][7]=self.labels[target]-i
  h=bytearray(self.old[:192]);prefixevent=command(0x42,18,0,NONE,NONE)
  events=[command(0x42,kind,desc,0 if kind==28 else NONE,NONE) for kind,desc in self.events]
  b=h
  def append(data):p=len(b);b.extend(data);return p
  def rows(rs):return b''.join(struct.pack('<24I',*r) for r in rs)
  struct.pack_into('<II',b,16,1,append(rows([prefixevent])))
  struct.pack_into('<II',b,24,len(events),append(rows(events)))
  struct.pack_into('<II',b,32,len(self.prefix),append(rows(self.prefix)))
  struct.pack_into('<II',b,40,len(self.rows),append(rows(self.rows)))
  ds=[(0,0,0,0xffffffff)]+[(1,0,self.labels[n],0) for n in self.funcs]
  struct.pack_into('<II',b,48,len(ds),append(b''.join(struct.pack('<4I',*d) for d in ds)))
  struct.pack_into('<II',b,56,len(self.history),append(struct.pack('<%dI'%len(self.history),*self.history)))
  strings=self.common+self.strings+[b''];pointers=[];pool=bytearray()
  for s in strings:pointers.append(len(pool));pool.extend(s+b'\0')
  table=append(struct.pack('<%dI'%len(pointers),*pointers));poolat=append(pool)
  b.extend(bytes((-len(b))%4));struct.pack_into('<II',b,64,self.nc,table);struct.pack_into('<I',b,76,poolat)
  struct.pack_into('<III',b,80,len(self.strings)+1,table+self.nc*4,len(self.strings))
  struct.pack_into('<I',b,4,len(b));struct.pack_into('<I',b,108,len(b))
  assert all(text_at(b,i)==s for i,s in enumerate(strings))
  assert all(u32(b,u32(b,60)+r[1]*4)==len(self.prefix)+i for i,r in enumerate(self.rows) if r[0]==0x30)
  return bytes(b),dict(functions={n:self.labels[n] for n in self.funcs},story_gates=self.gates,messages=self.messages,rows=len(self.rows),prefix=len(self.prefix))

def mission_logo(template,scenario,speakers,mapkey,nextindex):
 a=Logo(template,speakers)
 a.function('defeat',28)
 # Native type28 is a polled failure callback, not an unconditional loss event.
 # Do not evaluate annihilation before selected-party deployment has finished.
 a.emit(0x93,0x10071,0,0,0x800f,NONE,NONE,NONE)
 i=a.emit(0x91,0x800f,0x8000,1,DEAD,DEAD,0);a.fix.append((i,'defeat_exit'))
 a.emit(0x7a,0x100ad,0,0);a.emit(0xa1,0xffffffff,0);a.end('defeat')
 a.function('map',2);a.emit(0xb0,60,0x10014);a.emit(0xbd,mapkey);a.emit(0x79,0x10049,NONE,NONE);a.emit(0xba,0x10071,4,7);a.end('map')
 a.function('opening',27,0,0)
 a.emit(0xb0,1,0x10012);a.emit(0xaf,1,0x10014)
 a.emit(0xca,0,250) # Actual enemy actors, side2, group0.
 a.emit(0xc3,12);a.emit(0x6c,30,0) # Stock selected-party deployment, not recruitment.
 a.emit(0x68,53);a.emit(0xbc,53);a.emit(0xaf,60,0x10012)
 a.say(scenario['opening']);a.story(scenario['story_opening'])
 a.emit(0x7b,0x100ef,0x10086,0x10041)
 a.emit(0x5a,0x100ed,a.string('적 전멸'))
 a.emit(0x5a,0x10072,a.string('아군 전멸'))
 a.emit(0x5a,0x100b7,a.string('없음'))
 a.emit(0x5b,0x1ff);a.emit(0xd1,0);a.end('opening',0)
 # Mid-operation report is issued at the first normal battle callback. It does
 # not claim a terrain capture, enemy-count threshold or an imaginary NPC rescue.
 a.function('report',27,2,1)
 a.say(scenario['mid']);a.story(scenario['story_mid']);a.emit(0x7b,0x100ef,0x10086,0x10041);a.end('report',1)
 a.function('ending',27,1,2)
 a.emit(0x93,0x10071,0,0,0x800f,NONE,NONE,NONE)
 i=a.emit(0x91,0x800f,0x8000,1,DEAD,DEAD,0);a.fix.append((i,'ending_exit'))
 a.emit(0x7a,0x100ad,1,0) # Native army selector1 resolves to enemy side2.
 a.say(scenario['ending']);a.story(scenario['story_ending']);a.emit(0x7b,0x100ef,0x10086,0x10041)
 a.emit(0x6d);a.emit(0x67);a.emit(0xa1,nextindex,0);a.end('ending',2)
 return a.finish()

def append_strings(part,new):
 n=u32(part,8);shift=len(new)*4
 out=bytearray(part[:12]);out.extend(struct.pack('<%dI'%n,*(u32(part,12+i*4)+shift for i in range(n))))
 out.extend(bytes(shift));out.extend(part[12+n*4:])
 for i,s in enumerate(new):
  struct.pack_into('<I',out,12+(n+i)*4,len(out));out.extend(s+b'\0')
 out.extend(bytes((-len(out))%4));struct.pack_into('<II',out,4,len(out),n+len(new));return out

def master_titles(old):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))}
 titleid=u32(parts[0x80],8);parts[0x80]=append_strings(parts[0x80],[encode(s['title']) for s in SCENARIOS])
 sb=stage_base(m)-m.tables['Stag'][0];notes=[]
 for i,s in enumerate(SCENARIOS):
  p=sb+(s['key']-2000)*12
  assert parts[0x58][p:p+2]==b'\xff\xff' # Stag is header field0x58.
  r=bytearray(parts[0x58][sb+32*12:sb+33*12]);struct.pack_into('<Hhh',r,0,titleid+i,-1,-1);r[6]=s['number'];r[7]=0;r[10]=0
  parts[0x58][p:p+12]=r;notes.append(dict(key=s['key'],number=s['number'],title_id=titleid+i))
 parts[0x58][sb+33*12+6]=40;parts[0x58][sb+34*12+6]=41
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old);out.extend(bytes(len(old)-used));n=Master(out)
 for tag in m.tables:
  if tag in ['Stag','Strg']:continue
  p,size,_=m.tables[tag];q=n.tables[tag][0];assert old[p:p+size]==out[q:q+size],tag
 assert all(m.text(i)==n.text(i) for i in range(m.tables['Strg'][2]))
 return bytes(out),dict(titles=notes,used_bytes=used,renumbered={2033:40,2034:41})
