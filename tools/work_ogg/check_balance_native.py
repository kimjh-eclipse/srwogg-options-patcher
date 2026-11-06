"""Execute actual OGG scalar accessors offline against the prospective master."""
from apply_balance_25 import *
from probe_native import elfmem
from r5900_scalar_check import CPU
import numpy as np

def main():
 state=json.loads(STATE.read_text(encoding='utf8'));target=Path(state['canonical_iso'])
 balance=json.loads(BALANCE.read_text(encoding='utf8'));cast={r['pilot_name']:r for r in json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast']}
 edits,notes,_=plan(target,balance['units'],cast)
 old=elfmem(ROOT.parent/'슈퍼 로봇 대전 OG (K).iso');new=(OUT/'terrain_fresh_ram.bin').read_bytes();a=np.frombuffer(new,dtype='<u4');start=0x100000//4;end=0x500000//4
 fns={'hp':0x1a7d40,'en':0x1a7cc0,'armor':0x1a7b40,'move':0x1a7c40,'mobility':0x1a7bc0,'power':0x1a5dc0,'ability':0x1a6f00,'motion':0x1a4a20}
 mapping={}
 for name,pc in fns.items():
  if name=='ability':
   # OGG replaces OGs' gp-based clamp with an inline 0..5 clamp.
   assert u32(new,0x276178)==0x28c10006 and u32(new,0x2761f0)==0x90420057
   mapping[name]=0x276150;continue
  w=np.frombuffer(old[pc:pc+128],dtype='<u4');mask=np.array([0xffff0000 if x>>26 else 0xffffffff for x in w],dtype=np.uint32);score=np.zeros(end-start,dtype=np.uint16)
  exact=np.zeros(end-start,dtype=np.uint16)
  for j,x in enumerate(w):
   v=a[start+j:end+j];score+=((v&mask[j])==(x&mask[j]));exact+=(v==x)
  rank=score.astype(np.uint32)*64+exact;best=int(np.argmax(rank));rank[best]=0;second=int(np.argmax(rank));address=(best+start)*4
  assert score[best]>=25,(name,int(score[best]))
  assert int(score[best])*64+int(exact[best])>int(rank[second]),('ambiguous function',name)
  mapping[name]=address
  print(name,hex(address),int(score[best]),int(exact[best]),flush=True)
 results={}
 for offset,original,b,label in edits:
  cpu=CPU(new);master=0x1800000;data=0x1900000;cpu.mem[data:data+len(b)]=b
  for i,field in enumerate(range(0x18,0x8c,4)):
   at=data+u32(b,field)
   for rel,value in [(0,at),(4,cpu.read(at,4)),(8,cpu.read(at+4,4)),(12,cpu.read(at+8,4)),(16,at),(20,at+12)]:cpu.write(master+0x28+i*24+rel,value,4)
  count=0
  for n in notes[label.split()[0]]:
   for field in ['hp','en','armor','move','mobility']:
    got=cpu.run(mapping[field],[master,n['key']]);assert got==n['stats'][field],(n['name'],field,got,n['stats'][field]);count+=1
   for i in range(6):
    got=cpu.run(mapping['ability'],[master,n['key'],i]);assert got==(n['abilities']+[0]*6)[i],(n['name'],'ability',i,got);count+=1
   for w in n['weapons']:
    assert cpu.run(mapping['power'],[master,w['new_key']])==w['power'];count+=1
    assert cpu.run(mapping['motion'],[master,w['new_key']])==cpu.run(mapping['motion'],[master,w['original_key']]);count+=1
  results[label]=count
 report=dict(actual_ogg_functions={k:hex(v) for k,v in mapping.items()},native_accessor_checks=results,passed=True,live_playthrough=False)
 (ROOT/'balance_25_native_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
