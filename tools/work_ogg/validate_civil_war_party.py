"""Exercise temporary splits on a populated original and added roster."""
from validate_civil_war import *

def main():
 p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));v=machine(ram(Profiles(),4095),(DEST/'SHARED.BIN.master').read_bytes());seed_clones(v)
 for name,x in p['members'].items():
  if x['added']:continue
  if x['template']:
   row=bytearray(normalize(bytes.fromhex(x['template'])));struct.pack_into('<I',row,32,x['pilot']);assert v.birth(row)==1,name
  elif x['pilot'] is not None and v.cpu.run(0x244a40,[v.save,x['pilot'],1,0])<0:
   slot=v.cpu.run(0x24b180,[v.save,x['pilot'],0]);assert slot>=0;v.cpu.run(0x247c60,[v.save,2,slot,1,0])
 refs={}
 for i,(name,x) in enumerate(p['members'].items()):
  slots=[]
  for typ,key in [('unit',x['unit']),('pilot',x['pilot'])]:
   if key is None:slots.append(None);continue
   index=v.cpu.run(0x244c20 if typ=='unit' else 0x244a40,[v.save,key,0 if typ=='unit' else 1,0]);assert index>=0,(name,typ,key)
   at=v.save+(0x6efc+index*216 if typ=='unit' else 0x25cfc+index*92);slots.append((at,216 if typ=='unit' else 92))
   if typ=='pilot':v.cpu.write(at+6,35+i,2);v.cpu.write(at+8,401+i*11,2);v.cpu.write(at+10,24000+i*500,2)
  refs[name]=slots
 def snap():return {name:tuple(bytes(v.cpu.mem[at:at+n]) if ref else None for ref in slots for at,n in ([ref] if ref else [(0,0)])) for name,slots in refs.items()}
 initial=snap();cases=0
 # Replay exact availability records embedded in the actual new scripts.
 sequences=[(next(b for b in p['bridges'] if b['key']==2040),'bridge')]+[(s,'scene') for s in p['scenes']]
 for scene,kind in sequences:
  blob=(DEST/scene['logo']['file']).read_bytes()
  for row in records(blob):
   if row[0]!=0x4a:continue
   assert row[2]==0x100a8 and row[4] in [0,1];assert v.op(row)==10;cases+=1
   current=snap()
   for name,before in initial.items():
    for typ,(a,b) in enumerate(zip(before,current[name])):
     if a is None:assert b is None;continue
     allowed=42 if typ==0 else 2
     assert all(x==y for at,(x,y) in enumerate(zip(a,b)) if at!=allowed),(scene['key'],name,typ)
 assert snap()==initial,'Final reunion did not restore original availability'
 result=dict(passed=True,members=len(refs),native_members=sum(not x['added'] for x in p['members'].values()),added_members=25,embedded_availability_commands=cases,unit_upgrades_equipment_and_pilot_EXP_PP_kills_preserved=True,all_initial_roster_bytes_restored_after_reunion=True,custom_preinactive_roster_not_tested=True,live_gameplay=False)
 (ROOT/'civil_war_party_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
