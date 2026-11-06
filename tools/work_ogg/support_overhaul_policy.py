"""Optional support equipment and modest late maintenance for six allies."""
SUPPORT_ITEMS=[(0x64,3557,'수리장치'),(0x64,3558,'보급장치')]
SUPPORT_FLAG=(63,0)
MAINTENANCE_FLAG=(63,1)
THRESHOLD=29  # 29 chapters cleared: chapter30 onward
# slot -> changed EN cost / ammunition. No power/range/P/accuracy changes.
TUNING={
 '가루인':{0:{'en':25},1:{'ammo':10}},
 '텐잔':{1:{'en':18},3:{'ammo':10}},
 '토머스':{1:{'en':18},3:{'ammo':10}},
 '유리아':{2:{'ammo':10}},
 '지벨':{2:{'en':35}},
 '이글렛':{0:{'en':20}}
}
SUPPORT_STORY=0x1b3b3800
MAINTENANCE_STORY=0x1b4a0000
SUPPORT_NATIVE=0x1b4d0000

def rebuild_master(old,cast):
 import struct
 from catalog import Master,u16,u32
 from apply_balance_25 import get_record,logical_strings
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:(starts[i+1] if i+1<len(starts) else p+u32(old,p+4))]) for i,(k,p) in enumerate(zip(fields,starts))};parts[0x88].extend(bytes((-len(parts[0x88]))%4))
 free=iter(k for k in range(0xe00,4096) if u16(parts[0x20],12+k*2)==65535);unit_count=m.tables['Unit'][2];weapon_count=m.tables['Weap'][2];notes=[];allowed=set()
 for name,changes in TUNING.items():
  key=cast[name]['new_key'];ui,body=get_record(m,'Unit','UTbl',key,100);assert not body[0x5d] and body[0x62:0x64]==b'\0\0';full=bytearray(body);early_index=unit_count;unit_count+=1;parts[0x1c].extend(body);weapons=[]
  for slot,values in changes.items():
   wk=u16(body,0x24+slot*2);wi,row=get_record(m,'Weap','WTbl',wk,36);new=bytearray(row)
   for field,value in values.items():
    rel=0x1a if field=='en' else 0x19
    assert (0<value<row[rel] and row[rel]-value<=5) if field=='en' else (value==row[rel]+2)
    new[rel]=value
   assert {i for i in range(36) if new[i]!=row[i]}<={0x19,0x1a}
   nk=next(free);idx=weapon_count;weapon_count+=1;parts[0x24].extend(new);struct.pack_into('<H',parts[0x20],12+nk*2,idx);struct.pack_into('<H',full,0x24+slot*2,nk)
   weapons.append({'slot':slot,'old_key':wk,'new_key':nk,'name':m.text(u16(row,4)),'power':u16(row,8),'before_en':row[0x1a],'after_en':new[0x1a],'before_ammo':row[0x19],'after_ammo':new[0x19]})
  full[0x5d]=THRESHOLD;struct.pack_into('<h',full,0x62,(early_index-ui)*100);parts[0x1c][12+ui*100:12+(ui+1)*100]=full;allowed.add(ui)
  notes.append({'name':name,'key':key,'full_index':ui,'early_index':early_index,'threshold':THRESHOLD,'weapons':weapons,'before_unit_hex':body.hex(),'after_unit_hex':full.hex()})
 struct.pack_into('<II',parts[0x1c],4,12+unit_count*100,unit_count);struct.pack_into('<I',parts[0x18],4,12+unit_count*100)
 struct.pack_into('<II',parts[0x24],4,12+weapon_count*36,weapon_count)
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old);out.extend(bytes(len(old)-used));n=Master(out)
 for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
  for i in range(m.tables[tag][2]):
   if tag=='Unit' and i in allowed:continue
   a=m.tables[tag][0]+12+i*stride;b=n.tables[tag][0]+12+i*stride;assert old[a:a+stride]==out[b:b+stride],(tag,i)
 for tag in ['Strg','Sent','Expl']:assert logical_strings(m,tag)==logical_strings(n,tag)
 for tag in m.tables:
  if tag in ['Unit','Weap','UTbl','WTbl']:continue
  a,size,count=m.tables[tag];b=n.tables[tag][0];assert old[a:a+size]==out[b:b+size],tag
 return bytes(out),{'units':notes,'used_bytes':used,'capacity':len(old),'original_weapons_preserved':True,'other_units_and_pilots_preserved':True}

def support_script(blob,point,speakers):
 from story_scripts_25 import rebuild_logo,records,command
 from campaign_bonus_scripts import insert_commands
 lines=[('카이','지원 장비를 인계한다. 수리장치와 보급장치를 각각 하나씩 준비했다.'),('카이','환장 무장 목록에서 장비해라. 지원을 맡길 기체는 각자 정하도록.')]
 out,note=rebuild_logo(blob,point,lines,speakers,SUPPORT_FLAG)
 stop=next(i for i,r in enumerate(records(out)) if r[0]==0xba and r[2:5]==[0x100c1,*SUPPORT_FLAG])
 out=insert_commands(out,stop,[command(op,key,0) for op,key,name in SUPPORT_ITEMS])
 return out,note

def maintenance_script(blob,speakers):
 from story_scripts_25 import rebuild_logo,records
 point=next(i for i,r in enumerate(records(blob)) if r[0]==0x30 and r[2]==619)
 lines=[('카이','정비반이 여섯 기체의 급탄계와 소비 전력을 점검했다. 다음 출격부터 반영한다.'),('린','기본 화력은 그대로야. 가루인, 텐잔, 토머스의 기체부터 운용 기록을 대조했어.'),('린','유리아와 지벨, 이글렛의 기체도 마쳤어. 늘어난 탄수는 정비나 보급 후 확인해 줘.')]
 return rebuild_logo(blob,point,lines,speakers,MAINTENANCE_FLAG)
