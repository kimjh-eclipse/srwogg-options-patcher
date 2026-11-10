"""OG Gaiden chapter-one cast showcase; original ISO is read-only."""
from build_patch import Plan,put,arc,insert_commands,command,EXPECTED
from catalog import *
from localize_ingram import localize
from explanation_tables import table_records, pack_explanations
import shutil,os

def compact(table):
 if table[:4]==b'Expl':return bytearray(pack_explanations(table_records(table)))
 assert table[:4] in [b'Strg',b'Sent'],'Binary tables cannot be compacted as NUL strings'
 n=u32(table,8);values=[]
 for i in range(n):
  at=u32(table,12+i*4);values.append(bytes(table[at:table.index(0,at)+1]))
 pool=bytearray();where={}
 for v in sorted(set(values),key=lambda s:(-len(s),s)):
  q=pool.find(v)
  if q<0:q=len(pool);pool.extend(v)
  where[v]=q
 prefix=12+n*4
 b=bytearray(table[:4]+struct.pack('<II',prefix+len(pool),n))+bytearray(struct.pack('<%dI'%n,*[prefix+where[v] for v in values]))+pool
 b.extend(bytes((-len(b))%4))
 for i,v in enumerate(values):
  at=u32(b,12+i*4);assert b[at:b.index(0,at)+1]==v
 return b

def prepare():
 report=json.loads((OUT/'missing_cast.json').read_text(encoding='utf-8'))
 rows=json.loads((OUT/'chosen_cast.json').read_text(encoding='utf-8'))
 # Dummy unit zero is a scenario placeholder. Use Sean's normal vessel.
 units=report['ogg_units'];ship=next(int(k) for k,v in units.items() if v['name']=='히류개')
 for i,r in enumerate(rows):
  r['new_key']=0x700+i
  if r['unit_name']=='ダミー':r['unit']=ship;r['unit_name']=units[str(ship)]['name'];r['replacement_reason']='Scenario-only dummy replaced with Sean vessel'
  assert str(r['unit']) in units and str(r['pilot']) in report['ogg_pilots']
 return report,rows

def patch_master(old,rows):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields]
 parts={k:bytearray(old[p:(starts[i+1] if i+1<len(starts) else len(old))]) for i,(k,p) in enumerate(zip(fields,starts))}
 # IM's otherwise unused legacy names are Japanese. Add Korean names for the
 # clones without changing any existing string ID or original record.
 st=parts[0x80];sn=u32(st,8);values=[]
 for i in range(sn):
  q=u32(st,12+i*4);values.append(bytes(st[q:st.index(0,q)+1]))
 ids={v:i for i,v in enumerate(values)};name_ids={}
 for r in rows:
  for field in ['unit','pilot']:
   raw=encode(r[field+'_name'])+b'\0'
   if raw not in ids:ids[raw]=len(values);values.append(raw)
   name_ids[(r['new_key'],field)]=ids[raw]
 prefix=12+len(values)*4;pool=bytearray();offsets=[]
 for value in values:offsets.append(prefix+len(pool));pool.extend(value)
 parts[0x80]=bytearray(b'Strg'+struct.pack('<II',prefix+len(pool),len(values))+struct.pack('<%dI'%len(values),*offsets))+pool
 for table,lookup,stride,field in [(0x1c,0x18,100,'unit'),(0x2c,0x28,148,'pilot')]:
  t,l=parts[table],parts[lookup];count=u32(t,8)
  for i,r in enumerate(rows):
   src=u16(l,12+r[field]*2);assert src<count and u16(l,12+r['new_key']*2)==65535
   rec=bytearray(t[12+src*stride:12+(src+1)*stride])
   struct.pack_into('<H',rec,12 if field=='unit' else 4,name_ids[(r['new_key'],field)])
   if field=='unit':struct.pack_into('<H',rec,0x22,1)
   else:
    # Permit all clone pilots to board their showcase units.
    struct.pack_into('<H',rec,0x12,65535)
   t.extend(rec);struct.pack_into('<H',l,12+r['new_key']*2,count+i)
  put(t,4,u32(t,4)+len(rows)*stride);put(t,8,count+len(rows));put(l,4,u32(l,4)+len(rows)*stride)
 for k in (0x80,0x84,0x88):parts[k]=compact(parts[k])
 # Match the SP1 option in the preceding test build.
 t=parts[0x2c]
 for i in range(u32(t,8)):
  for rel in (*range(0x72,0x78),0x7f):
   if t[12+i*148+rel]>0:t[12+i*148+rel]=1
 new=bytearray(old[:starts[0]])
 for k in fields:put(new,k,len(new));new.extend(parts[k])
 assert len(new)<=len(old),('master capacity',len(new),len(old));new.extend(bytes(len(old)-len(new)))
 nm=Master(new)
 for tag,stride in [('Unit',100),('Weap',36),('Plot',148)]:
  a,_,n=m.tables[tag];b=nm.tables[tag][0]
  for i in range(n):
   allowed=set([*range(0x72,0x78),0x7f]) if tag=='Plot' else set()
   assert {j for j in range(stride) if old[a+12+i*stride+j]!=new[b+12+i*stride+j]}<=allowed
 for tag in ['Strg','Expl','Sent']:
  a,size,n=m.tables[tag];b,ns,_=nm.tables[tag]
  assert table_records(old[a:a+size])==table_records(new[b:b+ns])
 for r in rows:
  for tag,keytag,stride,field in [('Unit','UTbl',100,'unit'),('Plot','PTbl',148,'pilot')]:
   idx=u16(new,nm.tables[keytag][0]+12+r['new_key']*2);assert idx>=m.tables[tag][2]
   original_idx=u16(old,m.tables[keytag][0]+12+r[field]*2)
   a=m.tables[tag][0]+12+original_idx*stride;b=nm.tables[tag][0]+12+idx*stride
   assert nm.text(u16(new,b+(12 if tag=='Unit' else 4)))==r[field+'_name']
 return bytes(new)

