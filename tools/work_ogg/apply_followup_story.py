"""Write dialogue-only follow-ups to the single ISO under an exclusive lock."""
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
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));p=json.loads((ROOT/'followup_story_prepared.json').read_text(encoding='utf-8'));v=json.loads((ROOT/'followup_story_validation.json').read_text(encoding='utf-8'));assert p['prepared'] and v['passed'] and not state.get('followup_story_applied');assert p['before_sha256']==state['current_sha256'];target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;h=k.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(h,os.O_RDWR|os.O_BINARY),'r+b') as f:
  assert sha(f)==state['current_sha256'];edits=[]
  for s in p['scenes']:
   b=(ROOT/'analysis/followup_prepared'/f'{s["key"]}.logo').read_bytes();old=read(f,s['offset'],len(b));assert not any(old);edits.append((s['offset'],old,b,f"chapter{s['chapter']} follow-up dialogue"));at=s['pointer_offset'];edits.append((at,read(f,at,8),bytes.fromhex(s['pointer_hex']),f"chapter{s['chapter']} active script pointer"))
  edits.sort()
  for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0]
  j=ROOT/'followup_story_journal.json';r={'applied':False,'before_sha256':state['current_sha256'],'scene_count':5,'new_boxes':p['boxes'],'chapters':[s['chapter'] for s in p['scenes']],'gameplay_master_UNTD_and_balances_preserved':True,'extra_full_ISOs_created':0,'edits':[{'offset':at,'before_zlib_base64':pack(a),'after_zlib_base64':pack(b),'label':label} for at,a,b,label in edits]};j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
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
 r.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True);j.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');before=state['current_sha256'];state.update(current_sha256=after,last_edit_journal=str(j),followup_story_applied=True,followup_story_chapters=r['chapters'],followup_story_boxes=p['boxes']);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');a=ROOT/'AGENTS.md';s=a.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`');s+='\n- Follow-up scenes added in chapters25/29/31/32/36 (73 boxes), dialogue only. Flags62,7 and63,2..5 fill the remaining reserved60..63 bits; do not reuse any. Chapter32 is a new story-option directory selection beyond the historical22-chapter list. Chapter29 was relocated: resolve optional maintenance dialogue through its LIVE LOGO directory, not stale support_overhaul_prepared offsets. User owns playtesting; structural/native dialogue checks only, no emulator playthrough. See followup_story_content/prepared/validation/journal.\n';a.write_text(s,encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
