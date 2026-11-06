"""Native text/history and persistent event checks before the ISO is written."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_consistency' if (ROOT/'option_consistency').exists() else 'option_release')),str(ROOT)]
from validate_options import Profiles,ram
from build_options import rawmaster
from story_vm import VM
from story_scripts_25 import records,text_at,decode
from story_consistency_logo import guarded_block
from story_consistency_policy import FINAL_RESPONSE_FLAG
from validate_party_25 import guard_reload_checks
from audit_story_layout import loadarc
from inspect_iso import read,u32

def main():
 plan=json.loads((ROOT/'story_consistency_prepared.json').read_text(encoding='utf-8'));assert plan['passed'];story=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf-8'));meta={c['chapter']:c for c in story['chapters']};base=ram(Profiles(),127);vm=VM(base);c=vm.cpu;cases=0;histories=0;kept=0;blobs={};chapters=[]
 with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
  _,master=rawmaster(f,'SHARED.BIN');_,entries=loadarc(f,14)
  # The added final response uses a previously unused persistent bit.
  for keys,at,n in entries:
   b=read(f,at,n)
   if b[:4]==b'LOGO':assert not any(r[0] in [0x93,0xba] and r[2:5]==[0x100c1,*FINAL_RESPONSE_FLAG] for r in records(b))
  for ch in plan['chapters']:
   b=(ROOT/'analysis/consistency_prepared'/f'{ch["key"]}.logo').read_bytes();old=read(f,ch['offset'],ch['old_size']);blobs[ch['key']]=b;rs=records(b);changed={e['string_id'] for e in ch['replacements']};new_scene=ch['new_scene'];co=u32(b,44);prefix=u32(b,32)
   assert len(b)==ch['new_size'] and u32(b,4)==u32(b,108)==len(b)
   assert co==u32(b,36)+prefix*96
   for sid in range(u32(old,64)+u32(old,80)-1):
    if sid not in changed:assert text_at(old,sid)==text_at(b,sid);kept+=1
   for index,row in enumerate(rs):
    if row[0] in [0x90,0x91]:
     for field in ([6,7] if row[0]==0x90 else [7]):
      if row[field]<0x80000000:assert 0<=index+row[field]<=len(rs)
   # Every old dialogue label still resolves to the same logical line.
   for i,r in enumerate(rs):
    if r[0]!=0x30:continue
    assert r[1]<u32(b,56)
    assert u32(b,u32(b,60)+r[1]*4)==prefix+i,(ch['chapter'],i,r[1]);histories+=1
   test_sids=changed|{r[2] for i,r in enumerate(rs) if r[0]==0x30 and ch['movement'] and ch['movement']['new_range'][0]<=i<ch['movement']['new_range'][1]}
   if new_scene:test_sids.update(m['string_id'] for m in new_scene['messages'])
   # Native lookup exercises the real loader, string buffer and dialogue log.
   address=0x1800000;c.mem[address:address+len(b)]=b;c.run(0x5363c0,[vm.ctx,address])
   for row in rs:
    if row[0]!=0x30 or row[2] not in test_sids:continue
    raw=text_at(b,row[2]);assert 0<len(raw)<128
    c.run(0x53ad00,[vm.ctx,0,row[2]]);assert bytes(c.mem[vm.ctx+0x6c00:vm.ctx+0x6c00+len(raw)+1])==raw+b'\0'
    c.run(0x53a1f0,[vm.ctx,row[1],0,0,0],stop=0x53a244);ix=c.r[4]&0xffffffff;assert u32(b,u32(b,36)+ix*96+8)==row[2];cases+=2
   start,end=guarded_block(b,meta[ch['chapter']]['flag'])
   if ch['chapter']==28:
    assert next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==254)<start
    assert sum(r[0]==0x4a and r[2:5]==[0x100bd,0x701,1] for r in rs)==1
   if ch['chapter']==35:assert next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==193)<start<next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==194)
   if ch['chapter']==36:
    assert end<=next(i for i,r in enumerate(rs) if r[0]==0x30 and r[2]==712)
    assert [r for r in rs if r[0]==0x30][-1][2]==718
   chapters.append({'chapter':ch['chapter'],'replacement_boxes':len(ch['replacements']),'movement':bool(ch['movement']),'new_scene':bool(new_scene)})
 print('Text/history and scene ordering checks passed.',flush=True)
 # All 25 existing recruit constructors and persistent guards still work with
 # the prospective scripts; no extra ISO is materialized for this check.
 recruitment=guard_reload_checks(base,master.b,blobs)
 vm=VM(base);b=blobs[2034];rs=records(b);start,end=guarded_block(b,FINAL_RESPONSE_FLAG)
 def final_block():
  i=start;messages=0
  while i<end:
   r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
   if r[0]==0x30:messages+=1;i+=1;continue
   assert r[0] in [0x93,0x91,0xba];assert vm.op(r)==10;i=vm.cpu.read(vm.ctx+0x48d0,4)+1
  return messages
 assert final_block()==3 and final_block()==0
 result={'passed':True,'live_playthrough':False,'changed_chapters':len(chapters),'replacement_boxes':sum(c['replacement_boxes'] for c in chapters),'new_response_boxes':3,'native_text_history_checks':cases,'dialogue_history_entries_checked':histories,'unchanged_logical_strings_checked':kept,'native_records_preserved':True,'movement_within_existing_event':True,'chapter28_recovery_preserved':True,'final_original_closing_lines_preserved':True,'new_scene_repeat_skipped':True,'recruitment_and_reload':recruitment,'chapters':chapters,'notes':'Native save routines; map/group fixtures and fresh VM reloads as specified in party validator. No PCSX2 full playthrough.'}
 (ROOT/'story_consistency_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
