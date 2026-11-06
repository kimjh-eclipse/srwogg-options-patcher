from catalog import *
def getmaster(path):
 with path.open('rb') as f:
  e=next(x for x in inventory(f) if x['name']=='SHARED.BIN;1');a=lice(f,e['offset'],e['size']);e=a['entries'][3];a=lice(f,e['offset'],e['size']);e=a['entries'][0];return Master(read(f,e['offset'],e['size']))
def units(m):
 a,_,n=m.tables['UTbl'];lookup=struct.unpack_from('<%dH'%n,m.b,a+12)
 return [dict(index=i,name=m.text(u16(r,12)),keys=[k for k,v in enumerate(lookup) if v==i],bank=u16(r,0x44),weapons=[w for w in struct.unpack_from('<16H',r,0x24) if w!=65535],raw=r.hex()) for i,p,r in m.rows('Unit')]
def main():
 old=units(getmaster(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso'));new=units(getmaster(SOURCE));byname={}
 for r in new:byname.setdefault(r['name'],[]).append(r)
 oldbank={r['bank'] for r in old};newbank={r['bank'] for r in new}
 missing=[r for r in old if r['name'] not in byname];names=set(r['name'] for r in old);common=names & set(byname)
 print('Unit rows',len(old),len(new),'unique names',len(names),len(byname),'common',len(common),'missing',len(names-common));print('MISSING',[(r['index'],r['name'],r['bank']) for r in missing]);print('old banks absent new tables',sorted(oldbank-newbank))
 bodies=json.loads((OUT/'BATTLE.BIN.1.json').read_text());available={k for e in bodies['entries'] if e['size']>0 for k in e['keys']}
 print('OGs body banks missing from OGG archive',sorted(oldbank-available));print('EXAMPLES',[(r['name'],r['keys'],r['bank']) for r in new if any(s in r['name'] for s in ['리바레','쥬데','발시온','그레','디카','츠바','슬레이'])])
 report=dict(ogs_count=len(old),ogg_count=len(new),ogs_unique_names=len(names),ogg_unique_names=len(byname),matching_names=len(common),missing_names=sorted(names-common),missing_ogs_body_banks=sorted(oldbank-available),ogs=old,ogg=new)
 (OUT/'ogs_ogg_unit_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
