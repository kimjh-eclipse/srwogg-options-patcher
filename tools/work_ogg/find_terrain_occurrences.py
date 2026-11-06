from catalog import *
def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf-8'));path=Path(state['canonical_iso']);needle='荒野'.encode('cp932');hits=[];position=0;tail=b''
 with path.open('rb') as f:
  files=inventory(f);f.seek(0)
  while chunk:=f.read(16<<20):
   b=tail+chunk;base=position-len(tail);q=0
   while (q:=b.find(needle,q))>=0:
    off=base+q
    if not hits or hits[-1]['offset']!=off:
     e=next((x for x in files if not x['directory'] and x['offset']<=off<x['offset']+x['size']),{})
     hits.append(dict(offset=off,file=e.get('path'),context=b[max(0,q-20):q+90].hex()))
    q+=len(needle)
   position+=len(chunk);tail=b[-128:]
 print(json.dumps(hits,ensure_ascii=False,indent=2))
 (OUT/'terrain_remaining_raw_occurrences.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
