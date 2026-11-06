"""Read the verified official Korean base as a sparse overlay on the old ISO."""
from pathlib import Path
import json,zlib,base64
HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'official_base_delta.json').read_text(encoding='utf-8'))
CHANGES=[(e['offset'],zlib.decompress(base64.b64decode(e['after'])),zlib.decompress(base64.b64decode(e['before']))) for e in DATA['changes']]
SOURCE=HERE.parent.parent/'SRWOGS_EX_K.ISO'

class OfficialImage:
 def __init__(self):self.f=SOURCE.open('rb')
 def __enter__(self):return self
 def __exit__(self,*args):self.f.close()
 def close(self):self.f.close()
 def seek(self,*args):return self.f.seek(*args)
 def tell(self):return self.f.tell()
 def read(self,n=-1):
  start=self.f.tell();data=bytearray(self.f.read(n));end=start+len(data)
  for at,after,before in CHANGES:
   lo=max(at,start);hi=min(at+len(after),end)
   if lo<hi:data[lo-start:hi-start]=after[lo-at:hi-at]
  return bytes(data)

def source_image():return OfficialImage()
