"""OGG-native reward and hostile-stat hooks. All operations prepare byte edits."""
from story_native_hooks import I,R,J,branch,code
from probe_native import *

SQ_START,SQ_END=0x1132e4,0x113374
FLOAT_START,FLOAT_END=0x1d56b0,0x1d57cc
PILOT=0x113320
HP=0x1d5740
MONEY=0x113358
MONEY_ELSE=0x1d5738
MONEY_TAIL=0x1d57b4
REWARD=0x4a9fa0
STAT_GETTERS=[0x22ff10,0x230080,0x2301f0,0x230360,0x2304d0,0x230640]

class Asm:
 def __init__(self,start):self.start=start;self.words=[];self.labels={};self.fix=[]
 @property
 def pc(self):return self.start+len(self.words)*4
 def emit(self,w):self.words.append(w)
 def i(self,op,s,t,n):self.emit(I(op,s,t,n))
 def r(self,s,t,d,fn):self.emit(R(s,t,d,fn))
 def label(self,name):self.labels[name]=self.pc
 def b(self,op,s,t,name):self.fix.append((len(self.words),op,s,t,name));self.emit(0)
 def data(self):
  for idx,op,s,t,name in self.fix:self.words[idx]=branch(op,s,t,self.start+idx*4,self.labels[name])
  return code(self.words)

def compact_sq():
 a=Asm(SQ_START);a.i(9,0,3,28);a.label('first');a.i(31,2,0,0);a.i(9,3,3,-1);a.b(5,3,0,'first');a.i(9,2,2,16)
 a.i(9,2,2,0x40);a.i(9,0,3,8);a.label('second');a.i(31,2,0,0);a.i(9,3,3,-1);a.b(5,3,0,'second');a.i(9,2,2,16)
 a.i(9,2,2,-0x280);a.i(35,29,3,12);a.emit(J(2,SQ_END));a.emit(0)
 assert a.pc==PILOT;return a.data()

def compact_float():
 a=Asm(FLOAT_START);a.i(9,29,29,-16)
 for off in [0x378,0x37c,0x380,0x384]:a.i(43,4,0,off)
 a.i(9,4,5,0x390);a.i(9,0,3,-1);a.i(43,5,3,-8);a.i(43,5,3,-4);a.i(9,0,6,27)
 a.label('second');a.i(43,5,0,0);a.i(9,6,6,-1);a.b(5,6,0,'second');a.i(9,5,5,4)
 a.i(15,0,3,0x35);a.i(49,3,2,-0x33c8);a.i(49,3,1,-0x33c4);a.i(49,3,0,-0x33c0);a.i(9,0,6,8)
 a.label('floats');a.i(57,5,2,0);a.i(57,5,1,4);a.i(57,5,0,8);a.i(9,6,6,-1);a.b(5,6,0,'floats');a.i(9,5,5,12)
 a.i(15,0,5,0x35);a.i(9,5,5,-0x33c8);a.i(9,0,6,12)
 a.i(57,29,2,0);a.i(57,29,1,4);a.i(57,29,0,8);a.i(43,4,0,0x370);a.r(31,0,0,8);a.i(9,29,29,16)
 assert a.pc==MONEY_ELSE,(hex(a.pc),hex(MONEY_ELSE));return a.data()

def hostility(a,actor,end):
 a.i(35,actor,2,0x10);a.b(4,2,0,end);a.i(36,actor,3,0x74)
 a.i(12,3,3,7);a.r(2,3,2,33);a.i(15,0,3,0x15);a.r(2,3,2,33)
 a.i(36,2,2,0x573c);a.i(12,2,2,1)

def pilot_helper():
 a=Asm(PILOT);a.r(5,0,18,45);hostility(a,4,'ret');a.b(0x15,2,0,'ret');a.i(9,18,18,5);a.label('ret');a.r(31,0,0,8);a.emit(0)
 assert len(a.data())==56 and a.pc<=SQ_END;return a.data()

