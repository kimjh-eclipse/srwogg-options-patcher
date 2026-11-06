"""Apply step 3 to the single authorized ISO, with exclusive lock and rollback."""
from pathlib import Path
import sys,json,struct,hashlib,zlib,base64,ctypes,msvcrt,os
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from inspect_iso import read,inventory,lice

def sha(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def pack(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def apply():
 plan=json.loads((ROOT/'story_consistency_prepared.json').read_text(encoding='utf-8'));validation=json.loads((ROOT/'story_consistency_validation.json').read_text(encoding='utf-8'));state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));assert plan['passed'] and validation['passed'];assert state['current_sha256']==plan['before_sha256'];assert not state.get('story_consistency_applied');target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p
 h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  for ch in plan['chapters']:
   b=(ROOT/'analysis/consistency_prepared'/f'{ch["key"]}.logo').read_bytes();assert len(b)==ch['new_size'];n=max(ch['old_size'],len(b));old=read(f,ch['offset'],n)
   assert not any(old[ch['old_size']:]);new=b+b'\0'*(n-len(b));edits.append((ch['offset'],old,new,f"chapter {ch['chapter']} story consistency"))
   if len(b)!=ch['old_size']:
    p=ch['directory_pointer'];ptr=read(f,p,8);assert struct.unpack_from('<I',ptr,4)[0]==ch['old_size'];edits.append((p,ptr,ptr[:4]+struct.pack('<I',len(b)),f"chapter {ch['chapter']} script length"))
  edits.sort()
  for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0]
  journal=ROOT/'story_consistency_journal.json';result={'applied':False,'step':3,'before_sha256':state['current_sha256'],'changed_chapters':13,'replacement_boxes':31,'new_response_boxes':3,'masters_UNTD_balance_and_recruitment_schedule_preserved':True,'extra_full_ISOs_created':0,'edits':[{'offset':p,'before_zlib_base64':pack(a),'after_zlib_base64':pack(b),'label':label} for p,a,b,label in edits]};journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  try:
   for p,a,b,label in edits:assert read(f,p,len(a))==a;f.seek(p);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno())
   parent=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,parent['offset'],parent['size']);entry=outer['entries'][14];lice(f,entry['offset'],entry['size'])
   current=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
   for p,a,b,label in edits:
    while pos<p:raw=f.read(min(8<<20,p-pos));assert raw;current.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;current.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(8<<20):current.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==state['current_sha256'];after=current.hexdigest()
  except BaseException:
   for p,a,b,label in edits:f.seek(p);f.write(a)
   f.flush();os.fsync(f.fileno());assert sha(f)==state['current_sha256'];raise
 result.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True,changed_regions=len(edits));journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 before=state['current_sha256'];state.update(current_sha256=after,last_edit_journal=str(journal),story_consistency_applied=True,improvement_step_completed=3);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 p=ROOT/'AGENTS.md';s=p.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`');s+='\n- Step3 applied: 31 dialogue boxes in 13 chapters, moved chapter28/35/36 guarded scenes within their native events, final-response scene flag62,6. Original native outcomes, master/UNTD data, recruitment chapters and step2 recovery preserved. See story_consistency_policy.py, story_consistency_validation.json and story_consistency_journal.json. This is an incremental override of historical story_content_25.py; do not rerun historical builders.\n';p.write_text(s,encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':apply()
