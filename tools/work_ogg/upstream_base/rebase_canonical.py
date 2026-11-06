"""Merge the official base by asset/semantic string ID, keeping custom masters."""
from pathlib import Path
import sys,json,zlib,base64,hashlib,os,ctypes,msvcrt
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'option_revision'),str(HERE.parent)]
from source_image import source_image,DATA,CHANGES
from build_options import rawmaster
from inspect_iso import SOURCE,ROOT,read,u32
from apply_balance_25 import logical_strings

def digest(f):
 f.seek(0);h=hashlib.sha256()
 while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));target=Path(state['canonical_iso']);edits={};strings=[]
 with SOURCE.open('rb') as old,source_image() as new,target.open('rb') as current:
  entry,om=rawmaster(old,'SHARED.BIN');_,nm=rawmaster(new,'SHARED.BIN');ce,cm=rawmaster(current,'SHARED.BIN')
  for at,after,before in CHANGES:
   original=read(current,at,len(after));merged=bytearray(original)
   for i,(a,b) in enumerate(zip(before,after)):
    if a==b or entry['offset']<=at+i<entry['offset']+entry['size']:continue
    assert original[i] in [a,b],('asset conflict',hex(at+i))
    merged[i]=b
   if merged!=original:edits[at]=(original,bytes(merged))
  for tag in ['Strg','Sent']:
   aa=logical_strings(om,tag);bb=logical_strings(nm,tag);cc=logical_strings(cm,tag);tp=cm.tables[tag][0]
   for i,(a,b) in enumerate(zip(aa,bb)):
    if a==b:continue
    assert cc[i]==a and len(b)<=len(a),('logical conflict',tag,i)
    at=ce['offset']+tp+u32(cm.b,tp+12+i*4);value=b+bytes(len(a)-len(b))
    if at in edits:assert edits[at]==(a,value)
    edits[at]=(a,value);strings.append({'table':tag,'index':i,'before':a.hex(),'after':b.hex()})
 ordered=sorted((at,a,b) for at,(a,b) in edits.items())
 for a,b in zip(ordered,ordered[1:]):assert a[0]+len(a[1])<=b[0]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];kernel.CreateFileW.restype=ctypes.c_void_p
 handle=kernel.CreateFileW(str(target),0xc0000000,0,None,3,0,None)
 if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 with os.fdopen(msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY),'r+b') as f:
  before=digest(f);assert before==state['current_sha256']
  report={'applied':False,'before_sha256':before,'official_base_sha256':DATA['base_sha256'],'official_base_md5':DATA['base_md5'],'upstream_verified_windows':557,'semantic_strings':strings,'edits':[{'offset':at,'before':a.hex(),'after':b.hex()} for at,a,b in ordered],'custom_unit_pilot_weapon_tables_preserved':True,'extra_full_ISOs_created':0}
  journal=ROOT/'upstream_rebase_journal.json';journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  for at,a,b in ordered:assert read(f,at,len(a))==a
  try:
   for at,a,b in ordered:f.seek(at);f.write(b)
   f.flush();os.fsync(f.fileno())
   for at,a,b in ordered:assert read(f,at,len(b))==b
   _,now=rawmaster(f,'SHARED.BIN')
   for tag in ['Unit','Plot','Weap','UTbl','PTbl','WTbl']:
    at,size,count=cm.tables[tag];nxt=min([x[0] for x in cm.tables.values() if x[0]>at]+[len(cm.b)])
    assert now.b[at:nxt]==cm.b[at:nxt],tag
   for tag in ['Strg','Sent']:
    actual=logical_strings(now,tag);expected=logical_strings(cm,tag)
    for item in strings:
     if item['table']==tag:expected[item['index']]=bytes.fromhex(item['after'])
    assert actual==expected
   after=digest(f)
  except BaseException:
   for at,a,b in ordered:f.seek(at);f.write(a)
   f.flush();os.fsync(f.fileno());assert digest(f)==before;raise
 report.update(applied=True,after_sha256=after,changed_regions=len(ordered),semantic_string_count=len(strings))
 journal.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 state.update(current_sha256=after,last_edit_journal=str(journal),base_patch_repository=DATA['official_repository'],base_patch_version='1.4.3s',base_patch_sha256=DATA['base_sha256'],base_patch_md5=DATA['base_md5'])
 (ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8').replace('The last verified canonical SHA-256 is `'+before+'`','The last verified canonical SHA-256 is `'+after+'`')
 text+='\n- The base is now z3oo3z/PS2-SRWOGG-KPatch release SRWOGG, v1.4.3s, verified from JP MD5 cb7dc4485f46f220c46095c966a3aad0 and all 557 VCDIFF checksums. Official Korean base SHA-256 '+DATA['base_sha256']+'. The old SRWOGS_EX_K.ISO stays read-only. A sparse source_image overlay provides the new baseline without another ISO copy. Native master strings were merged by Strg/Sent ID; all custom Unit/Plot/Weap tables were preserved. See upstream_rebase_journal.json.\n'
 agents.write_text(text,encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['edits','semantic_strings']},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
