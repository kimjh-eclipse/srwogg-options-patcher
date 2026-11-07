"""Apply only the authorized boss resources to the one canonical test ISO."""
from apply_regional_five import *

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));p=json.loads((ROOT/'regional_bosses_prepared.json').read_text(encoding='utf8'));v=json.loads((ROOT/'regional_bosses_validation.json').read_text(encoding='utf8'));assert p['prepared'] and v['passed'] and v['ready_to_apply'] and p['before_sha256']==state['current_sha256'] and not state.get('regional_bosses_applied')
 target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO';dest=ROOT/'analysis/regional_bosses'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  def edit(at,b,label):
   a=read(f,at,len(b))
   if a!=b:edits.append((at,a,b,label))
  for ar,m in p['masters'].items():edit(m['offset'],(dest/m['file']).read_bytes(),ar+' enemy-only boss models and weapons')
  la,logos=loadarc(f,14)
  for s in p['scenes']:
   u=s['untd'];b=(dest/u['file']).read_bytes();assert len(b)==u['size'];edit(u['offset'],b,f'{s["key"]} bosses and valid placements')
   l=s['logo'];b=(dest/l['file']).read_bytes();assert not any(read(f,l['offset'],len(b)));edit(l['offset'],b,f'{s["key"]} boss identification and map selection')
   ix=next(e['index'] for e in la['entries'] if s['key'] in e['keys']);edit(la['directory']+8+ix*8,struct.pack('<II',l['offset']-la['directory'],len(b)),f'{s["key"]} current LOGO pointer')
  edits.sort()
  for a,b in zip(edits,edits[1:]):assert a[0]+len(a[1])<=b[0]
  j=ROOT/'regional_bosses_journal.json';r=dict(applied=False,before_sha256=state['current_sha256'],bosses=10,enemy_only=True,unmanned_only=True,extra_full_ISOs_created=0,live_playthrough=False,edits=[dict(offset=at,before_zlib_base64=pack(a),after_zlib_base64=pack(b),label=label) for at,a,b,label in edits]);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());entry=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,entry['offset'],entry['size'])
   for slot in [13,14]:
    e=outer['entries'][slot];lice(f,e['offset'],e['size'])
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
 oldprep=ROOT/'regional_five_prepared.json';(ROOT/'regional_five_before_bosses.json').write_text(oldprep.read_text(encoding='utf8'),encoding='utf8');newp=p['new_regional_prepared'];newp.update(applied=True,applied_sha256=after,status='experimental unmanned bosses applied; live playtesting pending');oldprep.write_text(json.dumps(newp,ensure_ascii=False,indent=2),encoding='utf8')
 for source in dest.glob('*'):
  if source.is_file():(ROOT/'analysis/regional_five'/source.name).write_bytes(source.read_bytes())
 (ROOT/'regional_five_validation.json').write_text((ROOT/'regional_bosses_story_validation.json').read_text(encoding='utf8'),encoding='utf8')
 state.update(current_sha256=after,last_edit_journal=str(j),regional_bosses_applied=True,regional_bosses=10,regional_bosses_unmanned=True,regional_space_map_corrected=40,regional_invalid_positions_fixed=True);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in r.items() if k!='edits'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
