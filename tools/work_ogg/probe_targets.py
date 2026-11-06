from catalog import *
def main():
 cat=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
 for name in ['SHARED.BIN','IM.BIN']:
  b=(OUT/(name+'.master')).read_bytes();m=Master(b)
  print(name,'length',hex(len(b)),'lastnonzero',hex(len(b.rstrip(b'\0'))),'sent',m.tables['Sent'])
  for tag,keytag,keys in [('Unit','UTbl',[0x23,0x4c,0x9f,0x58,0x456]),('Plot','PTbl',[0x3e,0x75,0x45d])]:
   at=m.tables[keytag][0]
   for key in keys:print(tag,hex(key),u16(b,at+12+key*2))
  for k in ['Sprt','Skil']:
   a,size,c=m.tables[k];n=(size-12)//c
   print(k,'stride',n,[(i,b[a+12+i*n:a+12+(i+1)*n].hex()) for i in range(min(c,4))])
 with SOURCE.open('rb') as f:
  for catkey in ['Unit','Plot']:
   print('TARGETS',catkey)
   for e in cat[catkey]:
    if any(x in e['name'] for x in ['잉그램','비안','레비','웬드','메키','아기하','시카','빈델','워단','쥬데','디카','그레','실버','드루','츠바','슬레이','리바레']):
     print(e['index'],e['keys'],e['name'])
  a=json.loads((OUT/'MAP.BIN.13.json').read_text());b=json.loads((OUT/'MAP.BIN.14.json').read_text())
  for key in [2001,2006]:
   e=next(e for e in a['entries'] if key in e['keys']);raw=read(f,e['offset'],e['size']);(OUT/f'unit_{key}.bin').write_bytes(raw)
   print('UNIT TABLE',key,e['index'],e['size'],u32(raw,40))
   for i in range(min(u32(raw,40),8)):
    r=raw[44+i*336:44+(i+1)*336];print(i,[hex(x) for x in struct.unpack_from('<9I',r)],'head',r[:0x90].hex())
   e=next(e for e in b['entries'] if key in e['keys']);raw=read(f,e['offset'],e['size']);(OUT/f'script_{key}.bin').write_bytes(raw)
   rs=[struct.unpack_from('<24I',raw,u32(raw,44)+i*96) for i in range(u32(raw,40))]
   print('SCRIPT',key,'control ops',[(i,hex(r[0]),[hex(v) for v in r[2:9]]) for i,r in enumerate(rs) if r[0] in (0x5e,0x5a,0xc5,0,0x23)])
  voice=json.loads((OUT/'BATTLE.BIN.5.json').read_text());print('VOICE62',[x for x in voice['entries'] if 62 in x['keys']])
if __name__=='__main__':main()
