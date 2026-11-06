"""Keep private allied clones independent of native unit-family events."""
import struct
from catalog import Master,u16

def edits_for_master(blob,keys):
 m=Master(blob);edits=[]
 for key in keys:
  index=u16(blob,m.tables['UTbl'][0]+12+key*2);assert index<m.tables['Unit'][2]
  at=m.tables['Unit'][0]+12+index*100
  variants=[at]
  if blob[at+0x5d]:
   delta=struct.unpack_from('<h',blob,at+0x62)[0];assert delta and delta%100==0
   variants.append(at+delta)
  for pos in variants:
   assert m.tables['Unit'][0]+12<=pos< m.tables['WTbl'][0]
   if blob[pos+0x14:pos+0x16]!=b'\xff\xff':edits.append((pos+0x14,blob[pos+0x14:pos+0x16],b'\xff\xff',key))
 return edits

def apply_to_master(blob,keys):
 b=bytearray(blob)
 for at,old,new,key in edits_for_master(blob,keys):b[at:at+2]=new
 return bytes(b)

STORY_RECOVERY=0x1b500000
NATIVE_RECOVERY=0x1b530000

def recovery_script(blob):
 from story_scripts_25 import records,command
 from campaign_bonus_scripts import insert_commands
 rows=records(blob)
 marker=[0x4a,0x100bd,0x701,1]
 existing=[i for i,r in enumerate(rows) if [r[0],*r[2:5]]==marker]
 if existing:
  assert len(existing)==1;return blob
 point=next(i+1 for i,r in enumerate(rows) if [r[0],*r[2:5]]==[0x4a,0x100bd,0x4ad,1])
 return insert_commands(blob,point,[command(0x4a,0x100bd,0x701,1)])

def native_recovery(original,archive):
 from inspect_iso import read
 entry=next(e for e in archive['entries'] if 2026 in e['keys'])
 at=archive['directory']+8+entry['index']*8
 rel,size=struct.unpack('<II',read(original,at,8))
 blob=recovery_script(read(original,archive['directory']+rel,size))
 pointer=struct.pack('<II',NATIVE_RECOVERY-archive['directory'],len(blob))
 return blob,pointer