def voice_clone(blob,source,key,silent=False):
 h=struct.unpack_from('<16H',blob);b=bytearray(blob)
 if source==62:b,_,_=localize(blob);b=bytearray(b)
 # Native banks may use an equivalent raw pilot key in the speaker selectors.
 tags=[u16(b,o)&0x7ff for o in range(h[12],h[13],2)]
 own=source if source in tags else max(set(tags),key=tags.count)
 for o in range(h[12],h[13],2):
  v=u16(b,o)
  if v&0x7ff==own:struct.pack_into('<H',b,o,(v&0xf800)|key)
 if silent:
  n=(h[13]-h[12])//2
  for i in range(n):struct.pack_into('<H',b,h[13]+i*2,0);put(b,h[14]+i*4,0)
  b=b[:h[15]]+encode('「……」')+b'\0'
 else:assert b[h[14]:h[15]]==blob[h[14]:h[15]],'Voice IDs changed'
 return bytes(b)

def make_plan(f,rows):
 p=Plan(f)
 for name in ['SHARED.BIN','IM.BIN']:
  a=arc(name+'.3');e=a['entries'][0];p.add(e['offset'],patch_master(read(f,e['offset'],e['size']),rows),name+' independent showcase cast')
 root=arc('BATTLE.BIN');a=arc('BATTLE.BIN.5');mapping=list(struct.unpack('<%dH'%a['slots'],read(f,a['offset']+16,a['slots']*2)));entries=[(e['offset'],e['size']) for e in a['entries']];cursor=0x99000000
 keys={k:e for e in a['entries'] for k in e['keys']}
 for r in rows:
  silent=r['pilot'] not in keys;e=keys[15 if silent else r['pilot']];blob=read(f,e['offset'],e['size']);b=voice_clone(blob,15 if silent else r['pilot'],r['new_key'],silent)
  cursor=(cursor+2047)//2048*2048;p.empty(cursor,b,'voice clone '+r['pilot_name']);r['silent']=silent
  while len(mapping)<=r['new_key']:mapping.append(65535)
  assert mapping[r['new_key']]==65535;mapping[r['new_key']]=len(entries);entries.append((cursor,len(b)));cursor+=len(b)
 assert cursor<0x9a4d4000
 assert 16+len(mapping)*2<=a['directory']-a['offset']
 d=b'Wpbb'+struct.pack('<I',len(entries))+b''.join(struct.pack('<II',at-a['directory'],n) for at,n in entries)
 assert a['directory']+len(d)<=min(at for at,n in entries)
 p.add(a['offset']+8,struct.pack('<II',len(entries),len(mapping)),'voice counts');p.add(a['offset']+16,struct.pack('<%dH'%len(mapping),*mapping),'voice key map');p.add(a['directory'],d,'voice directory')
 p.add(root['directory']+8+5*8+4,struct.pack('<I',cursor-a['offset']),'voice span')
 # All additional units use one native deployment group, with unique coordinates.
 a=arc('MAP.BIN.13');e=next(e for e in a['entries'] if 2001 in e['keys']);old=read(f,e['offset'],e['size']);count=u32(old,40);template=old[44+6*336:44+7*336];new=bytearray(old)
 occupied={(u32(old,44+i*336+16),u32(old,44+i*336+20)) for i in range(count)}
 positions=[(x,y) for y in range(22,32) for x in range(2,23) if (x,y) not in occupied]
 assert len(rows)<=len(positions) and len(rows)+3<=128 and len(rows)+3<=192
 for r,xy in zip(rows,positions):
  row=bytearray(template);k=r['new_key'];r['position']=xy
  for off,value in [(0,k),(4,32),(8,0),(16,xy[0]),(20,xy[1]),(28,1),(32,k),(0x38,0),(0x3c,0),(0x40,0)]:put(row,off,value)
  for off in (0x60,0x74,0x88):put(row,off,0xffff0000|k)
  new.extend(row)
 put(new,40,count+len(rows));dest=0x1b000000;p.empty(dest,new,'chapter one cast placements');p.add(a['directory']+8+e['index']*8,struct.pack('<II',dest-a['directory'],len(new)),'placement entry')
 root=arc('MAP.BIN');p.add(root['directory']+8+13*8+4,struct.pack('<I',dest+len(new)-a['offset']),'placement span')
 a=arc('MAP.BIN.14');e=next(e for e in a['entries'] if 2001 in e['keys']);old=read(f,e['offset'],e['size']);new=insert_commands(old,26,[command(0xca,32,0xffffffff)]);dest=0x1b020000;p.empty(dest,new,'chapter one mass deployment');p.add(a['directory']+8+e['index']*8,struct.pack('<II',dest-a['directory'],len(new)),'script entry');p.add(root['directory']+8+14*8+4,struct.pack('<I',dest+len(new)-a['offset']),'script span')
 p.validate();return p

