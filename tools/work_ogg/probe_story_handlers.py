from probe_native import *
import numpy as np

def main():
 tables=(ROOT.parent/'work_ogs/runtime/beowulf/current_user_ram.bin').read_bytes();old=elfmem(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso')
 new=(OUT/'terrain_fresh_ram.bin').read_bytes();a=np.frombuffer(new,dtype='<u4');start,end=0x100000//4,0x800000//4
 md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN);md.skipdata=True
 print('OLD TABLE')
 for op in [0x30,0x33,0x5a,0x5b,0x59,0x84,0x85,0x8b,0x8c,0x95,0x21,0xc5]:
  p=0x868190+op*12;print(hex(op),[hex(u32(tables,p+j)) for j in [0,4,8]])
  pc=u32(tables,p+8);w=np.frombuffer(old[pc:pc+128],dtype='<u4');mask=np.array([0xffff0000 if x>>26 else 0xffffffff for x in w],dtype=np.uint32);score=np.zeros(end-start,dtype=np.uint16);exact=score.copy()
  for j,x in enumerate(w):v=a[start+j:end+j];score+=((v&mask[j])==(x&mask[j]));exact+=(v==x)
  rank=score.astype(np.uint32)*64+exact;best=np.argsort(rank)[-3:][::-1];print('MATCH',[(hex((int(k)+start)*4),int(score[k]),int(exact[k])) for k in best])
  if op in [0x5a,0x5b,0x95]:
   pc=(int(best[0])+start)*4;print('DISASM',hex(pc))
   for x in md.disasm(new[pc:pc+160],pc):print(hex(x.address),x.mnemonic,x.op_str)
 # OGG's dispatch table is found from the matched dialogue handler pointer.

if __name__=='__main__':main()
