from inspect_resources import *
def texts(b):
 h=struct.unpack_from('<16H',b)
 # Speaker/text-offset tables are padded to 4 bytes for odd row counts.
 # Their padded length must not invent a final voice ID in the string pool.
 n=min((h[13]-h[12])//2,(h[14]-h[13])//2,(h[15]-h[14])//4)
 out=[]
 for i in range(n):
  p=h[15]+struct.unpack_from('<H',b,h[13]+i*2)[0]
  raw=b[p:b.index(0,p)]
  out.append(dict(index=i,speaker=struct.unpack_from('<H',b,h[12]+i*2)[0],voice=u32(b,h[14]+i*4),raw=raw.hex(),jp=raw.decode('cp932',errors='replace'),kr=decode(raw)))
 return out
def main():
 results={}
 for label,path in [('ogg',SOURCE),('ogs',ROOT.parent/'슈퍼 로봇 대전 OG (K).iso')]:
  with path.open('rb') as f:
   files=inventory(f);e=next(x for x in files if x['name']=='BATTLE.BIN;1');a=lice(f,e['offset'],e['size']);v=a['entries'][5];a=lice(f,v['offset'],v['size']);e=next(x for x in a['entries'] if 62 in x['keys']);b=read(f,e['offset'],e['size'])
  (OUT/(label+'_ingram.bin')).write_bytes(b);results[label]=texts(b)
  print(label,len(results[label]),'unique',len(set(r['raw'] for r in results[label])))
  for r in results[label][:8]:print(r['index'],r['voice'],r['jp'] if label=='ogg' else r['kr'])
 (OUT/'ingram_text_compare.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 ogs={r['voice']:r for r in results['ogs']}
 matches=sum(r['voice'] in ogs for r in results['ogg']);print('voice matches',matches)
 for r in results['ogg']:
  if '時間' in r['jp']:print('SCREENSHOT',r,'OGS',ogs.get(r['voice']))
if __name__=='__main__':main()
