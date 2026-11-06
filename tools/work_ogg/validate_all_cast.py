from build_all_cast import *
from r5900_scalar_check import CPU

def main():
 # Exercise the original game's free-slot allocation code, including its boundary.
 c=CPU((OUT/'elf_ram.bin').read_bytes());obj=0x1000000
 units=[c.run(0x243f30,[obj,0]) for i in range(129)]
 pilots=[c.run(0x243d90,[obj,0]) for i in range(193)]
 assert units==list(range(128))+[-1]
 assert pilots==list(range(192))+[-1]
 meta,rows=prepare();assert len(rows)+3<=128
 body=arc('BATTLE.BIN.1');bodykeys={k for e in body['entries'] if e['size'] for k in e['keys']}
 m=Master((OUT/'SHARED.BIN.master').read_bytes());ut=m.tables['UTbl'][0];wt=m.tables['WTbl'][0]
 for r in rows:
  idx=u16(m.b,ut+12+r['unit']*2);u=m.b[m.tables['Unit'][0]+12+idx*100:m.tables['Unit'][0]+12+(idx+1)*100]
  assert u16(u,0x44) in bodykeys,(r['unit_name'],'body absent')
  for k in struct.unpack_from('<16H',u,0x24):
   if k==65535:continue
   assert k<m.tables['WTbl'][2] and u16(m.b,wt+12+k*2)!=65535,(r['unit_name'],'weapon absent',k)
 target=ROOT/'SRWOGG_ALL_CAST_CH1.iso'
 with target.open('rb') as f:
  for name in ['SHARED.BIN','IM.BIN']:
   e=arc(name+'.3')['entries'][0];mm=Master(read(f,e['offset'],e['size']))
   for r in rows:
    for tag,lookup in [('Unit','UTbl'),('Plot','PTbl')]:assert u16(mm.b,mm.tables[lookup][0]+12+r['new_key']*2)<mm.tables[tag][2]
  for slot,magic in [(13,b'UNTD'),(14,b'LOGO')]:
   a=arc('MAP.BIN.'+str(slot));e=next(x for x in a['entries'] if 2001 in x['keys']);dp=a['directory']+8+e['index']*8;off,n=struct.unpack('<II',read(f,dp,8));b=read(f,a['directory']+off,n);assert b[:4]==magic
   if slot==13:
    assert u32(b,40)==11+len(rows)
    for i,r in enumerate(rows):
     p=44+(11+i)*336;assert u32(b,p)==u32(b,p+32)==r['new_key'] and u32(b,p+4)==32 and u32(b,p+8)==0
   else:
    co=u32(b,0x2c);assert list(struct.unpack_from('<24I',b,co+26*96))==command(0xca,32,0xffffffff)
 result=dict(native_allied_unit_capacity=128,native_allied_pilot_capacity=192,extra_allies=len(rows),original_allies=3,unit_capacity_boundary_executed=True,pilot_capacity_boundary_executed=True,body_and_weapon_references_valid=True,both_master_lookups_valid=True,all_106_placements_verified=True,native_deployment_command_verified=True,live_playthrough_verified=False)
 (ROOT/'validation_all_cast.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
