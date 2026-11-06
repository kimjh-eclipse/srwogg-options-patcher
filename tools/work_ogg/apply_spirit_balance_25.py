"""Apply roadmap step 1 to the 13 affected allied clones, using sparse rollback."""
from pathlib import Path
import json,sys,os,hashlib,ctypes,msvcrt
sys.path.insert(0,str(Path(__file__).resolve().parent/('option_spirits' if (Path(__file__).resolve().parent/'option_spirits').exists() else 'option_release')))
from build_options import rawmaster
from apply_balance_25 import get_record,u16
from story_master_25 import PROFILES
from spirit_policy_25 import POLICY,SPIRITS,apply_to_row
from story_vm import VM

ROOT=Path(__file__).resolve().parent
TARGET=ROOT.parent/'SRWOGS_EX_K_TEST.ISO'

def validate(original,modified,cast,verify_names=False):
 from catalog import Master
 old=Master(original);new=Master(modified);changed={};checks=0
 vm=VM();vm.load_master(modified)
 names={i:new.text(u16(r)) for i,p,r in new.rows('Sprt')}
 if verify_names:
  for name,key in SPIRITS.items():assert names[key]==name
 for name in PROFILES:
  key=cast[name]['new_key'];idx,row=get_record(old,'Plot','PTbl',key,148);_,got=get_record(new,'Plot','PTbl',key,148)
  assert idx>=old.tables['Plot'][2]-27
  expected=apply_to_row(name,row);assert got==expected
  if expected!=row:changed[idx]=name
  assert got[0x64]==row[0x64] and got[:0x6c]==row[:0x6c] and got[0x80:]==row[0x80:]
  for slot in range(6):
   for pc,offset in [(0x2727e0,0x6c),(0x272730,0x72),(0x272680,0x78)]:
    assert vm.cpu.run(pc,[vm.master,key,slot])==expected[offset+slot],(name,hex(pc),slot);checks+=1
   assert got[0x72+slot]>0 and (got[0x72+slot]!=1 or got[0x6c+slot]==22)
  assert vm.cpu.run(0x272600,[vm.master,key])==expected[0x7e];checks+=1
  assert vm.cpu.run(0x272580,[vm.master,key])==expected[0x7f];checks+=1
  assert expected[0x7e]>=32 and expected[0x7f]>0
  if name in ['울즈','안사즈','스리사즈']:
   for i in range(6):
    if got[0x6c+i]==10:assert got[0x72+i]==60 and got[0x78+i]==38
 assert len(changed)==13
 for i,p,row in old.rows('Plot'):
  if i not in changed:assert modified[p:p+len(row)]==row
 # The changed bytes are confined to spirit IDs, costs, levels and twin fields.
 permitted={old.tables['Plot'][0]+12+i*148+j for i in changed for j in range(0x6c,0x80)}
 assert {i for i,(a,b) in enumerate(zip(original,modified)) if a!=b}<=permitted
 return checks

def digest(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));cast={r['pilot_name']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf-8'))['cast']}
 edits=[];checks=0
 with TARGET.open('rb') as f:
  for archive in ['SHARED.BIN','IM.BIN']:
   e,m=rawmaster(f,archive);blob=bytearray(m.b)
   for name in POLICY:
    idx,row=get_record(m,'Plot','PTbl',cast[name]['new_key'],148);new=apply_to_row(name,row);at=m.tables['Plot'][0]+12+idx*148+0x6c
    assert new!=row,'Already applied or unexpected input'
    edits.append((e['offset']+at,row[0x6c:0x80],new[0x6c:0x80]));blob[at:at+20]=new[0x6c:0x80]
   checks+=validate(bytes(m.b),bytes(blob),cast,archive=='SHARED.BIN')
 edits.sort()
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];kernel.CreateFileW.restype=ctypes.c_void_p
 handle=kernel.CreateFileW(str(TARGET),0xc0000000,0,None,3,0,None)
 if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY),'r+b') as f:
  before=digest(f);assert before==state['current_sha256']
  result={'applied':False,'before_sha256':before,'step':1,'changed_pilots':list(POLICY),'unchanged_pilots':[n for n in PROFILES if n not in POLICY],'native_checks':checks,'original_pilot_and_unit_weapon_data_preserved':True,'SP_max_unchanged':True,'scout_SP1_is_native':True,'edits':[{'offset':at,'before':a.hex(),'after':b.hex()} for at,a,b in edits]}
  journal=ROOT/'spirit_balance_25_journal.json';journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  try:
   for at,a,b in edits:f.seek(at);assert f.read(len(a))==a;f.seek(at);f.write(b)
   f.flush();os.fsync(f.fileno())
   for at,a,b in edits:f.seek(at);assert f.read(len(b))==b
   after=digest(f)
  except BaseException:
   for at,a,b in edits:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert digest(f)==before;raise
 result.update(applied=True,after_sha256=after,changed_regions=len(edits),changed_region_bytes=sum(len(b) for at,a,b in edits))
 journal.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 state.update(current_sha256=after,last_edit_journal=str(journal),sp_cost_policy='native plus 13 allied-clone role corrections',spirit_balance_25_applied=True,spirit_balance_changed_pilots=13,improvement_step_completed=1)
 (ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`')
 text+='\n- Roadmap step 1 applied: 13 of the 25 allied clone pilots have role-based spirit corrections; 12 retain their sets. Uruz/Ansuz Awakening costs60 atLv38, Thurisaz is an assault profile, Tempest Love costs65 atLv38, four missing twin spirits are filled. Native pilots/enemies, SP maxima, units and weapons are unchanged. Native spirit ID/cost/level/twin getters passed 1000 checks. See spirit_policy_25.py and spirit_balance_25_journal.json. Do not let the option builder overwrite corrected clone costs with source boss costs.\n'
 agents.write_text(text,encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
