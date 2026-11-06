"""Check follow-up scene selection in all profiles without writing any ISO."""
from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT)]
from validate_options import Profiles,Image,legacy_checks,ram
from audit_story_layout import loadarc
from story_scripts_25 import records,text_at
from story_consistency_logo import guarded_block
from story_vm import VM
from early_equipment_policy import FLAG as EARLY_FLAG,UNITS,WEAPONS
from prepare_early_equipment import execute as early_execute,qty
from campaign_bonus_scripts import EARLY

def execute(vm,blob,start,end):
 rs=records(blob);i=start;shown=[]
 while i<end:
  r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
  if r[0]==0x30:shown.append(r[2]);i+=1;continue
  assert r[0] in [0x93,0x91,0xba]
  assert vm.op(r)==10;i=vm.cpu.read(vm.ctx+0x48d0,4)+1
 return shown

def main():
 p=Profiles();meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf-8'))
 prep=json.loads((ROOT/'followup_story_prepared.json').read_text(encoding='utf-8'))
 old_native=json.loads((ROOT/'followup_story_validation.json').read_text(encoding='utf-8'))
 assert old_native['passed'];count=messages=0
 for mask in range(1024):
  image=Image(p,mask)
  try:
   _,es=loadarc(image,14)
   for scene in prep['scenes']:
    _,at,size=next(e for e in es if scene['key'] in e[0]);image.seek(at);blob=image.read(size)
    if mask&1:
     assert at==scene['offset'] and size==scene['size']
     start,end=guarded_block(blob,scene['flag'])
     assert len([r for r in records(blob)[start:end] if r[0]==0x30])==len(scene['messages'])
     for msg in scene['messages']:
      assert text_at(blob,msg['string_id'])==bytes.fromhex(msg['encoded']);messages+=1
     if scene['chapter']==29:
      ms,me=guarded_block(blob,[63,1]);assert end==ms
      assert records(blob)[ms+1][4]==(0 if mask&256 else 2)
    else:
     assert at!=scene['offset']
     assert not any(r[0]==0x93 and r[2:5]==[0x100c1,*scene['flag']] for r in records(blob))
    count+=1
   _,at,size=next(e for e in es if 2003 in e[0]);image.seek(at);blob=image.read(size)
   start,end=guarded_block(blob,EARLY_FLAG);rs=records(blob)
   assert rs[start+1][4]==(0 if mask&512 else 2)
   assert [(r[0],r[2]) for r in rs[start:end] if r[0] in [0x5f,0x64]]==[(0x5f,k) for k,n in UNITS]+[(0x64,k) for k,n in WEAPONS]
   assert all(r[3:6]==[0xdeaddeed]*3 for r in rs[start:end] if r[0]==0x5f)
   assert end==guarded_block(blob,[63,7])[0]
  finally:image.f.close()
 native=[];base=ram(p,511)
 for mask in [1,257]:
  image=Image(p,mask);_,es=loadarc(image,14);_,at,size=next(e for e in es if 2027 in e[0]);image.seek(at);blob=image.read(size);image.f.close()
  start,end=guarded_block(blob,[63,2]);ms,me=guarded_block(blob,[63,1]);vm=VM(base)
  shown=execute(vm,blob,start,me);assert len(shown)==16+(3 if mask&256 else 0)
  assert not execute(vm,blob,start,me)
  native.append({'mask':mask,'followup_boxes':16,'maintenance_boxes':len(shown)-16,'repeat_boxes':0})
 # All feature edits other than story pointers / its optional dialogue guard
 # must be byte-identical to the preceding nine-option release.
 from build_options import load_pack,PREVIOUS_PACK
 old=load_pack(PREVIOUS_PACK)[1]
 moved=0
 for a,b in zip(p.features[1],old[1]):
  assert a[1]==b[1]
  if a[0]!=b[0]:
   s=next(s for s in prep['scenes'] if s['chapter']==25)
   assert s['offset']<=a[0]<s['offset']+s['size']
   assert s['old_offset']<=b[0]<s['old_offset']+s['old_size'];moved+=1
 assert moved==2
 assert len(p.features[2])==len(old[2])==2
 assert [b for at,b in p.features[2]]==[b for at,b in old[2]]
 for bit in range(3,8):assert p.features[bit]==old[bit],bit
 assert p.features[8][:-1]==old[8][:-1]
 assert p.features[8][-1][1]==old[8][-1][1]
 assert len(p.features[8][-1][1])==96
 equipment=[]
 for mask in [0,1,4,5,512,513,516,517]:
  image=Image(p,mask);_,master=__import__('build_options').rawmaster(image,'SHARED.BIN');_,es=loadarc(image,14);_,at,size=next(e for e in es if 2003 in e[0]);image.seek(at);blob=image.read(size);image.f.close();vm=VM(base);vm.load_master(master.b)
  assert early_execute(vm,blob,bool(mask&512))==(4 if mask&512 else 0)
  for key,name in UNITS:assert (vm.cpu.run(0x244c20,[vm.save,key,0,0])>=0)==bool(mask&512)
  assert [qty(vm,k) for k,n in WEAPONS]==[int(bool(mask&512))]*2
  # The independent eight-supply block must still execute or skip correctly.
  rs=records(blob);start,end=guarded_block(blob,[63,7]);i=start;grants=0
  while i<end:
   r=rs[i];vm.cpu.write(vm.ctx+0x48d0,i,4)
   if r[0]==0x30:i+=1;continue
   assert r[0] in [0x93,0x91,0x60,0x64,0xba];assert vm.op(r)==10;grants+=r[0] in [0x60,0x64];i=vm.cpu.read(vm.ctx+0x48d0,4)+1
  assert grants==(8 if mask&4 else 0)
  assert early_execute(vm,blob,bool(mask&512))==0
  for key,name in WEAPONS:assert qty(vm,key)==int(bool(mask&512))
  equipment.append({'mask':mask,'story':bool(mask&1),'eight_supplies':bool(mask&4),'early_equipment':bool(mask&512),'early_grants':4 if mask&512 else 0,'supply_grants':grants,'repeat_grants':0})
 result={'passed':True,'pack_sha256':meta['pack_sha256'],'profiles':1024,'scene_profile_checks':count,'encoded_dialogue_comparisons':messages,'story_off_uses_original_scripts':True,'other_feature_edits_preserved':True,'new_chapter32_directory_switch_checked':True,'chapter29_native_composed_profiles':native,'early_equipment_selection_checks':1024,'early_equipment_independence':equipment,'legacy_recognition':legacy_checks(p),'live_playthrough':False,'ISO_writes_performed':False}
 (HERE/'followup_options_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
