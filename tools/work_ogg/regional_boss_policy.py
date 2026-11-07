"""Ten excluded lineups return as unmanned, enemy-only reconstruction models."""
import struct
from catalog import Master,u16,u32,encode
from apply_balance_25 import get_record
from regional_five_policy import append_strings

# (original unit key, unique label, base HP, armor, main weapon peak)
GROUPS=[
 [(187,'하가네（모사형）',50000,1700,4700),(329,'그레이스토크（모사형）',48000,1650,4400)],
 [(1248,'라이노세라스（반형）',56000,1750,4700),(249,'라이노세라스（한스형）',50000,1700,4500)],
 [(1233,'베르게르밀（아기라형）',48000,1600,4700),(1246,'라즈앙그리프（쿠엘보형）',52000,1750,4900)],
 [(239,'마하트（모사형）',60000,1800,4600),(238,'페레그린（모사형）',50000,1650,4400)],
 [(1166,'시로가네（모사형）',65000,1800,4700),(174,'세프타킨（복원체）',95000,1800,5000)]]

OPENING=[
 [('카이','하가네와 그레이스토크의 형상을 한 무인함이다. 함장과 승무원의 생체 반응은 없다.'),('카이','옛 전투 기록으로 움직이는 모사체다. 두 함선을 멈추고 시험장을 확보한다.')],
 [('레첼','라이노세라스 두 기다. 반과 한스가 사용했던 서로 다른 장비 구성을 재현했다.'),('료우토','통제실은 비어 있어요. 원격 지휘 회선을 끊으려면 두 기를 모두 정지시켜야 합니다.')],
 [('라투니','아기라의 전투 기록과 쿠엘보 박사의 기체 기록을 사용하고 있어요. 두 분이 타고 있는 건 아닙니다.'),('제올라','기록 속 사람을 다시 싸우게 할 수는 없어요. 저 모사 기체들을 멈춰요.')],
 [('비렛타','콜로니 바깥의 마하트와 페레그린이다. 두 함선 모두 승무원 반응 없이 움직인다.'),('라이','과거 함대의 전술을 흉내 내고 있습니다. 주민 항로에 사선을 주지 않겠습니다.')],
 [('라미아','시로가네형 무인함 뒤에 세프타킨의 복원체가 있습니다. 회수한 전투 자료를 함께 사용하고 있습니다.'),('액셀','본래의 힘을 전부 되찾은 건 아니군. 그래도 내버려 두면 항로가 막힌다. 여기서 멈춘다.')]]
STORY_OPENING=[
 [('린','다이테츠 함장님의 배를 흉내 내다니…… 저 안에 사람이 없다는 건 확인했어. 망설이지 않을게.')],
 [('비안','옛 부하의 이름을 내세울 필요는 없겠군. 저 안에 구할 사람은 없다. 병기를 멈추게.')],
 [('오우카','박사님은 나를 살리려고 남으셨어. 그 기록을 아이들을 가두는 데 쓰게 두지는 않겠어.'),('이글렛','운용 기록을 이렇게 섞었군. 내 분석은 넘기겠다. 접속 권한을 달라고 하지는 않겠어.')],
 [('메키보스','지구의 함선을 접수하던 때의 회선까지 남겼군. 이번에는 그 회선을 끊으러 왔다.')],
 [('잉그램','세프타킨의 자료를 재구성한 흔적이다. 같은 모습이라고 해서 완전한 재현은 아니다.'),('레몬','과거의 병기로 다음 전쟁을 만들게 두지는 않을 거야. 액셀렌, 엄호를 부탁해.')]]
ENDING=[
 [('카이','두 모사 함선의 지휘 회선이 멎었다. 잔해는 정비반이 확인한다.')],
 [('레첼','두 라이노세라스의 제어 장치를 확보했다. 이름을 빌린 모사 병기는 더 움직이지 않는다.')],
 [('라투니','두 기체의 제어 장치를 봉인했습니다. 스쿨의 자료도 다른 목적으로 쓰이지 않게 인계할게요.')],
 [('라이','두 무인함이 정지했습니다. 콜로니의 민간 항로를 다시 열겠습니다.')],
 [('라미아','시로가네형과 세프타킨 복원체의 정지를 확인했습니다. 새 생산에 쓰일 기록도 봉인했습니다.')]]

