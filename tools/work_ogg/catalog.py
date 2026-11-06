from inspect_resources import *
def u16(b,p=0):return struct.unpack_from('<H',b,p)[0]
class Master:
 def __init__(self,b):
  self.b=b;self.tables={}
  for k in range(0x18,0x8c,4):
   at=u32(b,k);tag=b[at:at+4].decode('ascii');self.tables[tag]=(at,u32(b,at+4),u32(b,at+8))
 def text(self,n):
  at,_,count=self.tables['Strg'];assert n<count
  p=at+u32(self.b,at+12+n*4)
  return decode(self.b[p:self.b.index(b'\0',p)])
 def rows(self,tag):
  at,size,count=self.tables[tag]
  nxt=min([x[0] for x in self.tables.values() if x[0]>at]+[len(self.b)])
  stride=(nxt-at-12)//count
  assert (nxt-at-12)%count==0,(tag,nxt-at-12,count)
  return [(i,at+12+i*stride,self.b[at+12+i*stride:at+12+(i+1)*stride]) for i in range(count)]
def main():
 b=(OUT/'SHARED.BIN.master').read_bytes();m=Master(b)
 for tag,t in m.tables.items():print(tag,hex(t[0]),hex(t[1]),t[2])
 print('TEXT SAMPLE',[(i,m.text(i)) for i in range(10)])
 for tag in ['Unit','Plot','Weap']:
  rows=m.rows(tag);print('ROWS',tag,len(rows),len(rows[0][2]))
  for i,p,r in rows[:3]:print(i,hex(p),r.hex(' '))
 out={}
 for tag in ['Unit','Plot']:
  keytag='UTbl' if tag=='Unit' else 'PTbl';k,_,n=m.tables[keytag]
  lookup=struct.unpack_from('<%dH'%n,b,k+12)
  out[tag]=[]
  for i,p,r in m.rows(tag):
   ns=u16(r,12) if tag=='Unit' else u16(r,4)
   item=dict(index=i,offset=p,keys=[j for j,v in enumerate(lookup) if v==i],name_id=ns,name=m.text(ns),hex=r.hex())
   out[tag].append(item)
   if any(x in item['name'] for x in ['그랑존','잉그램','다크','알카이드','리바레','쥬데','발시온','슈우','미자르','알티스','마그나','메이시스']):print('BOSS',tag,item)
 (OUT/'catalog.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
