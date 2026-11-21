"""Read OGGOPT01 formats 1/2 and compose ordinary and conditional edits."""
from pathlib import Path
import struct,io,zlib,bisect,hashlib

class Pack:
    def __init__(self,path):
        f=io.BytesIO(Path(path).read_bytes())
        def n(fmt):return struct.unpack(fmt,f.read(struct.calcsize(fmt)))
        def blob():return f.read(n('<I')[0])
        def edits():return [(at,f.read(size)) for at,size in (n('<QI') for _ in range(n('<I')[0]))]
        assert f.read(8)==b'OGGOPT01'
        self.version=n('<I')[0];assert self.version in [1,2]
        self.size=n('<Q')[0];self.source_sha=f.read(32);self.count=n('<I')[0]
        self.options=[(blob().decode('utf8'),blob().decode('utf8')) for _ in range(self.count)]
        self.regions=[]
        for _ in range(n('<I')[0]):
            at,size=n('<QI');original=zlib.decompress(blob(),-15);base=zlib.decompress(blob(),-15)
            assert len(original)==len(base)==size;self.regions.append((at,original,base))
        self.features=[edits() for _ in range(self.count)]
        self.conditional=[]
        if self.version==2:
            for _ in range(n('<I')[0]):
                require,forbid=n('<II');assert not require&forbid and (require|forbid)<1<<self.count
                self.conditional.append(dict(require=require,forbid=forbid,edits=edits()))
        self.profiles={}
        for _ in range(n('<I')[0]):
            mask=n('<I')[0];self.profiles[f.read(32)]=mask
        self.source_fingerprint=f.read(32);self.legacy={}
        for _ in range(n('<I')[0]):
            digest=f.read(32);self.legacy[digest]=n('<I')[0]
        assert not f.read();self.starts=[r[0] for r in self.regions]
    def data(self,mask):
        assert 0<=mask<1<<self.count
        out=[bytearray(b) for at,o,b in self.regions]
        for bit,es in enumerate(self.features):
            if mask&(1<<bit):
                for at,b in es:setbytes(self.regions,out,at,b)
        for c in self.conditional:
            if mask&c['require']==c['require'] and not mask&c['forbid']:
                for at,b in c['edits']:setbytes(self.regions,out,at,b)
        return out

_STARTS={}
def setbytes(regions,data,at,b):
    item=_STARTS.get(id(regions))
    if item is None:item=(regions,[r[0] for r in regions]);_STARTS[id(regions)]=item
    i=bisect.bisect_right(item[1],at)-1
    assert i>=0 and at+len(b)<=regions[i][0]+len(data[i]),('unmanaged write',hex(at),len(b))
    rel=at-regions[i][0];data[i][rel:rel+len(b)]=b

def fingerprint(regions,data):
    h=hashlib.sha256()
    for (at,*unused),b in zip(regions,data):h.update(struct.pack('<QI',at,len(b)));h.update(hashlib.sha256(b).digest())
    return h.digest()

class Image:
    def __init__(self,pack,mask,path):self.pack=pack;self.data=pack.data(mask);self.f=Path(path).open('rb');self.pos=0
    def seek(self,at,whence=0):self.pos=at if whence==0 else self.pos+at if whence==1 else self.pack.size+at;return self.pos
    def tell(self):return self.pos
    def read(self,n):
        self.f.seek(self.pos);out=bytearray(self.f.read(n));end=self.pos+len(out)
        for (at,*unused),data in zip(self.pack.regions,self.data):
            lo=max(at,self.pos);hi=min(at+len(data),end)
            if lo<hi:out[lo-self.pos:hi-self.pos]=data[lo-at:hi-at]
        self.pos=end;return bytes(out)
    def close(self):self.f.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
