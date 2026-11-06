"""Port the recorded common OGs balance changes, preserving OGG's own base buffs."""
from catalog import *
from compare_ogs_units import getmaster
from apply_balance_25 import get_record

SOURCE_BALANCED=ROOT.parent/'work_ogs/build/SRWOGS_K.iso'
SOURCE_VANILLA=ROOT.parent/'슈퍼 로봇 대전 OG (K).iso'

def weapon_plan(target):
 source=getmaster(SOURCE_BALANCED);vanilla=getmaster(SOURCE_VANILLA)
 entries=json.loads((ROOT.parent/'work_ogs/runtime/weapon_balance_manifest.json').read_text(encoding='utf8'))['weapons']
 indices={int(e['index'],16) for e in entries}|{0x2a3,0x1d5,0x1d9}
 policies={}
 for idx in sorted(indices):
  keys=[k for k in range(4096) if u16(source.b,source.tables['WTbl'][0]+12+k*2)==idx];assert keys
  key=keys[0];_,old=get_record(vanilla,'Weap','WTbl',key,36);_,new=get_record(source,'Weap','WTbl',key,36)
  policies[key]=(old,new,idx)
 edits=[];notes=[]
 with target.open('rb') as f:
  for ar in ['SHARED.BIN','IM.BIN']:
   e=json.loads((OUT/(ar+'.3.json')).read_text())['entries'][0];raw=read(f,e['offset'],e['size']);m=Master(raw)
   for key,(stock,balanced,sourceidx) in policies.items():
    idx,r=get_record(m,'Weap','WTbl',key,36);n=bytearray(r)
    # Add the same power delta, rather than overwriting Gaiden's improved weapons.
    power=u16(r,8)+u16(balanced,8)-u16(stock,8);assert 0<=power<=65535
    if u16(r,8):struct.pack_into('<H',n,8,power)
    else:assert u16(stock,8)==u16(balanced,8)==0
    if sourceidx in {int(e['index'],16) for e in entries}:
     n[0x15]=(n[0x15]&~0x30)|(balanced[0x15]&0x30)
    if stock[3]&0x3f!=balanced[3]&0x3f:n[3]=(n[3]&0xc0)|(balanced[3]&0x3f)
    for p in [0x17,0x18,0x1a,0x1b]:
     if stock[p]!=balanced[p]:n[p]=balanced[p]
    mask=stock[0x14]^balanced[0x14];n[0x14]=(n[0x14]&~mask)|(balanced[0x14]&mask)
    if sourceidx==0x312:n[0x14]=(n[0x14]&~0x88)|(balanced[0x14]&0x88)
    assert n[:3]==r[:3] and n[4:8]==r[4:8] and n[0x1c:]==r[0x1c:]
    allowed={3,8,9,0x14,0x15,0x17,0x18,0x1a,0x1b}
    assert {p for p in range(36) if n[p]!=r[p]}<=allowed
    if n!=r:
     at=e['offset']+m.tables['Weap'][0]+12+idx*36;edits.append((at,r,bytes(n),f'{ar} common weapon key {key}'))
     if ar=='SHARED.BIN':notes.append(dict(key=key,name=m.text(u16(r,4)),power_before=u16(r,8),power_after=u16(n,8),en_before=r[0x1a],en_after=n[0x1a],morale_before=r[0x1b],morale_after=n[0x1b],barrier=(n[0x15]>>4)&3,cost_tier=n[3]&7,growth_tier=(n[3]>>3)&7,all_attack=bool(n[0x14]&0x80),motion_preserved=True))
  values=[s*i for s in [2000,3000,5000,6500,7500] for i in range(16)];old=struct.pack('<80I',*values)
  elf=next(x for x in inventory(f) if x['name'].startswith('SLPS_'));b=read(f,elf['offset'],elf['size']);p=b.find(old)
  assert p>=0 and b.find(old,p+1)<0
  new=struct.pack('<80I',*(v if i<16 else v*4//5 for i,v in enumerate(values)))
  edits.append((elf['offset']+p,old,new,'weapon upgrade cost tiers 1-4 minus 20 percent'))
 edits.sort();return edits,dict(weapons=notes,balanced_source=str(SOURCE_BALANCED),power_policy='same delta relative to OGG base; existing Gaiden-only improvements retained',discount_tiers=[1,2,3,4],cheapest_tier_preserved=True,cost_table_virtual=0x100000+p-0x180)