def hp_helper():
 a=Asm(HP);a.i(43,29,31,0x28);a.i(43,29,2,0x2c);hostility(a,17,'done')
 a.b(4,2,0,'done');a.i(35,17,6,0x18);a.i(35,17,4,4);a.i(9,0,5,0x14);a.emit(J(3,0x249300));a.r(0,0,7,45)
 a.b(6,2,0,'done');a.i(11,2,3,20000);a.b(4,3,0,'done');a.i(9,0,3,10)
 a.r(2,3,0,27);a.r(0,0,2,18);a.r(16,2,16,33)
 a.label('done');a.i(35,29,31,0x28);a.i(35,29,2,0x2c);a.i(35,17,4,0x168);a.r(31,0,0,8);a.emit((2<<16)|(3<<11)|(2<<6))
 assert a.pc<=FLOAT_END,(len(a.data()),hex(a.pc));return a.data()

def money_helper():
 a=Asm(MONEY);a.emit(0x00101040);a.emit(0x00501021);a.emit(0x00021040);a.i(9,0,3,5);a.r(2,3,0,27);a.emit(J(2,MONEY_TAIL));a.r(0,0,16,18)
 tail=Asm(MONEY_TAIL);tail.i(35,29,2,0x11c);tail.labels['else']=MONEY_ELSE;tail.b(4,2,0,'else');tail.emit(0);tail.emit(J(2,0x4aa1b4));tail.emit(0)
 other=code([J(2,0x4aa1c4),0])
 assert a.pc==SQ_END and tail.pc<=FLOAT_END and MONEY_ELSE+len(other)==HP
 return a.data(),tail.data(),other

def native_plan(target):
 main=elfmem(target);edits=[];notes={}
 with target.open('rb') as f:
  elf=next(e for e in inventory(f) if e['name'].startswith('SLPS_'));mp=next(e for e in inventory(f) if e['name']=='MPOL.BIN;1');overlay=read(f,mp['offset'],mp['size'])
  assert overlay[:4]==b'MWo3' and u32(overlay,8)==0x422000
  def addva(pc,new,label):
   offset=elf['offset']+0x180+pc-0x100000;old=read(f,offset,len(new));assert old==main[pc:pc+len(new)]
   edits.append((offset,old,new,label));return old
  money,tail,other=money_helper()
  sq=compact_sq()+pilot_helper()+money;assert len(sq)==SQ_END-SQ_START
  original=addva(SQ_START,sq,'equivalent SQ clear / hostile pilot +5')
  assert [u32(original,i*4) for i in range(36)]==[I(31,2,0,o) for o in list(range(0,0x1c0,16))+list(range(0x200,0x280,16))]
  init=compact_float()+other+hp_helper()+tail;init=init.ljust(FLOAT_END-FLOAT_START,b'\0');addva(FLOAT_START,init,'equivalent object initializer / hostile base HP +10 percent / money return paths')
  for fn in STAT_GETTERS:
   assert u32(main,fn+0x18)==0x00a0902d and u32(main,fn+0x1c)==0x7fb00000
   addva(fn+0x18,code([J(3,PILOT)]),'hostile pilot combat stat +5')
  assert main[0x2368b0:0x2368b8]==code([I(35,17,4,0x168),(2<<16)|(3<<11)|(2<<6)])
  addva(0x2368b0,code([J(3,HP),0]),'hostile small-unit HP hook')
  def addov(pc,before,after,label):
   off=pc-0x422000;assert overlay[off:off+len(before)]==before,(hex(pc),overlay[off:off+len(before)].hex())
   edits.append((mp['offset']+off,before,after,label))
  assert u32(overlay,REWARD-0x422000)==0x27bdfee0
  addov(0x4aa1ac,code([0x10400005,0]),code([J(2,MONEY),0]),'scale final funds before accumulation')
  addov(0x4aa644,code([0]),code([0x8e030244]),'preserve PP accumulator load in common minimum-check delay')
  # Gaiden reuses S1 across copilots. Scale a temporary, so later pilots do
  # not accidentally receive progressively compounded 4x/8x/16x PP.
  addov(0x4aa648,code([0x8e030244]),code([(17<<16)|(2<<11)|(1<<6)]),'double each final PP award in temporary')
  addov(0x4aa64c,code([R(3,17,3,33)]),code([R(3,2,3,33)]),'accumulate scaled PP without changing shared per-pilot amount')
 notes.update(pilot_helper=PILOT,hp_helper=HP,money_helper=MONEY,reward_function=REWARD,
              loop_ranges=[[SQ_START,SQ_END],[FLOAT_START,FLOAT_END]],overlay='MPOL.BIN',overlay_base=0x422000)
 return edits,notes
