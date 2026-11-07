"""Audit the prospective image without creating a second full ISO."""
from prepare_civil_war import *

class PreparedImage:
 def __init__(self,f,p):
  self.f=f;self.pos=0;self.edits=[(e['offset'],(DEST/e['file']).read_bytes()) for e in p['edits']]
 def seek(self,at,whence=0):
  assert whence==0;self.pos=at;return at
 def read(self,n):
  self.f.seek(self.pos);b=bytearray(self.f.read(n));end=self.pos+len(b)
  for at,data in self.edits:
   lo=max(self.pos,at);hi=min(end,at+len(data))
   if lo<hi:b[lo-self.pos:hi-self.pos]=data[lo-at:hi-at]
  self.pos=end;return bytes(b)

def main():
 p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));count=0
 with TARGET.open('rb') as f:
  image=PreparedImage(f,p);files=inventory(f);changed={x['key'] for x in p['bridges']}
  def unchanged_payload(a,b):
   nonlocal count
   assert a['offset']==b['offset'] and a['size']==b['size']
   ca=lice(f,a['offset'],a['size']);cb=lice(image,b['offset'],b['size'])
   if ca:
    assert cb and ca['count']==cb['count'] and ca['slots']==cb['slots']
    for x,y in zip(ca['entries'],cb['entries']):assert x['keys']==y['keys'];unchanged_payload(x,y)
   else:
    assert read(f,a['offset'],a['size'])==read(image,b['offset'],b['size']),(hex(a['offset']),a['size']);count+=1
  for name in ['MAP.BIN;1','BATTLE.BIN;1']:
   file=next(e for e in files if e['name']==name);old=lice(f,file['offset'],file['size']);new=lice(image,file['offset'],file['size'])
   assert old['count']==new['count']
   for a,b in zip(old['entries'],new['entries']):
    slot=a['index'];modified=(name=='MAP.BIN;1' and slot in [13,14]) or (name=='BATTLE.BIN;1' and slot==5)
    if not modified:
     unchanged_payload(a,b);continue
    oa=lice(f,a['offset'],a['size']);na=lice(image,b['offset'],b['size']);assert na['count']==oa['count']+(5 if name=='MAP.BIN;1' else 36)
    for before,after in zip(oa['entries'],na['entries']):
     is_bridge=name=='MAP.BIN;1' and slot==14 and any(k in changed for k in before['keys'])
     assert before['keys']==after['keys']
     if not is_bridge:
      assert before['offset']==after['offset'] and before['size']==after['size'];assert read(f,before['offset'],before['size'])==read(image,after['offset'],after['size']);count+=1
    assert all(e['keys'] for e in na['entries'][oa['count']:])
  # No stale pointers after appending/relocating private dialogue payloads.
  for slot in [13,14]:
   _,leaves=loadarc(image,slot)
   for s in p['scenes']:
    expected=s['untd' if slot==13 else 'logo'];assert any(s['key'] in ks and (at,n)==(expected['offset'],expected['size']) for ks,at,n in leaves)
  # Text is authored Korean, not accidentally retained Japanese source glyphs.
  messages=[m for s in p['scenes']+p['bridges'] for m in s['messages']]
  assert all(not any('\u3040'<=c<='\u30ff' or '\u3400'<=c<='\u9fff' for c in m['text']) for m in messages)
 result=dict(passed=True,unchanged_resource_payloads=count,all_declared_archive_bounds_checked=True,original_MAP_and_BATTLE_payloads_preserved_except_five_dialogue_bridges=True,new_speech_chunks=36,authored_dialogue_boxes=len(messages),extra_full_ISOs_created=0)
 (ROOT/'civil_war_resource_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
