from catalog import *
from collections import Counter
def main():
 b=(OUT/'script_2001.bin').read_bytes();co=u32(b,44);count=u32(b,40)
 lines=[]
 def string(k):
  if k>=u32(b,64)+u32(b,80):return ''
  p=u32(b,76)+u32(b,u32(b,68)+k*4)
  return decode(b[p:b.find(b'\0',p)])
 for i in range(count):
  r=struct.unpack_from('<24I',b,co+i*96)
  vals=' '.join(hex(x) if x!=0xdeaddead else '_' for x in r)
  texts=' | '.join(f'{k}:{string(r[k])}' for k in [2] if string(r[k]))
  lines.append(f'{i}: {vals} {texts}')
 (OUT/'scenario_2001.txt').write_text('\n'.join(lines),encoding='utf-8')
 print('\n'.join(lines[:25]));print('\n'.join(lines[-40:]));print(Counter(u32(b,co+i*96) for i in range(count)))
 with SOURCE.open('rb') as f:
  inv=json.loads((OUT/'iso_inventory.json').read_text(encoding='utf-8'))
  for e in inv['files']:
   if e['path'].startswith('/OL/'):(OUT/e['name'].split(';')[0]).write_bytes(read(f,e['offset'],e['size']))
if __name__=='__main__':main()
