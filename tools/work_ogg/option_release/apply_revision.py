"""Apply only native SP costs and the agreed OGs price curves, in place."""
from pathlib import Path
import sys,json,hashlib,base64,zlib,os,ctypes,msvcrt
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_options import plan,TARGET,ROOT

HERE=Path(__file__).resolve().parent
def digest(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'))
 common,off,features,proof=plan();wanted={p:b for p,b in common if len(b)==1}
 wanted.update(dict(features[6]))
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
 kernel.CreateFileW.restype=ctypes.c_void_p
 handle=kernel.CreateFileW(str(TARGET),0xc0000000,0,None,3,0,None)
 if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 fd=msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY)
 with os.fdopen(fd,'r+b') as f:
  before=digest(f);assert before==state['current_sha256']
  edits=[]
  for at,b in sorted(wanted.items()):
   f.seek(at);old=f.read(len(b))
   if old!=b:edits.append((at,old,b))
  assert edits
  journal={'applied':False,'before_sha256':before,'edits':[{'offset':at,'before':a.hex(),'after':b.hex()} for at,a,b in edits],'scope':['native SP costs','OGs final weapon price table'],'extra_full_ISOs_created':0}
  path=ROOT/'sp_and_prices_revision_journal.json';path.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf-8')
  try:
   for at,a,b in edits:f.seek(at);f.write(b)
   f.flush();os.fsync(f.fileno())
   for at,a,b in edits:f.seek(at);assert f.read(len(b))==b
   after=digest(f)
  except BaseException:
   for at,a,b in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert digest(f)==before;raise
 journal.update(applied=True,after_sha256=after,changed_regions=len(edits),changed_region_bytes=sum(len(b) for at,a,b in edits))
 path.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf-8')
 state.update(current_sha256=after,last_edit_journal=str(path),spirit_cost_one=False,sp_cost_policy='native',weapon_upgrade_cost_steps=[1600,1600,1920,3200,3200],weapon_upgrade_ten_stage_totals=[88000,88000,105600,176000,176000])
 (ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf-8'))
 meta.update(canonical_build_input_sha256=meta['canonical_iso_sha256'],canonical_iso_sha256=after)
 (HERE/'build_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
 agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8')
 text=text.replace('chapter 4, SP1, Korean names','chapter 4, native SP costs, Korean names')
 text=text.replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`')
 text+='\n- Revision v20261106.1 removes the SP1 option and restores native SP costs for existing and cloned pilots. Weapon prices now match the final OGs curves: step multipliers 1600/1600/1920/3200/3200, ten-stage totals 88000/88000/105600/176000/176000. Only SP cost fields and the 320-byte weapon price table changed in the canonical ISO. See sp_and_prices_revision_journal.json. The seven-option pack accepts all 256 prior eight-option profiles.\n'
 agents.write_text(text,encoding='utf-8')
 print(json.dumps({k:v for k,v in journal.items() if k!='edits'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
