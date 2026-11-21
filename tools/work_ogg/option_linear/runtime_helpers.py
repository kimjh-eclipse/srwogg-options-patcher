from pathlib import Path
import sys,struct
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT)]
from pack_io import Pack,Image
from inspect_iso import inventory,read,u32,lice,OUT
from catalog import Master
from story_vm import VM,CPU
from audit_story_layout import TARGET

def rawmaster(f,name):
    e=next(e for e in inventory(f) if e['name']==name+';1');a=lice(f,e['offset'],e['size']);e=a['entries'][3];a=lice(f,e['offset'],e['size']);e=a['entries'][0]
    return e,Master(read(f,e['offset'],e['size']))

def ram(p,mask):
    with Image(p,mask,TARGET) as image:
        entries=inventory(image);elf=next(e for e in entries if e['name'].startswith('SLPS_'));mp=next(e for e in entries if e['name']=='MPOL.BIN;1')
        out=bytearray((OUT/'terrain_fresh_ram.bin').read_bytes());overlay=read(image,mp['offset'],mp['size']);out[0x422000:0x422000+len(overlay)]=overlay
        for (at,o,b),data in zip(p.regions,image.data):
            lo=max(at,elf['offset']+0x180);hi=min(at+len(data),elf['offset']+elf['size'])
            if lo<hi:
                pc=0x100000+lo-elf['offset']-0x180;out[pc:pc+hi-lo]=data[lo-at:hi-at]
        return bytes(out)

def load_master(vm,blob):
    vm.load_master(blob)
    for i,k in reversed(list(enumerate(range(0x18,0x8c,4)))):
        if i>16:
            a=vm.master+0x28+i*24;vm.cpu.mem[a+4:a+28]=vm.cpu.mem[a:a+24]
    vm.cpu.write(vm.master+0x1a8+24,0x1900000+Master(blob).tables['Stag'][0]+32,4)

class PartyCPU(CPU):
    def step(self):
        word=self.read(self.pc,4)
        if word>>26==17 and (word>>21)&31==16 and word&63==36:
            source=(word>>11)&31;dest=(word>>6)&31
            value=struct.unpack('<f',struct.pack('<I',self.fpr[source]))[0]
            assert value.is_integer(),'This check only supplies exact integer CVT.W.S inputs'
            self.fpr[dest]=int(value)&0xffffffff;self.pc+=4;self.count+=1
        elif self.pc in [0x213d90,0x214440]:
            self.write(0x17e0000+0x18,0xffffffff,4);self.put(2,0x17e0000);self.pc=self.r[31]&0xffffffff;self.pending=None;self.count+=1
        else:super().step()

def machine(base,master):
    v=VM(base);v.cpu=PartyCPU(base);v.cpu.r[28]=0x31def0;v.cpu.write(v.ctx+0x2870,0x319d40,4);v.cpu.write(0x46ecec,0,4);load_master(v,master);return v
