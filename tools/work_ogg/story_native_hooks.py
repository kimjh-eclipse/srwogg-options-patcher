"""Small OGG-native hooks, tested offline before any ISO write.

Two equivalent zero-fill loops make room inside the existing executable.
No new ELF section, RAM allocation, or file growth is used.
"""
from story_vm import VM,CPU,ROOT,OUT,u32,struct

def I(op,s,t,n):return (op<<26)|(s<<21)|(t<<16)|(n&65535)
def R(s,t,d,fn):return (s<<21)|(t<<16)|(d<<11)|fn
def J(op,pc):return (op<<26)|((pc>>2)&0x3ffffff)
def branch(op,s,t,pc,target):return I(op,s,t,(target-pc-4)//4)
def code(ws):return struct.pack('<%dI'%len(ws),*ws)

PHASE=0x206368
RET=PHASE+9*4
AVG=0x206394
AVG_BODY=0x2060a4

def patches(ram):
 # a0/v0/v1/a1/a2/a3/t0..t4/at/fp/ra = 4/2/3/5/6/7/8..12/1/30/31
 a=[0x44800000,I(9,4,5,0x80),I(9,0,6,96),I(43,5,0,0),I(9,6,6,-1),
    branch(5,6,0,0x20634c,0x206344),I(9,5,5,4),I(9,4,5,0x180),
    I(9,0,6,0x20),R(0,0,3,33),J(2,0x2063ac),0]
 b=[I(9,4,6,0x80),I(9,0,7,96),I(43,6,0,0),I(9,7,7,-1),
    branch(5,7,0,0x206088,0x206080),I(9,6,6,4),I(9,4,6,0x180),
    I(9,0,7,0x20),R(0,0,3,33),J(2,0x2060e8),0]
 phase=[I(36,2,3,0x5d),branch(4,3,0,PHASE+4,RET),I(15,0,1,0x32),
        I(35,1,1,-0x20d4),I(35,1,1,0x1000),R(1,3,1,43),
        branch(4,1,0,PHASE+24,RET),I(33,2,3,0x62),R(2,3,2,33),R(31,0,0,8),0]
 head=[I(35,30,7,0),I(9,0,8,-1),branch(5,7,8,AVG+8,RET),I(15,0,9,2),
       J(2,AVG_BODY),I(13,9,9,0x5cfc)]
 body=[R(4,9,9,33),I(9,0,10,192),R(0,0,11,33),R(0,0,8,33),
       I(36,9,12,2),branch(4,12,0,AVG_BODY+20,AVG_BODY+36),I(37,9,12,0xa),
       R(11,12,11,33),I(9,8,8,1),I(9,10,10,-1),
       branch(5,10,0,AVG_BODY+40,AVG_BODY+16),I(9,9,9,92),
       branch(4,8,0,AVG_BODY+48,RET),I(9,0,7,2500),R(11,8,0,27),R(31,0,0,8),R(0,0,7,18)]
 assert len(code(a+phase+head))==0x74 and len(code(b+body))==0x70
 assert u32(ram,0x2788f8)==R(31,0,0,8)
 assert u32(ram,0x20d478)==I(35,30,7,0)
 assert u32(ram,0x275af0)==I(36,2,2,0x5d)
 assert u32(ram,0x206338)==0x44800000 and u32(ram,0x206078)==I(43,6,0,0x80)
 return [(0x206338,code(a+phase+head),'equivalent zero-fill A / phased weapon / average EXP'),
         (0x206078,code(b+body),'equivalent zero-fill B / average EXP body'),
         (0x2788f8,code([J(2,PHASE)]),'unit resolver phase hook'),
         (0x20d478,code([J(3,AVG)]),'initial EXP sentinel hook'),
         # This optional property is zero in every existing SHARED/IM unit.
         # Keep its public getter zero while using the byte as private metadata.
         (0x275af0,code([R(0,0,2,33)]),'preserve stock zero property / hide private phase marker')]

def install(cpu):
 for p,b,label in patches((OUT/'terrain_fresh_ram.bin').read_bytes()):cpu.mem[p:p+len(b)]=b

def test_loops():
 ram=(OUT/'terrain_fresh_ram.bin').read_bytes();checks=0
 for start,end,arg in [(0x206338,0x2063ac,5),(0x206078,0x2060e8,6)]:
  for align in [0,4,8,12]:
   cs=[CPU(ram),CPU(ram)];install(cs[1]);base=0x1801000+align
   for c in cs:
    for i in range(1,32):c.r[i]=0xabc000+i
    c.r[4]=base;c.r[arg]=base;c.r[arg+1]=0
    c.fpr=[0x12345678+i for i in range(32)]
    c.mem[base:base+0x220]=b'\xa5'*0x220
    c.run(start,stop=end)
   assert cs[0].r==cs[1].r,(hex(start),'register mismatch')
   assert cs[0].fpr==cs[1].fpr
   assert cs[0].mem[base:base+0x220]==cs[1].mem[base:base+0x220]
   assert {(a,n) for a,n,p in cs[0].writes}=={(a,n) for a,n,p in cs[1].writes}
   checks+=1
 return checks

def test_average():
 checks=0
 for exps in [[],[1000],[1500,3500,4000],[49000]*191]:
  for value in [0,2500,49000,0xffffffff]:
   v=VM();c=v.cpu;install(c);ptr=0x1800100;c.r[30]=ptr;c.write(ptr,value,4)
   for i,e in enumerate(exps):
    p=v.save+0x25cfc+i*92;c.write(p+2,1,1);c.write(p+0xa,e,2)
   c.run(AVG,[v.save]);got=c.r[7]&0xffffffff
   expect=value if value!=0xffffffff else (sum(exps)//len(exps) if exps else 2500)
   assert got==expect,(value,exps[:4],got,expect);checks+=1
 return checks

if __name__=='__main__':
 print('Equivalent loops',test_loops(),'average EXP',test_average())