def main():
 report,rows=prepare();target=ROOT/'SRWOGG_ALL_CAST_CH1.iso';assert not target.exists()
 with SOURCE.open('rb') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==EXPECTED;p=make_plan(f,rows)
 shutil.copyfile(SOURCE,target)
 with target.open('r+b') as f:
  for o,a,b,label in p.edits:assert read(f,o,len(a))==a;f.seek(o);f.write(b)
  f.flush();os.fsync(f.fileno())
 inverse=hashlib.sha256();digest=hashlib.sha256();pos=0
 with target.open('rb') as f:
  for o,a,b,label in p.edits:
   while pos<o:
    raw=f.read(min(4<<20,o-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
   assert f.read(len(b))==b;inverse.update(a);digest.update(b);pos+=len(b)
  while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
 assert inverse.hexdigest()==EXPECTED
 result=dict(source=str(SOURCE),target=str(target),source_sha256=EXPECTED,target_sha256=digest.hexdigest(),additional_pairs=len(rows),distinct_units=len({r['unit_name'] for r in rows}),distinct_pilots=len({r['pilot_name'] for r in rows}),all_unrelated_bytes_preserved=True,live_verified=False,cast=rows,edits=[dict(offset=o,size=len(b),label=l,sha256=hashlib.sha256(b).hexdigest()) for o,a,b,l in p.edits])
 (ROOT/'manifest_all_cast.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 text=['OG외전 1화 누락 기체·파일럿 전원 등장 시험판','',f'추가 편성: {len(rows)}기。 아래 목록은 원본과 별도인 아군 복제 데이터。','동일 기체의 세부 변형을 모두 중복 배치하는 대신 각 기체명·누락 파일럿을 포함。','1화 검증용。 이후 본편 진행 및 전체 전투 연출은 미검증。','정신기 SP 1。 잉그램 자막 한글 수정 포함。 다른 추가 파일럿의 미번역 자막은 남아 있을 수 있음。','']
 text.extend(f'{i+1:03} {r["unit_name"]} / {r["pilot_name"]}'+(' [원본 음성 없음: 무음]' if r['silent'] else '') for i,r in enumerate(rows))
 (ROOT/'1화_추가_등장목록.txt').write_text('\n'.join(text),encoding='utf-8-sig')
 print(json.dumps({k:v for k,v in result.items() if k not in ('cast','edits')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
