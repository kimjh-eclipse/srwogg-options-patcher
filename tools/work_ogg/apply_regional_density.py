"""Apply just the expanded enemy lists and their five directory pointers."""
from apply_regional_five import *

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));p=json.loads((ROOT/'regional_density_prepared.json').read_text(encoding='utf8'));v=json.loads((ROOT/'regional_density_validation.json').read_text(encoding='utf8'));assert p['prepared'] and v['passed'] and v['ready_to_apply'] and p['before_sha256']==state['current_sha256'] and not state.get('regional_density_applied')
 target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  for s in p['scenes']:
   at=s['untd']['offset'];b=(ROOT/'analysis/regional_density'/s['untd']['file']).read_bytes();assert not any(read(f,at,len(b)));edits.append((at,read(f,at,len(b)),b,str(s['key'])+'32 enemies'))
   at=s['directory_pointer'];edits.append((at,read(f,at,8),bytes.fromhex(s['pointer_hex']),str(s['key'])+' active UNTD pointer'))
  edits.sort()
  for a,b in zip(edits,edits[1:]):assert a[0]+len(a[1])<=b[0]
  j=ROOT/'regional_density_journal.json';r=dict(applied=False,before_sha256=state['current_sha256'],enemies_per_mission=32,bosses_per_mission=2,extra_full_ISOs_created=0,edits=[dict(offset=at,before_zlib_base64=pack(a),after_zlib_base64=pack(b),label=label) for at,a,b,label in edits]);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());entry=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,entry['offset'],entry['size']);leaf=outer['entries'][13];lice(f,leaf['offset'],leaf['size'])
   digest=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
   for at,a,b,label in edits:
    while pos<at:raw=f.read(min(8<<20,at-pos));assert raw;digest.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;digest.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(8<<20):digest.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==state['current_sha256'];after=digest.hexdigest()
  except BaseException:
   for at,a,b,label in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert sha(f)==state['current_sha256'];raise
 r.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
 old=ROOT/'regional_five_prepared.json';(ROOT/'regional_five_before_density.json').write_text(old.read_text(encoding='utf8'),encoding='utf8');new=p['new_regional_prepared'];new.update(applied=True,applied_sha256=after,status='32-enemy regional missions applied; live playtesting pending');old.write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf8')
 for s in p['scenes']:(ROOT/'analysis/regional_five'/s['untd']['file']).write_bytes((ROOT/'analysis/regional_density'/s['untd']['file']).read_bytes())
 state.update(current_sha256=after,last_edit_journal=str(j),regional_density_applied=True,regional_enemies_per_mission=32,regional_ordinary_enemies_per_mission=30,regional_bosses_per_mission=2);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in r.items() if k!='edits'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
