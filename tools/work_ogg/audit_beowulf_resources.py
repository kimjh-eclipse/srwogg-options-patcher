from inspect_beowulf_import import *

def archive(f,name):
 e=next(e for e in inventory(f) if e['name']==name+';1');return e,lice(f,e['offset'],e['size'])
def children(f,root):return {i:lice(f,x['offset'],x['size']) for i,x in enumerate(root['entries'])}
def entry(a,k):return a['entries'][k] if not a['slots'] else next(x for x in a['entries'] if k in x['keys'])
def data(f,a,k):e=entry(a,k);return read(f,e['offset'],e['size'])

def main():
 with OGsBeowulfImage() as s,TARGET.open('rb') as t:
  se,sr=archive(s,'BATTLE.BIN');te,tr=archive(t,'BATTLE.BIN');ss=children(s,sr);tt=children(t,tr)
  row=data(s,ss[7],0)[227*144:228*144];aks=sorted(set(struct.unpack_from('<70H',row,4))-{65535});cks=sorted(set(struct.unpack_from('<20H',data(s,ss[9],0),223*60))-{65535})
  print('Transfer body',len(data(s,ss[1],227)),'attacks',len(aks),sum(len(data(s,ss[2],k)) for k in aks),'cutins',len(cks),sum(len(data(s,ss[3],k)) for k in cks))
  print('Battle tail',te['offset']+te['size']-max(x['offset']+x['size'] for x in tr['entries']))
  for i in [1,2,3,5]:
   a=tt[i];print('Archive',i,'first payload gap',min(x['offset'] for x in a['entries'])-(a['directory']+8+a['count']*8),'mapping slack',a['directory']-a['offset']-16-a['slots']*2)
  print('free body keys',sorted(set(range(tt[1]['slots']))-{k for x in tt[1]['entries'] for k in x['keys']}));print('metadata',[len(data(t,tt[i],0)) for i in [7,8,9]])
  _,gm=archive(t,'GRAPHIC.BIN');ga={i:lice(t,x['offset'],x['size']) for i,x in enumerate(gm['entries']) if i in [1,2,4]}
  used={i:{k for x in ga[i]['entries'] for k in x['keys']} for i in [1,2]}
  print('free face groups',[k for k in range(200,249) if all(not any(x in used[i] for x in range(k*mult,(k+1)*mult)) for i,mult in [(1,32),(2,10)])])
  _,m=rawmaster(t,'SHARED.BIN');units=[]
  for k in range(1024,1450):
   ix=u16(m.b,m.tables['UTbl'][0]+12+k*2)
   if ix==65535:continue
   r=m.b[m.tables['Unit'][0]+12+ix*100:m.tables['Unit'][0]+12+(ix+1)*100];name=m.text(u16(r,12))
   if any(z in name for z in ['아인','페르','게뮤','그리트','크노','글리트','게가','아룬']):units.append((k,name,u32(r),u16(r,0x44)))
  print('Einst',units)
if __name__=='__main__':main()
