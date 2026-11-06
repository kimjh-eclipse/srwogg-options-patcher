"""Add the native Huckebein R grant to the single ISO under an exclusive lock."""
from pathlib import Path
import sys,json,hashlib,zlib,base64,ctypes,msvcrt,os
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from inspect_iso import read,inventory,lice

def sha(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()
def pack(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));p=json.loads((ROOT/'huckebein_r_early_prepared.json').read_text(encoding='utf-8'));v=json.loads((ROOT/'huckebein_r_early_validation.json').read_text(encoding='utf-8'));assert p['prepared'] and v['passed'] and not state.get('huckebein_r_early_applied');assert p['before_sha256']==state['current_sha256'];target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  for s in [p]:
   b=(ROOT/'analysis/huckebein_r_early/story.logo').read_bytes();old=read(f,s['offset'],len(b));assert hashlib.sha256(old).hexdigest()==p['before_extent_sha256'];edits.append((s['offset'],old,b,'chapter3 Huckebein Mk3 R unit-only grant'));at=s['pointer_offset'];edits.append((at,read(f,at,8),bytes.fromhex(s['pointer_hex']),'chapter3 early equipment script pointer'))
  edits.sort()
  for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0]
  j=ROOT/'huckebein_r_early_journal.json';r={'applied':False,'before_sha256':state['current_sha256'],'chapter':3,'units':p['units'],'weapons':p['weapons'],'new_pilots':0,'gameplay_master_UNTD_and_balances_preserved':True,'extra_full_ISOs_created':0,'edits':[{'offset':at,'before_zlib_base64':pack(a),'after_zlib_base64':pack(b),'label':label} for at,a,b,label in edits]};j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
   f.flush();os.fsync(f.fileno());e=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');a=lice(f,e['offset'],e['size']);e=a['entries'][14];lice(f,e['offset'],e['size'])
   current=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
   for at,a,b,label in edits:
    while pos<at:raw=f.read(min(8<<20,at-pos));assert raw;current.update(raw);inverse.update(raw);pos+=len(raw)
    assert f.read(len(b))==b;current.update(b);inverse.update(a);pos+=len(b)
   while raw:=f.read(8<<20):current.update(raw);inverse.update(raw)
   assert inverse.hexdigest()==state['current_sha256'];after=current.hexdigest()
  except BaseException:
   for at,a,b,label in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert sha(f)==state['current_sha256'];raise
 r.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');before=state['current_sha256'];state.update(current_sha256=after,last_edit_journal=str(j),huckebein_r_early_applied=True,huckebein_r_early_chapter=3,early_equipment_units=p['units'],early_equipment_weapons=p['weapons']);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');a=ROOT/'AGENTS.md';s=a.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`');s+='\n- Huckebein Mk3 R native unit1209 joins the same chapter3 early-equipment option (bit9), unit only, no pilot creation/assignment and no stat/master/UNTD changes. It shares existing flag59,7, so past grants do not replay. Preserve this in both story/no-story chapter3 scripts. See huckebein_r_early_prepared/validation/journal.\n';a.write_text(s,encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
