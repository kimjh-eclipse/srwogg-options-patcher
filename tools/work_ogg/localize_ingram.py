"""Translate the preserved Ingram subtitles; leave voice IDs/selectors intact."""
from inspect_ingram_text import texts
from inspect_resources import *
import shutil,os

def wrap(text,width=24):
 text='「'+text.replace(' ','　')+'」';lines=[]
 while len(text)>width:
  cut=text.rfind('　',8,width+1)
  if cut<0:cut=width
  lines.append(text[:cut]);text=text[cut:].lstrip('　')
 lines.append(text)
 assert len(lines)<=3,(text,lines)
 return '/　'.join(lines)

def localize(blob):
 originals=json.loads((OUT/'ingram_unique.json').read_text(encoding='utf-8'))
 translated=(ROOT/'ingram_ko.txt').read_text(encoding='utf-8').splitlines()
 assert len(originals)==len(translated)==176
 mapping={bytes.fromhex(r['raw']):wrap(t) for r,t in zip(originals,translated)}
 rows=texts(blob);assert len(rows)==382 and set(bytes.fromhex(r['raw']) for r in rows)==set(mapping)
 h=struct.unpack_from('<16H',blob);new=bytearray(blob[:h[15]]);pool=bytearray();positions={};review=[]
 for r in rows:
  source=bytes.fromhex(r['raw']);text=mapping[source];raw=encode(text)
  assert decode(raw)==text
  assert not any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in text),text
  if raw not in positions:positions[raw]=len(pool);pool.extend(raw+b'\0')
  assert positions[raw]<65536
  struct.pack_into('<H',new,h[13]+r['index']*2,positions[raw])
 new.extend(pool)
 assert new[:h[13]]==blob[:h[13]],'Selector/speaker data changed'
 assert new[h[14]:h[15]]==blob[h[14]:h[15]],'Voice IDs changed'
 checked=texts(new)
 for a,b in zip(rows,checked):
  assert a['voice']==b['voice'] and a['speaker']==b['speaker']
  assert b['kr']==mapping[bytes.fromhex(a['raw'])]
 for r,t in zip(originals,translated):review.append(dict(japanese=r['jp'],korean=t,encoded_display=mapping[bytes.fromhex(r['raw'])]))
 return bytes(new),dict(rows=382,unique_lines=176,all_voice_ids_preserved=True,all_selectors_and_speakers_preserved=True,all_text_round_trips=True,max_line_width=24,live_display_verified=False),review

def main():
 source=ROOT/'SRWOGG_INGRAM_TEST.iso';target=ROOT/'SRWOGG_INGRAM_KR_v2.iso'
 expected=json.loads((ROOT/'manifest_test.json').read_text(encoding='utf-8'))['target_sha256']
 with source.open('rb') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==expected
  e=next(x for x in inventory(f) if x['name']=='BATTLE.BIN;1');root=lice(f,e['offset'],e['size']);v=root['entries'][5];a=lice(f,v['offset'],v['size']);e=next(x for x in a['entries'] if 0x700 in x['keys']);old=read(f,e['offset'],e['size']);new,checks,review=localize(old)
  assert len(new)<65536
  if len(new)>len(old):assert not any(read(f,e['offset']+len(old),len(new)-len(old)))
  edits=[(e['offset'],read(f,e['offset'],len(new)),new,'Ingram Korean subtitle pool and offsets'),(a['directory']+8+e['index']*8+4,struct.pack('<I',len(old)),struct.pack('<I',len(new)),'voice chunk length')]
  span=max(x['offset']+(len(new) if x['index']==e['index'] else x['size']) for x in a['entries'])-a['offset']
  o=root['directory']+8+5*8+4;edits.append((o,read(f,o,4),struct.pack('<I',span),'voice archive span'));edits.sort()
 assert not target.exists(),'Output already exists'
 shutil.copyfile(source,target)
 with target.open('r+b') as f:
  for o,b,c,label in edits:
   assert read(f,o,len(b))==b;f.seek(o);f.write(c)
  f.flush();os.fsync(f.fileno())
 inverse=hashlib.sha256();target_hash=hashlib.sha256();pos=0
 with target.open('rb') as f:
  for o,b,c,label in edits:
   while pos<o:
    raw=f.read(min(4<<20,o-pos));assert raw;pos+=len(raw);inverse.update(raw);target_hash.update(raw)
   assert f.read(len(c))==c;inverse.update(b);target_hash.update(c);pos+=len(c)
  while raw:=f.read(4<<20):inverse.update(raw);target_hash.update(raw)
 assert inverse.hexdigest()==expected,'Unrelated data changed'
 report=dict(source=str(source),target=str(target),source_sha256=expected,target_sha256=target_hash.hexdigest(),checks=checks,all_other_bytes_preserved=True,old_chunk_size=len(old),new_chunk_size=len(new),edits=[dict(offset=o,before=b.hex(),after=c.hex(),label=l) for o,b,c,l in edits])
 (ROOT/'manifest_korean_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'잉그램_전투자막_번역대조.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='edits'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
