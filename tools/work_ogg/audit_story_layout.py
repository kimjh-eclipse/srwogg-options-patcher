from catalog import *
from compare_ogs_units import getmaster
from collections import Counter

TARGET=ROOT.parent/'SRWOGS_EX_K_TEST.ISO'

def loadarc(f,slot):
 a=json.loads((OUT/f'MAP.BIN.{slot}.json').read_text(encoding='utf8'))
 result=[]
 for e in a['entries']:
  off,size=struct.unpack('<II',read(f,a['directory']+8+e['index']*8,8));result.append((e['keys'],a['directory']+off,size))
 return a,result

def strings(b):
 count=u32(b,80);table=u32(b,68);pool=u32(b,76);base=u32(b,64)
 return {base+i:decode(b[pool+u32(b,table+i*4):b.index(0,pool+u32(b,table+i*4))]) for i in range(count)}

def main():
 result={};dest=OUT/'story_layout';dest.mkdir(exist_ok=True)
 with TARGET.open('rb') as f:
  _,es=loadarc(f,14)
  for keys,at,size in es:
   if not any(k>=2000 for k in keys):continue
   b=read(f,at,size);ss=strings(b);n=u32(b,40);co=u32(b,44);rows=[list(struct.unpack_from('<24I',b,co+i*96)) for i in range(n)]
   result[str(keys[0])]=dict(keys=keys,offset=at,size=size,commands=n,prefix=u32(b,32),main=n-u32(b,32),strings=ss,events=[list(struct.unpack_from('<4I',b,u32(b,52)+i*16)) for i in range(u32(b,48))],head=rows[:45],tail=rows[-40:],opcodes=dict(Counter(r[0] for r in rows)))
   text=[]
   for i,r in enumerate(rows):
    text.append(f'{i}: '+' '.join('_' if v==0xdeaddead else f'{v:X}' for v in r)+' | '+' | '.join(f'{j}:{ss[v]}' for j,v in enumerate(r[2:8],2) if v in ss))
   (dest/f'{keys[0]}.txt').write_text('\n'.join(text),encoding='utf8')
   (dest/f'{keys[0]}.bin').write_bytes(b)
   print(keys[0],n,'prefix',u32(b,32),'str',list(ss.items())[:4],'end',[hex(r[0]) for r in rows[-14:]])
 (OUT/'story_layout.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 m=getmaster(TARGET);p=m.tables['Stag'][0];print('STAG HEAD',m.b[p:p+160].hex(' '))

if __name__=='__main__':main()
