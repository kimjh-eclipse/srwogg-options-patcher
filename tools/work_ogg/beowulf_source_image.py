"""Read the OGs Beowulf release in memory; never modify its project or image."""
from pathlib import Path
import io,struct,json,hashlib,bisect
ROOT=Path(__file__).resolve().parent
class OGsBeowulfImage:
 def __init__(self):
  root=ROOT.parent/'work_ogs';path=root/'iso_quickpatch/OGS_beowulf_options.bin';b=path.read_bytes();meta=json.loads((root/'runtime/beowulf_options_profiles.json').read_text(encoding='utf8'));assert hashlib.sha256(b).hexdigest().lower()==meta['pack_sha256'].lower()
  self.pack_sha256=hashlib.sha256(b).hexdigest();f=io.BytesIO(b)
  def n(fmt):return struct.unpack(fmt,f.read(struct.calcsize(fmt)))
  assert f.read(8)==b'OGSBEO02';self.size,count,pool_count=n('<QII');assert count==64
  pool=[f.read(n('<I')[0]) for _ in range(pool_count)];self.edits=[]
  for mask in range(64):
   assert n('<I')[0]==mask;f.read(32);digest=f.read(32).hex();rows=[]
   for _ in range(n('<I')[0]):
    at,size,a,c=n('<QIII');assert len(pool[a])==len(pool[c])==size;rows.append((at,pool[c]))
   if mask==32:self.edits=rows;self.profile_sha256=digest
  self.edits.sort();self.starts=[p for p,b in self.edits]
  self.f=(root/'build/SRWOGS_K.iso').open('rb');self.pos=0
 def seek(self,p,whence=0):self.pos=p if whence==0 else self.pos+p if whence==1 else self.size+p;return self.pos
 def tell(self):return self.pos
 def read(self,n):
  self.f.seek(self.pos);b=bytearray(self.f.read(n));end=self.pos+len(b)
  ix=max(0,bisect.bisect_right(self.starts,self.pos)-1)
  for at,data in self.edits[ix:]:
   if at>=end:break
   lo=max(at,self.pos);hi=min(end,at+len(data))
   if lo<hi:b[lo-self.pos:hi-self.pos]=data[lo-at:hi-at]
  self.pos=end;return bytes(b)
 def close(self):self.f.close()
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