def rebuild_master(old):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))};parts[0x88].extend(bytes((-len(parts[0x88]))%4))
 specs=[r for group in GROUPS for r in group];startid=m.tables['Strg'][2];parts[0x80]=append_strings(parts[0x80],[encode(r[1]) for r in specs])
 units=iter(k for k in range(0x780,2048) if u16(parts[0x18],12+k*2)==65535);weapons=iter(k for k in range(0xe80,4096) if u16(parts[0x20],12+k*2)==65535)
 un=m.tables['Unit'][2];wn=m.tables['Weap'][2];notes=[]
 for i,(source,name,hp,armor,peak) in enumerate(specs):
  _,original=get_record(m,'Unit','UTbl',source,100);body=bytearray(original);key=next(units);struct.pack_into('<I',body,0,hp);struct.pack_into('<H',body,12,startid+i);struct.pack_into('<H',body,0x14,65535)
  struct.pack_into('<HH',body,0x18,450 if source==174 else 300,armor);body[0x53]=105 if source in [1233,1246,174] else 95
  # Remove regeneration that would stall a 12-unit regional battle. Ordinary
  # fields/coats/jammers remain; the original enemy/ally records are untouched.
  abilities=[a for a in body[0x57:0x5d] if a and a not in [10,11,12,14,15]]
  if source==174:abilities=[a for a in abilities if a!=9]+[2,13]
  body[0x57:0x5d]=bytes(abilities+[0]*(6-len(abilities)));body[0x5d]=0;struct.pack_into('<h',body,0x62,0)
  wrs=[(slot,w,get_record(m,'Weap','WTbl',w,36)[1]) for slot,w in enumerate(struct.unpack_from('<16H',body,0x24)) if w!=65535];oldpeak=max(u16(r,8) for slot,w,r in wrs);newweapons=[]
  for slot,w,raw in wrs:
   r=bytearray(raw);power=u16(r,8);wname=m.text(u16(r,4));status=any(s in wname for s in ['채프','네트','드레인','테이커','브레이커'])
   # Low-power status weapons keep their original damage. Main weapons gain a
   # modest proportional amount, without changing motion, range or attributes.
   if power>=2400 and not status:struct.pack_into('<H',r,8,min(peak,power+max(0,peak-oldpeak)))
   nk=next(weapons);struct.pack_into('<H',parts[0x20],12+nk*2,wn);wn+=1;parts[0x24].extend(r);struct.pack_into('<H',body,0x24+slot*2,nk)
   newweapons.append(dict(slot=slot,source_key=w,key=nk,power=u16(r,8),source_power=power,name=m.text(u16(r,4))))
  struct.pack_into('<H',parts[0x18],12+key*2,un);un+=1;parts[0x1c].extend(body);notes.append(dict(stage=35+i//2,key=key,source_key=source,name=name,hp=hp,armor=armor,mobility=body[0x53],pilot=1029,weapons=newweapons,original_unit_hex=original.hex(),unit_hex=body.hex()))
 struct.pack_into('<II',parts[0x1c],4,12+un*100,un);struct.pack_into('<I',parts[0x18],4,12+un*100);struct.pack_into('<II',parts[0x24],4,12+wn*36,wn)
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 used=len(out);assert used<=len(old);out.extend(bytes(len(old)-used));n=Master(out)
 for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
  p=m.tables[tag][0]+12;q=n.tables[tag][0]+12;assert old[p:p+m.tables[tag][2]*stride]==out[q:q+m.tables[tag][2]*stride],tag
 for tag in m.tables:
  if tag in ['UTbl','Unit','WTbl','Weap','Strg']:continue
  p,size,c=m.tables[tag];q=n.tables[tag][0];assert old[p:p+size]==out[q:q+size],tag
 assert all(m.text(i)==n.text(i) for i in range(m.tables['Strg'][2]))
 return bytes(out),dict(units=notes,weapon_count=wn-m.tables['Weap'][2],used_bytes=used,capacity=len(old),original_combat_records_preserved=True)
