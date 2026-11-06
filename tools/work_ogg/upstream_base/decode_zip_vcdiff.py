"""RFC3284 default-table decoder with a bounded forward ZIP source window.

Consumes xdelta3's uncompressed recode, checking every target Adler32. Only
changed 4K pages are saved; neither Japanese nor Korean full ISOs are created.
"""
from pathlib import Path
import io,struct,zipfile,zlib,hashlib,base64,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def integer(f):
 v=0
 for _ in range(10):
  b=f.read(1);assert b,'truncated integer';v=(v<<7)|(b[0]&127)
  if not b[0]&128:return v
 raise ValueError('oversized integer')

def table():
 t=[[(2,0,0)]]+[[ (1,n,0)] for n in range(18)]
 for mode in range(9):
  for n in [0,*range(4,19)]:t.append([(3,n,mode)])
 for mode in range(6):
  for a in range(1,5):
   for c in range(4,7):t.append([(1,a,0),(3,c,mode)])
 for mode in range(6,9):
  for a in range(1,5):t.append([(1,a,0),(3,4,mode)])
 for mode in range(9):t.append([(3,4,mode),(1,1,0)])
 assert len(t)==256;return t

def decode_window(source,target_size,data,inst,addr):
 t=table();out=bytearray();di=0;ins=io.BytesIO(inst);ad=io.BytesIO(addr);near=[0]*4;same=[0]*768;next_slot=0
 while ins.tell()<len(inst):
  code=ins.read(1)[0]
  for kind,n,mode in t[code]:
   if not n:n=integer(ins)
   if kind==1:out.extend(data[di:di+n]);di+=n
   elif kind==2:out.extend(bytes([data[di]])*n);di+=1
   else:
    if mode==0:at=integer(ad)
    elif mode==1:at=len(source)+len(out)-integer(ad)
    elif mode<6:at=near[mode-2]+integer(ad)
    else:at=same[(mode-6)*256+ad.read(1)[0]]
    near[next_slot]=at;next_slot=(next_slot+1)%4;same[at%768]=at
    while n:
     if at<len(source):part=source[at:min(at+n,len(source))]
     else:
      at_target=at-len(source);assert 0<=at_target<len(out)
      part=out[at_target:min(at_target+n,len(out))]
     assert len(part)>0;out.extend(part);at+=len(part);n-=len(part)
   assert len(out)<=target_size
 assert len(out)==target_size and di==len(data) and ad.tell()==len(addr)
 return bytes(out)

def main():
 archive=Path.home()/'Downloads/Super Robot Taisen OG Gaiden (Japan Korea).zip'
 source_md5=hashlib.md5();sha=hashlib.sha256();md5=hashlib.md5();position=0;changes=[];windows=0
 with zipfile.ZipFile(archive) as z,z.open(z.infolist()[0]) as jp,(ROOT/'SRWOGS_EX_K.ISO').open('rb') as old,(HERE/'official_uncompressed.vcdiff').open('rb') as patch:
  assert patch.read(4)==b'\xd6\xc3\xc4\0';flags=patch.read(1)[0];assert flags&3==0
  if flags&4:patch.read(integer(patch))
  start=0;buffer=bytearray()
  while indicator:=patch.read(1):
   flag=indicator[0];assert flag in [1,5]
   source_size=integer(patch);source_at=integer(patch);delta_size=integer(patch);delta_end=patch.tell()+delta_size
   target_size=integer(patch);assert patch.read(1)==b'\0'
   dn=integer(patch);insn=integer(patch);an=integer(patch)
   checksum=struct.unpack('>I',patch.read(4))[0] if flag&4 else None
   data=patch.read(dn);inst=patch.read(insn);addr=patch.read(an);assert patch.tell()==delta_end
   assert source_at>=start and source_size<=128<<20
   skip=source_at-start
   if skip<=len(buffer):del buffer[:skip]
   else:
    remaining=skip-len(buffer);buffer.clear()
    while remaining:
     b=jp.read(min(8<<20,remaining));assert b;source_md5.update(b);remaining-=len(b)
   start=source_at
   if len(buffer)<source_size:
    b=jp.read(source_size-len(buffer));assert len(b)==source_size-len(buffer);source_md5.update(b);buffer.extend(b)
   result=decode_window(memoryview(buffer)[:source_size],target_size,data,inst,addr)
   assert checksum is not None and zlib.adler32(result)&0xffffffff==checksum,('checksum',windows)
   previous=old.read(len(result));assert len(previous)==len(result);sha.update(result);md5.update(result)
   if previous!=result:
    for at in range(0,len(result),4096):
     a=previous[at:at+4096];b=result[at:at+4096]
     if a!=b:changes.append({'offset':position+at,'before':base64.b64encode(zlib.compress(a)).decode(),'after':base64.b64encode(zlib.compress(b)).decode(),'length':len(b)})
   position+=len(result);windows+=1
   if windows%100==0:print('Verified upstream windows:',windows,flush=True)
  while b:=jp.read(8<<20):source_md5.update(b)
 assert source_md5.hexdigest()=='cb7dc4485f46f220c46095c966a3aad0'
 assert windows==557 and position==4666294272
 result={'passed':True,'official_repository':'https://github.com/z3oo3z/PS2-SRWOGG-KPatch','release':'SRWOGG','version':'1.4.3s','source_md5':source_md5.hexdigest(),'base_sha256':sha.hexdigest(),'base_md5':md5.hexdigest(),'bytes':position,'xdelta_target_checksums_verified':True,'verified_windows':windows,'changed_pages_from_previous_base':len(changes),'changes':changes,'extra_full_ISOs_created':0}
 (HERE/'official_base_delta.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='changes'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
