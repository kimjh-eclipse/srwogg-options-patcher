"""Read-only ISO9660/OGG resource inventory. Never alters the supplied ISO."""
from pathlib import Path
import hashlib,json,struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'SRWOGS_EX_K.ISO'
OUT=ROOT/'analysis'
SECTOR=2048
def u32(b,p=0):return struct.unpack_from('<I',b,p)[0]
def read(f,p,n):
    f.seek(p);b=f.read(n)
    if len(b)!=n:raise ValueError((p,n,len(b)))
    return b
def record(b):
    return dict(name=b[33:33+b[32]].decode('ascii'),offset=u32(b,2)*SECTOR,size=u32(b,10),directory=bool(b[25]&2))
def inventory(f):
    p=read(f,16*SECTOR,SECTOR);assert p[:7]==b'\x01CD001\x01'
    entries=[]
    def walk(r,parent=''):
        b=read(f,r['offset'],r['size']);pos=0
        while pos<len(b):
            n=b[pos]
            if not n:pos=(pos//SECTOR+1)*SECTOR;continue
            e=record(b[pos:pos+n]);pos+=n
            if e['name'] in ('\0','\1'):continue
            e['path']=parent+'/'+e['name'];entries.append(e)
            if e['directory']:walk(e,e['path'])
    walk(record(p[156:156+p[156]]));return entries
def lice(f,base,limit):
    h=read(f,base,16)
    if h[:4]!=b'LICE':return None
    di,count,slots=struct.unpack_from('<III',h,4)
    assert di+8+count*8<=limit
    mapping=struct.unpack('<%dH'%slots,read(f,base+16,slots*2))
    d=read(f,base+di,8+count*8);assert d[:4]==b'Wpbb' and u32(d,4)==count
    entries=[]
    for i in range(count):
        off,size=struct.unpack_from('<II',d,8+8*i);assert di+off+size<=limit
        at=base+di+off;magic=read(f,at,min(32,size))
        entries.append(dict(index=i,keys=[k for k,v in enumerate(mapping) if v==i],offset=at,size=size,head=magic.hex()))
    return dict(offset=base,directory=base+di,count=count,slots=slots,entries=entries)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(source=str(SOURCE),size=SOURCE.stat().st_size)
    with SOURCE.open('rb') as f:
        report['files']=inventory(f)
        for e in report['files']:
            if e['directory']:continue
            h=read(f,e['offset'],min(e['size'],32));e['head']=h.hex()
            arc=lice(f,e['offset'],e['size'])
            if arc:
                (OUT/(e['name'].split(';')[0]+'.json')).write_text(json.dumps(arc,ensure_ascii=False,indent=2),encoding='utf-8')
                e['archive_count']=arc['count'];e['archive_slots']=arc['slots']
            if e['name'].startswith('SYSTEM.CNF') or h[:4]==b'\x7fELF':
                (OUT/e['name'].split(';')[0]).write_bytes(read(f,e['offset'],e['size']))
        f.seek(0);sha=hashlib.sha256()
        while b:=f.read(16*1024*1024):sha.update(b)
        report['sha256']=sha.hexdigest()
    (OUT/'iso_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
