from inspect_resources import *
def main():
 with SOURCE.open('rb') as f:
  for name in ['SHARED.BIN','IM.BIN']:
   e=json.loads((OUT/f'{name}.3.json').read_text())['entries'][0];b=read(f,e['offset'],e['size']);(OUT/(name+'.master')).write_bytes(b)
   h=0x10;print(name,hex(e['offset']),b[:0xa0].hex(' '))
   for k in range(0x18,0x8c,4):
    at=h+u32(b,h+k);print(hex(k),hex(at),b[at:at+20].hex(' '))
  for ar in (13,14):
   a=json.loads((OUT/f'MAP.BIN.{ar}.json').read_text())
   print('MAP',ar)
   for e in a['entries']:
    b=read(f,e['offset'],min(e['size'],128))
    print(e['index'],e['keys'],hex(e['offset']),e['size'],b[:44].hex(' '))
if __name__=='__main__':main()
