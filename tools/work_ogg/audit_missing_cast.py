from compare_ogs_units import getmaster
from catalog import *

def cast(m,tag):
 a,_,n=m.tables['UTbl' if tag=='Unit' else 'PTbl'];look=struct.unpack_from('<%dH'%n,m.b,a+12)
 rs=m.rows(tag);bykey={}
 for key,idx in enumerate(look):
  if idx==65535:continue
  _,p,r=rs[idx];bykey[key]=dict(key=key,index=idx,name=m.text(u16(r,12 if tag=='Unit' else 4)),raw=r.hex())
 return bykey
def scan(path,isogg):
 m=getmaster(path);units=cast(m,'Unit');pilots=cast(m,'Plot');pairs=[]
 with path.open('rb') as f:
  e=next(x for x in inventory(f) if x['name']=='MAP.BIN;1');root=lice(f,e['offset'],e['size']);e=root['entries'][13];a=lice(f,e['offset'],e['size'])
  for e in a['entries']:
   if isogg and not any(2001<=k<=2034 or 2050<=k<=2056 for k in e['keys']):continue
   b=read(f,e['offset'],e['size'])
   if b[:4]!=b'UNTD' or len(b)!=44+u32(b,40)*336:continue
   for i in range(u32(b,40)):
    r=b[44+i*336:44+(i+1)*336];u,p=u32(r),u32(r,32)
    if u not in units or p not in pilots:continue
    pairs.append(dict(stage=e['keys'],row=i,unit=u,pilot=p,unit_name=units[u]['name'],pilot_name=pilots[p]['name'],faction=u32(r,8),data=r.hex()))
 return m,units,pilots,pairs
def main():
 _,ou,op,old=scan(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso',False);_,nu,np,new=scan(SOURCE,True)
 us={r['unit_name'] for r in new};ps={r['pilot_name'] for r in new}
 seen=set();missing=[]
 for r in old:
  key=(r['unit_name'],r['pilot_name'])
  if key in seen:continue
  seen.add(key)
  if r['unit_name'] not in us or r['pilot_name'] not in ps:
   missing.append(dict(**r,missing_unit=r['unit_name'] not in us,missing_pilot=r['pilot_name'] not in ps,unit_available=r['unit'] in nu,pilot_available=r['pilot'] in np))
 result=dict(missing=missing,ogg_story_unit_names=sorted(us),ogg_story_pilot_names=sorted(ps),ogs_units=ou,ogs_pilots=op,ogg_units=nu,ogg_pilots=np)
 (OUT/'missing_cast.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('OGG story names units/pilots',len(us),len(ps),'Missing pairs',len(missing))
 for i,r in enumerate(missing):print(i,hex(r['unit']),hex(r['pilot']),r['unit_name'],r['pilot_name'],'missing',r['missing_unit'],r['missing_pilot'],'available',r['unit_available'],r['pilot_available'])
if __name__=='__main__':main()
