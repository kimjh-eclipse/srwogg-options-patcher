"""Apply validated civil-war resources to the single canonical image."""
from apply_regional_five import *
def main():
 for report in ['civil_war_resource_validation.json','civil_war_party_validation.json']:assert json.loads((ROOT/report).read_text(encoding='utf8'))['passed']
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));v=json.loads((ROOT/'civil_war_validation.json').read_text(encoding='utf8'));assert p['prepared'] and v['ready_to_apply'] and not state.get('civil_war_applied');assert state['current_sha256']==p['before_sha256'];target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 edits=[]
 for e in p['edits']:
  a=zlib.decompress(base64.b64decode(e['before_zlib_base64']));b=(ROOT/'analysis/civil_war'/e['file']).read_bytes();assert len(a)==len(b)==e['size'] and hashlib.sha256(b).hexdigest()==e['after_sha256'];edits.append((e['offset'],a,b,e['label']))
 edits.sort();assert all(a[0]+len(a[1])<=b[0] for a,b in zip(edits,edits[1:]))
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];j=ROOT/'civil_war_journal.json';r=dict(applied=False,before_sha256=state['current_sha256'],edits=[dict(offset=at,before_zlib_base64=pack(a),after_zlib_base64=pack(b),label=label) for at,a,b,label in edits]);j.write_text(json.dumps(r,indent=2),encoding='utf8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());digest=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
   for at,a,b,label in edits:
    while pos<at:raw=f.read(min(8<<20,at-pos));assert raw;digest.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;digest.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(8<<20):digest.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==state['current_sha256'];after=digest.hexdigest()
   a,ls=loadarc(f,14)
   for s in p['scenes']:assert any(s['key'] in ks and at==s['logo']['offset'] and n==s['logo']['size'] for ks,at,n in ls)
  except BaseException:
   for at,a,b,label in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert sha(f)==state['current_sha256'];raise
 r.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True,extra_full_ISOs_created=0);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');state.update(current_sha256=after,last_edit_journal=str(j),civil_war_applied=True,civil_war_keys=list(range(2041,2046)),civil_war_auto_encounter=True,civil_war_pairs=26,additional_battles=11,final_display_chapter=47);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');p.update(applied=True,after_sha256=after);(ROOT/'civil_war_prepared.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k!='edits'}))
if __name__=='__main__':main()
