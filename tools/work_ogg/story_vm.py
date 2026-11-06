from catalog import *
from r5900_scalar_check import CPU
from compare_ogs_units import getmaster
from build_patch import command

RAM=OUT/'terrain_fresh_ram.bin'
TABLE=0x572d40

class VM:
 def __init__(self):
  self.ram=RAM.read_bytes();self.cpu=CPU(self.ram);self.ctx=0x1600000;self.rec=0x1700000;self.cpu.r[28]=0x31def0
  # OGG startup initializes gp at this executable-specific address.
  self.save=u32(self.ram,0x31df24);self.master=u32(self.ram,0x31df20);self.diff=u32(self.ram,0x31df2c)
  self.cpu.write(self.ctx+0x2870,0x319d40,4)
  for i in range(16):self.cpu.write(self.ctx+0x74ec+i*4,0xffffffff,4)
 def op(self,r):
  c=self.cpu
  for i,v in enumerate(r):c.write(self.rec+i*4,v,4)
  c.write(self.ctx+0x7538,0,4)
  fn=u32(self.ram,TABLE+r[0]*12+8);return c.run(fn,[self.ctx,self.rec],limit=1000000)
 def reg(self,reg,value):return self.op(command(0x9a,value,reg))
 def readreg(self,reg):
  self.cpu.run(0x53fd20,[self.ctx,reg]);return struct.unpack('<f',struct.pack('<I',self.cpu.fpr[0]))[0]
 def load_master(self,blob):
  c=self.cpu;dest=0x1900000;c.mem[dest:dest+len(blob)]=blob
  for i,k in enumerate(range(0x18,0x8c,4)):
   p=dest+u32(blob,k)
   for r,v in [(0,p),(4,c.read(p,4)),(8,c.read(p+4,4)),(12,c.read(p+8,4)),(16,p),(20,p+12)]:c.write(self.master+0x28+i*24+r,v,4)
 def birth(self,row):
  c=self.cpu;game=0x1800000;source=0x1880000;obj=0x1780000
  c.write(obj+0x28,game,4)
  for rel,value in [(0x41e0,self.master),(0x41e4,self.save),(0x41ec,self.diff)]:c.write(game+rel,value,4)
  c.mem[source:source+336]=row;c.write(obj+0x33e34,source,4)
  return c.run(0x20d020,[obj,0],limit=1000000)

def main():
 vm=VM();c=vm.cpu;print('gp',hex(c.r[28]),'master/save',hex(vm.master),hex(vm.save))
 print('reg',vm.reg(0x8000,123),vm.readreg(0x8000))
 for group in [0x1c,0x1d,0x1e,0x1f]:
  before=len(c.writes);print('set flag',group,vm.op(command(0xba,0x10071,group,0)))
  print('flag',vm.op(command(0x93,0x10071,group,0,0x8000,0xdeaddeed,0xdeaddeed,0xdeaddeed)),vm.readreg(0x8000),'writes',[(hex(a),n,hex(pc)) for a,n,pc in c.writes[before:] if not 0x15f0000<a<0x1800000][-8:])
 m=getmaster(ROOT.parent/'SRWOGS_EX_K_TEST.ISO');b=bytearray(m.b)
 for tag in ['UTbl','PTbl']:struct.pack_into('<H',b,m.tables[tag][0]+12+0x7ff*2,u16(b,m.tables[tag][0]+12+0x700*2))
 vm.load_master(b)
 a=json.loads((OUT/'MAP.BIN.13.json').read_text());e=next(x for x in a['entries'] if 2001 in x['keys'])
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
  off,n=struct.unpack('<II',read(f,a['directory']+8+e['index']*8,8));raw=read(f,a['directory']+off,n)
 row=bytearray(raw[44+11*336:44+12*336])
 for off in [0,32]:struct.pack_into('<I',row,off,0x7ff)
 for off in [0x60,0x74,0x88]:struct.pack_into('<I',row,off,0xffff07ff)
 for off in [0x38,0x3c,0x40,0x44,0x48,0x4c]:struct.pack_into('<I',row,off,2)
 print('missing unit',c.run(0x244c20,[vm.save,0x7ff,0,0]))
 print('birth',vm.birth(row));slot=c.run(0x244c20,[vm.save,0x7ff,0,0]);pilot=c.run(0x244a40,[vm.save,0x7ff,1,0]);print('unit/pilot',slot,pilot)
 print('grades',[c.run(0x248950,[vm.save,x,slot,0]) for x in [0xd,0xe,0xf,0x10]])
 print('rowwords',[(hex(i),hex(u32(row,i))) for i in range(0x20,0xa0,4)])

if __name__=='__main__':main()
