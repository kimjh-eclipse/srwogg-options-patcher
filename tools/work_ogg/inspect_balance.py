"""Read current OGG stats; writes only a small analysis report, never an ISO."""
from catalog import *
from compare_ogs_units import getmaster

TARGET=ROOT.parent/'SRWOGS_EX_K_TEST.ISO'

def main():
 m=getmaster(TARGET);rows=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast']
 rows=[r for r in rows if r['pilot_name'] not in ['아기라','세프타킨','셉타긴']]
 assert len(rows)==25
 byname={}
 for i,p,r in m.rows('Unit'):byname.setdefault(m.text(u16(r,12)),[]).append((i,r))
 result={'target':str(TARGET),'cast':[],'benchmarks':[]}
 def item(r):
  return dict(hp=u32(r),en=u16(r,0x18),mobility=r[0x53],armor=u16(r,0x1a),move=r[0x52],
              halfwords=list(struct.unpack('<18H',r[:36])),tail=list(r[0x44:]),raw=r.hex())
 for r in rows:
  idx=u16(m.b,m.tables['UTbl'][0]+12+r['new_key']*2);b=m.b[m.tables['Unit'][0]+12+100*idx:m.tables['Unit'][0]+12+100*(idx+1)]
  d={**r,**item(b),'unit_record':idx,'weapons':[]}
  for w in struct.unpack_from('<16H',b,0x24):
   if w==65535:continue
   wi=u16(m.b,m.tables['WTbl'][0]+12+w*2);wrec=m.b[m.tables['Weap'][0]+12+wi*36:m.tables['Weap'][0]+12+(wi+1)*36]
   d['weapons'].append(dict(key=w,index=wi,name=m.text(u16(wrec,4)),power=u16(wrec,8),halfwords=list(struct.unpack('<18H',wrec)),raw=wrec.hex()))
  result['cast'].append(d)
  print(r['pilot_name'],r['unit_name'],'HP',d['hp'],'EN',d['en'],'운동',d['mobility'],'장갑',d['armor'],'이동',d['move'],'무기',[(w['name'],w['power']) for w in d['weapons']])
 for name,ls in byname.items():
  if any(s in name for s in ['알트아이젠','라인바이스','다이젠가','소울게인','안쥬르그','바이사가','빌트뷔르','Ｒ－１','Ｒ－ＧＵＮ파워','휴케바인Ｍｋ－Ⅲ','게슈펜스트Ｍｋ－Ⅱ개','발시오네']):
   for i,b in ls:
    d=dict(name=name,index=i,**item(b),weapons=[]);result['benchmarks'].append(d)
    for w in struct.unpack_from('<16H',b,0x24):
     if w==65535:continue
     wi=u16(m.b,m.tables['WTbl'][0]+12+w*2);wr=m.b[m.tables['Weap'][0]+12+wi*36:m.tables['Weap'][0]+12+(wi+1)*36]
     d['weapons'].append(dict(key=w,name=m.text(u16(wr,4)),power=u16(wr,8)))
    if d['hp']<15000:print('REF',name,i,'HP',d['hp'],'EN',d['en'],'운동',d['mobility'],'장갑',d['armor'],'무기',[(w['name'],w['power']) for w in d['weapons']])
 (OUT/'balance_current_readonly.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
