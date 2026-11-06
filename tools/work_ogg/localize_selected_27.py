"""Localize every remaining Japanese subtitle in the approved 27 voice chunks."""
from export_27_subtitles import *
from localize_ingram import wrap
import os,shutil,subprocess

NEW=ROOT/'SRWOGG_27_CH1_KR.iso'
PATCH=ROOT/'OGG_27_CH1_KR.xdelta'

def translations():
 result={};pilot=None
 for line in (ROOT/'subtitles_27_ko.tsv').read_text(encoding='utf-8').splitlines():
  if not line:continue
  if line.startswith('['):pilot=line[1:-1];result[pilot]={};continue
  idx,text=line.split('\t',1);assert int(idx) not in result[pilot]
  result[pilot][int(idx)]=wrap(text)
 assert sum(len(x) for x in result.values())==417
 return result

def rewrite(blob,unique,translated):
 rows=texts(blob);h=struct.unpack_from('<16H',blob);mapping={unique[i]['raw']:encode(t) for i,t in translated.items()}
 for i,t in translated.items():
  assert has_japanese(unique[i]['kr'])
  assert decode(encode(t))==t and not has_japanese(t)
 new=bytearray(blob[:h[15]]);pool=bytearray();positions={}
 for r in rows:
  raw=mapping.get(r['raw'],bytes.fromhex(r['raw']))
  if raw not in positions:positions[raw]=len(pool);pool.extend(raw+b'\0')
  assert positions[raw]<65536
  struct.pack_into('<H',new,h[13]+r['index']*2,positions[raw])
 new.extend(pool)
 assert new[:h[13]]==blob[:h[13]] and new[h[14]:h[15]]==blob[h[14]:h[15]]
 preserved=changed=0
 for old,now in zip(rows,texts(new)):
  assert (old['voice'],old['speaker'])==(now['voice'],now['speaker'])
  assert not has_japanese(now['kr']),(old,now)
  if old['raw'] not in mapping:assert old['raw']==now['raw'];preserved+=1
  else:assert bytes.fromhex(now['raw'])==mapping[old['raw']];changed+=1
 return bytes(new),dict(row_count=len(rows),changed_rows=changed,preserved_rows=preserved,remaining_japanese_rows=0,voice_ids_and_speakers_preserved=True,selectors_preserved=True)

def main():
 source_report=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf-8'));export=json.loads((OUT/'subtitles_27.json').read_text(encoding='utf-8'));tr=translations();edits=[];proof=[];review=[]
 assert not NEW.exists() and not PATCH.exists()
 print('Checking source and preparing all remaining subtitles...',flush=True)
 with TARGET.open('rb') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==source_report['target_sha256']
  root=arc('BATTLE.BIN');outer=root['entries'][5];span=u32(read(f,root['directory']+8+5*8+4,4));a=lice(f,outer['offset'],span);cursor=0x99400000
  for item in export:
   e=next(e for e in a['entries'] if item['key'] in e['keys']);blob=read(f,e['offset'],e['size']);r=tr.get(item['pilot'],{})
   expected={i for i,x in enumerate(item['unique']) if has_japanese(x['kr'])};assert set(r)==expected,(item['pilot'],set(r)^expected)
   if not r:
    assert all(not has_japanese(x['kr']) for x in texts(blob));proof.append(dict(pilot=item['pilot'],row_count=len(texts(blob)),changed_rows=0,preserved_rows=len(texts(blob)),remaining_japanese_rows=0));continue
   new,check=rewrite(blob,item['unique'],r);proof.append(dict(pilot=item['pilot'],**check))
   cursor=(cursor+2047)//2048*2048;assert cursor+len(new)<0x9a4d4000 and not any(read(f,cursor,len(new)))
   edits.append((cursor,bytes(len(new)),new,'Korean subtitles '+item['pilot']))
   at=a['directory']+8+e['index']*8;edits.append((at,read(f,at,8),struct.pack('<II',cursor-a['directory'],len(new)),'translated chunk pointer '+item['pilot']));cursor+=len(new)
   for i,t in r.items():review.append(dict(pilot=item['pilot'],unique_index=i,voice_id=item['unique'][i]['voice'],original_display=item['unique'][i]['kr'],japanese_source=item['unique'][i]['jp'],korean=t))
  at=root['directory']+8+5*8+4;edits.append((at,read(f,at,4),struct.pack('<I',cursor-a['offset']),'voice archive span'))
 edits.sort()
 for left,right in zip(edits,edits[1:]):assert left[0]+len(left[1])<=right[0]
 print('Creating fully localized 27-lineup ISO...',flush=True);shutil.copyfile(TARGET,NEW)
 with NEW.open('r+b') as f:
  for at,b,c,label in edits:assert read(f,at,len(b))==b;f.seek(at);f.write(c)
  f.flush();os.fsync(f.fileno())
  # Read the final directory, not the in-memory output, to audit all 27 chunks.
  actual=lice(f,a['offset'],cursor-a['offset']);total=0
  for item in export:
   e=next(e for e in actual['entries'] if item['key'] in e['keys']);rows=texts(read(f,e['offset'],e['size']));total+=len(rows)
   assert all(not has_japanese(r['kr']) for r in rows),item['pilot']
 print('All 27 subtitle chunks pass. Checking the complete image...',flush=True)
 inverse=hashlib.sha256();digest=hashlib.sha256();pos=0
 with NEW.open('rb') as f:
  for at,b,c,label in edits:
   while pos<at:
    raw=f.read(min(4<<20,at-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
   assert f.read(len(c))==c;inverse.update(b);digest.update(c);pos+=len(c)
  while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
 assert inverse.hexdigest()==source_report['target_sha256']
 report=dict(source=str(TARGET),target=str(NEW),patch=str(PATCH),source_sha256=source_report['target_sha256'],target_sha256=digest.hexdigest(),pilots_audited=27,unique_lines_audited=2479,unique_lines_translated=417,subtitle_rows_audited=total,remaining_japanese_rows=0,other_image_data_preserved=True,voice_audio_unchanged=True,live_display_verified=False,checks=proof)
 (ROOT/'manifest_selected_27_korean.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'27편성_추가자막_번역대조.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Creating patch for original SRWOGS_EX_K.ISO...',flush=True)
 subprocess.run([str(ROOT.parent/'xdelta.exe'),'-e','-s',str(SOURCE),str(NEW),str(PATCH)],check=True)
 subprocess.run([str(ROOT.parent/'xdelta.exe'),'-d','-J','-s',str(SOURCE),str(PATCH)],check=True)
 report['xdelta_decode_verified']=True;report['patch_size']=PATCH.stat().st_size
 (ROOT/'manifest_selected_27_korean.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
