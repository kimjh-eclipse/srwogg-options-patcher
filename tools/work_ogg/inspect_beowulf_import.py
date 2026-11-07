"""Read-only compatibility audit for the user's OGs Beowulf assets."""
from pathlib import Path
import sys,json,struct,collections
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/('option_density' if (ROOT/'option_density').exists() else 'option_release')),str(ROOT),str(ROOT.parent/'work_ogs')]
from inspect_iso import inventory,lice,read,u32
from catalog import Master,u16
from build_options import rawmaster
from audit_story_layout import TARGET,loadarc
from beowulf_source_image import OGsBeowulfImage

def main():
 result={}
 for label in ['OGG','OGs']:
  with (TARGET.open('rb') if label=='OGG' else OGsBeowulfImage()) as f:
   files=inventory(f);item={};result[label]=item
   for ar in ['BATTLE.BIN','GRAPHIC.BIN','SHARED.BIN']:
    e=next(e for e in files if e['name']==ar+';1');a=lice(f,e['offset'],e['size']);entries=[]
    for x in a['entries']:
     child=lice(f,x['offset'],x['size']) if read(f,x['offset'],4)==b'LICE' else None
     entries.append(dict(index=x['index'],offset=x['offset'],size=x['size'],head=read(f,x['offset'],12).hex(),count=child['count'] if child else None,slots=child['slots'] if child else None))
    item[ar]=dict(offset=e['offset'],size=e['size'],entries=entries)
   if label=='OGG':_,m=rawmaster(f,'SHARED.BIN')
   else:
    e=next(e for e in files if e['name']=='SHARED.BIN;1');m=Master(read(f,e['offset']+0x11e800,0x190000-0x11e800))
   def rows(table,lookup,stride):
    keys=collections.defaultdict(list);p=m.tables[lookup][0]
    for k in range(m.tables[lookup][2]):
     ix=u16(m.b,p+12+k*2)
     if ix!=65535:keys[ix].append(k)
    return [(i,m.b[m.tables[table][0]+12+i*stride:m.tables[table][0]+12+(i+1)*stride],keys[i]) for i in range(m.tables[table][2])]
   hits=[]
   for i,r,keys in rows('Unit','UTbl',100):
    name=m.text(u16(r,12))
    if any(t in name.replace('　','') for t in ['아인스트','게슈펜스트','베오울프','페르제','글리트','게뮤트','레지세이아']):hits.append(dict(record=i,keys=keys,name=name,hp=u32(r),bank=u16(r,0x44),map_model=u16(r,0x46),row=r.hex()))
   item['units']=hits;item['tables']={k:[v[1],v[2]] for k,v in m.tables.items()}
   if label=='OGs':
    p=m.tables['PTbl'][0];ix=u16(m.b,p+12+0x603*2);r=m.b[m.tables['Plot'][0]+12+ix*148:m.tables['Plot'][0]+12+(ix+1)*148];item['beowulf_pilot']=dict(record=ix,name=m.text(u16(r,4)),face=u16(r,0x48),row=r.hex())
 (ROOT/'beowulf_import_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 for label,item in result.items():
  print(label)
  for name in ['BATTLE.BIN','GRAPHIC.BIN']:
   print(name,hex(item[name]['offset']),item[name]['size'])
   for e in item[name]['entries']:print(e['index'],hex(e['offset']),e['size'],e['head'][:8],e['count'],e['slots'])
  print('Units:',[{k:v for k,v in r.items() if k!='row'} for r in item['units']])
  if 'beowulf_pilot' in item:print('Pilot:',{k:v for k,v in item['beowulf_pilot'].items() if k!='row'})
if __name__=='__main__':main()
