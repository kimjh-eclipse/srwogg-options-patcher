"""Apply the authorized experimental missions to the one canonical image."""
from pathlib import Path
import sys,json,hashlib,zlib,base64,ctypes,msvcrt,os,struct
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from inspect_iso import inventory,lice,read,u32
from audit_story_layout import loadarc

def pack(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')
def sha(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));p=json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8'));v=json.loads((ROOT/'regional_five_validation.json').read_text(encoding='utf8'))
 assert p['prepared'] and v['passed'] and v['ready_for_experimental_apply'] and not state.get('regional_five_applied')
 assert p['before_sha256']==state['current_sha256'];target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  def edit(at,b,label):
   a=read(f,at,len(b))
   if a!=b:edits.append((at,a,b,label))
  for s in p['resources']:
   b=(ROOT/'analysis/regional_five'/s['file']).read_bytes();assert len(b)==s['size'] and not any(read(f,s['offset'],len(b)));edit(s['offset'],b,s['file'])
  root=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,root['offset'],root['size'])
  for slot,kind in [(13,'untd'),(14,'logo')]:
   a,leaves=loadarc(f,slot);count=a['count'];assert count==p['slot_counts'][str(slot)]
   assert not any(read(f,a['directory']+8+count*8,40))
   edit(a['offset']+8,struct.pack('<I',count+5),f'LICE{slot} count');edit(a['directory']+4,struct.pack('<I',count+5),f'Wpbb{slot} count')
   for i,s in enumerate(p['scenes']):
    key=s['key'];r=s[kind];assert read(f,a['offset']+16+key*2,2)==b'\xff\xff';edit(a['offset']+16+key*2,struct.pack('<H',count+i),f'{kind} key{key}')
    edit(a['directory']+8+(count+i)*8,struct.pack('<II',r['offset']-a['directory'],r['size']),f'{kind} entry{key}')
   if slot==13:
    leafend=max(at+n for _,at,n in leaves);parent=outer['entries'][13];span=max(parent['size'],leafend-parent['offset'])
    edit(outer['directory']+8+13*8+4,struct.pack('<I',span),'UNTD parent span includes every existing leaf')
   else:
    ix=next(e['index'] for e in a['entries'] if 2032 in e['keys']);s=next(s for s in p['bridge'] if s['mode']=='story');edit(a['directory']+8+ix*8,struct.pack('<II',s['offset']-a['directory'],s['size']),'chapter34 bridge story pointer')
  for ar,item in p['masters'].items():edit(item['offset'],(ROOT/'analysis/regional_five'/item['file']).read_bytes(),ar+' titles and display numbers')
  edits.sort()
  for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0]
  j=ROOT/'regional_five_journal.json';report=dict(applied=False,before_sha256=state['current_sha256'],extra_full_ISOs_created=0,experimental=True,playthrough_verified=False,edits=[dict(offset=at,before_zlib_base64=pack(a),after_zlib_base64=pack(b),label=label) for at,a,b,label in edits]);j.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());outer=lice(f,root['offset'],root['size'])
   for slot in [13,14]:
    e=outer['entries'][slot];a=lice(f,e['offset'],e['size']);assert all(any(k in e['keys'] for e in a['entries']) for k in range(2035,2040))
   current=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
   for at,a,b,label in edits:
    while pos<at:raw=f.read(min(8<<20,at-pos));assert raw;current.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;current.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(8<<20):current.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==state['current_sha256'];after=current.hexdigest()
  except BaseException:
   for at,a,b,label in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert sha(f)==state['current_sha256'];raise
 report.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True);j.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 before=state['current_sha256'];state.update(current_sha256=after,last_edit_journal=str(j),regional_five_applied=True,regional_five_experimental=True,regional_five_keys=list(range(2035,2040)),final_display_chapter=41);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 path=ROOT/'AGENTS.md';s=path.read_text(encoding='utf8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`');s+='\n- Experimental five regional battles after original34 are applied, new keys2035..2039; original35/36 display40/41. Native deployment/defeat/victory guards use owned-party selection and army counts; no new roster grants. Original maps/models and master combat tables preserved. 34 bridge added before native dialogue close; Duminus is alive and fleeing, main pursuit continues. External passages are explicitly new fan scenario fiction. New option12 must toggle routing and bridge in BOTH story/native34 variants, plus original35/36 display numbers; story bit0 gates extra character lines. Native38 Inspector remnants use earth-made units because alien minion assets are absent. LICE13/14 membership is now dynamic: do not use historical cached entry counts. Parent13 span was repaired to cover preexisting leaf172 (+6144 bytes); leave this common. No PCSX2 playthrough or memory-card test claim. See regional_five_prepared/validation/journal.\n';path.write_text(s,encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='edits'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
