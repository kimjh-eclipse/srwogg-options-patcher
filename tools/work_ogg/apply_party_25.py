"""Fix private-clone family identity and add one idempotent chapter-28 recovery."""
from pathlib import Path
import sys,json,struct,hashlib,zlib,base64,os,ctypes,msvcrt
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_party' if (ROOT/'option_party/build_options.py').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster,source_image
from party_policy_25 import edits_for_master,recovery_script,native_recovery,STORY_RECOVERY,NATIVE_RECOVERY
from audit_story_layout import loadarc
from inspect_iso import inventory,lice,read,u32

def digest(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def packed(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def main():
 validation=json.loads((ROOT/'party_25_validation.json').read_text(encoding='utf-8'));assert validation['passed']
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));target=Path(state['canonical_iso'])
 keys=[r['key'] for ch in json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'))['chapters'] for r in ch['recruits']];edits=[];masters=[]
 with target.open('rb') as f,source_image() as original:
  for name in ['SHARED.BIN','IM.BIN']:
   entry,m=rawmaster(f,name)
   for at,a,b,key in edits_for_master(m.b,keys):edits.append((entry['offset']+at,a,b,'private clone family '+hex(key)));masters.append({'archive':name,'key':key,'relative_offset':at})
  a,entries=loadarc(f,14);_,at,n=next(e for e in entries if 2026 in e[0]);story=recovery_script(read(f,at,n));native,npointer=native_recovery(original,a)
  for address,blob,label in [(STORY_RECOVERY,story,'chapter28 story recovery'),(NATIVE_RECOVERY,native,'chapter28 native recovery')]:
   before=read(f,address,len(blob));assert not any(before)
   edits.append((address,before,blob,label))
  entry=next(e for e in a['entries'] if 2026 in e['keys']);dp=a['directory']+8+entry['index']*8
  edits.append((dp,read(f,dp,8),struct.pack('<II',STORY_RECOVERY-a['directory'],len(story)),'chapter28 active script pointer'))
  mapentry=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,mapentry['offset'],mapentry['size']);parent=outer['entries'][14]
  end=max(STORY_RECOVERY+len(story),NATIVE_RECOVERY+len(native));assert end<=mapentry['offset']+mapentry['size']
  span=outer['directory']+8+14*8+4
  edits.append((span,read(f,span,4),struct.pack('<I',max(parent['size'],end-parent['offset'])),'MAP14 archive span covers relocated scripts'))
 edits.sort();assert len(masters)==4
 for x,y in zip(edits,edits[1:]):assert x[0]+len(x[1])<=y[0]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];kernel.CreateFileW.restype=ctypes.c_void_p
 handle=kernel.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY),'r+b') as f:
  before=digest(f);assert before==state['current_sha256']
  result={'applied':False,'step':2,'before_sha256':before,'masters':masters,'story_recovery':{'offset':STORY_RECOVERY,'size':len(story)},'native_recovery':{'offset':NATIVE_RECOVERY,'size':len(native),'pointer':npointer.hex()},'edits':[{'offset':p,'before_zlib_base64':packed(x),'after_zlib_base64':packed(y),'label':label} for p,x,y,label in edits],'stats_spirits_and_original_units_preserved':True,'extra_full_ISOs_created':0}
  journal=ROOT/'party_25_journal.json';journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  try:
   for at,a,b,label in edits:assert read(f,at,len(a))==a;f.seek(at);f.write(b)
   f.flush();os.fsync(f.fileno())
   for at,a,b,label in edits:assert read(f,at,len(b))==b
   # Validate every nested script pointer against the declared MAP14 extent.
   outer=lice(f,mapentry['offset'],mapentry['size']);p=outer['entries'][14];lice(f,p['offset'],p['size'])
   after=digest(f)
  except BaseException:
   for at,a,b,label in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert digest(f)==before;raise
 result.update(applied=True,after_sha256=after,changed_regions=len(edits));journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 state.update(current_sha256=after,last_edit_journal=str(journal),party_preservation_25_applied=True,improvement_step_completed=2);(ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 agents=ROOT/'AGENTS.md';s=agents.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`');s+='\n- Roadmap step2: private Rin Huckebein full/locked forms have family alias -1 in SHARED/IM, preventing native 0x4AD events from disabling clone0x701 and its occupant. Chapter28 adds idempotent activation of existing clone0x701, including a separate no-story script. MAP14 parent span covers both recovery payloads and the no-story chapter3 payload. Preserve these in option composition; see party_policy_25.py and party_25_journal.json.\n';agents.write_text(s,encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
