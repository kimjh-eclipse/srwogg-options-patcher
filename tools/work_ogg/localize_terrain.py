"""Patch only fixed terrain-name fields in the single canonical test ISO."""
from catalog import *
import os

def main():
 statefile=ROOT/'current_target.json';state=json.loads(statefile.read_text(encoding='utf-8'));path=Path(state['canonical_iso'])
 assert path==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 journal=ROOT/'terrain_ko_journal.json';assert not journal.exists(),'Review existing terrain journal before running again'
 names=json.loads((OUT/'terrain_names.json').read_text(encoding='utf-8'));translations=(ROOT/'terrain_ko.txt').read_text(encoding='utf-8').splitlines();assert len(names)==len(translations)==149
 mapping={r['japanese']:k.replace(' ','　') for r,k in zip(names,translations)}
 a=json.loads((OUT/'MAP.BIN.12.json').read_text());e=a['entries'][0];edits=[]
 print('Verifying canonical ISO...',flush=True)
 # Opening writable before mutation also checks whether an emulator blocks access.
 with path.open('r+b') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==state['current_sha256']
  old=read(f,e['offset'],e['size']);assert old[:4]==b'MPTI' and len(old)==8+1024*52
  new=bytearray(old);review=[]
  for i in range(1024):
   at=8+i*52;field=old[at:at+32];raw=field.split(b'\0')[0]
   if not raw:continue
   name=raw.decode('cp932',errors='replace').split('@')[0];text=mapping[name];encoded=encode(text)
   assert decode(encoded)==text and len(encoded)<32
   # '@' may be a Shift-JIS trail byte inside a character. Locate the real
   # delimiter after decoding the complete original name, not bytes.split().
   n=len(name.encode('cp932'));comment=raw[n+1:] if raw[n:n+1]==b'@' else b''
   out=encoded
   if raw[n:n+1]==b'@':
    available=31-len(encoded)-1;comment=comment[:available]
    while comment:
     try:comment.decode('cp932');break
     except UnicodeDecodeError:comment=comment[:-1]
    out+=b'@'+comment
   assert len(out)<=31;out+=bytes(32-len(out));new[at:at+32]=out
   edits.append((e['offset']+at,field,out));review.append(dict(terrain_id=i,japanese=name,korean=text))
  assert len(edits)==453
  assert new[:8]==old[:8]
  for i in range(1024):assert new[8+i*52+32:8+(i+1)*52]==old[8+i*52+32:8+(i+1)*52],('Terrain stats changed',i)
  for r in review:
   at=8+r['terrain_id']*52;raw=new[at:at+32].split(b'\0')[0];text=decode(raw).split('@')[0]
   assert text==r['korean'] and not any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in text)
  record=dict(target=str(path),source_sha256=state['current_sha256'],applied=False,unique_names=149,translated_records=453,terrain_stats_preserved=True,edits=[dict(offset=o,before=b.hex(),after=c.hex()) for o,b,c in edits],translation=review)
  journal.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
  print('Applying 149 terrain names to the existing test ISO...',flush=True)
  try:
   for at,b,c in edits:assert read(f,at,32)==b;f.seek(at);f.write(c)
   f.flush();os.fsync(f.fileno())
   assert read(f,e['offset'],e['size'])==new
   print('Checking the full image and unchanged combat data...',flush=True)
   inverse=hashlib.sha256();digest=hashlib.sha256();pos=0;f.seek(0)
   for at,b,c in edits:
    while pos<at:
     raw=f.read(min(4<<20,at-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
    assert f.read(32)==c;inverse.update(b);digest.update(c);pos+=32
   while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
   assert inverse.hexdigest()==state['current_sha256'],'Unexpected changes outside terrain-name fields'
  except BaseException:
   for at,b,c in edits:f.seek(at);f.write(b)
   f.flush();os.fsync(f.fileno());raise
 record.update(applied=True,target_sha256=digest.hexdigest(),all_other_image_bytes_preserved=True,live_display_verified=False)
 journal.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
 state.update(current_sha256=record['target_sha256'],terrain_names_localized=True,last_edit_journal=str(journal));statefile.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 guide=ROOT/'AGENTS.md';text=guide.read_text(encoding='utf-8');text=text.replace(record['source_sha256'],record['target_sha256']);text+='\n- Terrain-name localization: 149 unique names / 453 records are Korean; terrain stats and all combat data were preserved. See `terrain_ko_journal.json`.\n';guide.write_text(text,encoding='utf-8')
 print(json.dumps({k:v for k,v in record.items() if k not in ('edits','translation')},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
