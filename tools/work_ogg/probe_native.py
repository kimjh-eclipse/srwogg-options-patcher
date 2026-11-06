from inspect_iso import *
import numpy as np
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS64,CS_MODE_LITTLE_ENDIAN
def elfmem(path):
 with path.open('rb') as f:
  e=next(x for x in inventory(f) if x['name'].startswith('SLPS_'));b=read(f,e['offset'],e['size'])
 mem=bytearray(32<<20)
 for i in range(struct.unpack_from('<H',b,44)[0]):
  p=u32(b,28)+i*struct.unpack_from('<H',b,42)[0]
  typ,off,va,pa,fs,ms,flags,align=struct.unpack_from('<8I',b,p)
  if typ==1:mem[va:va+fs]=b[off:off+fs]
 return mem
def main():
 old=elfmem(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso');new=elfmem(SOURCE);a=np.frombuffer(new,dtype='<u4');start=0x100000//4;end=0x300000//4
 for pc in [0x1d5970,0x1abc50,0x1ab6f0,0x1a9b70,0x1a7d40,0x1a2900]:
  w=np.frombuffer(old[pc:pc+128],dtype='<u4');mask=np.array([0xffff0000 if x>>26 else 0xffffffff for x in w],dtype=np.uint32);score=np.zeros(end-start,dtype=np.uint16)
  for j,x in enumerate(w):score+=((a[start+j:end+j]&mask[j])==(x&mask[j]))
  best=np.argsort(score)[-3:][::-1];print(hex(pc),[(hex((int(x)+start)*4),int(score[x])) for x in best])
  if pc==0x1d5970:
   p=(int(best[0])+start)*4;md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN);md.skipdata=True
   for x in md.disasm(bytes(new[p:p+0x250]),p):print(hex(x.address),x.mnemonic,x.op_str)
 (OUT/'elf_ram.bin').write_bytes(new)
if __name__=='__main__':main()
