"""Add two guard-side sorties and revise the joint rescue in place."""
from pathlib import Path
import sys,json,struct,base64,zlib,hashlib
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_civil_war' if (ROOT/'option_civil_war').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster
from audit_story_layout import TARGET,loadarc
from inspect_iso import inventory,lice,read,u32
from catalog import Master,u16,encode
from regional_five_policy import stage_base,append_strings
from civil_war_policy import mission,GUARD,INFIL,REBELS,RELAY_KEYS,HOSTAGE_KEY,ORDINARY_KEYS
from civil_guard_content import chapters,ORDER,MOB_LEVEL,ACE_LEVEL
from civil_reinforcement_policy import append_waves,KEYS,SOURCES,OFFSETS
DEST=ROOT/'analysis/civil_guard'
INITIAL_KEYS=ORDINARY_KEYS+[2043,2044]

def edit_master(old,titles,shared=True):
 m=Master(old);fields=list(range(0x18,0x8c,4));starts=[u32(old,k) for k in fields];parts={k:bytearray(old[p:starts[i+1] if i+1<len(starts) else p+u32(old,p+4)]) for i,(k,p) in enumerate(zip(fields,starts))};sid=m.tables['Strg'][2]
 for i,key in enumerate([2043,2044]):
  assert u16(parts[0x18],12+key*2)==65535;struct.pack_into('<H',parts[0x18],12+key*2,u16(parts[0x18],12+SOURCES[i]*2))
 if shared:
  parts[0x80]=append_strings(parts[0x80],[encode(t) for t in titles]);sb=stage_base(m)-m.tables['Stag'][0]
  for i,key in enumerate([2046,2047]):
   at=sb+(key-2000)*12;assert parts[0x58][at:at+2]==b'\xff\xff';row=bytearray(parts[0x58][sb+43*12:sb+44*12]);struct.pack_into('<Hhh',row,0,sid+i,-1,-1);row[6]=45+i;parts[0x58][at:at+12]=row
  for index,num in [(44,47),(45,48),(34,49)]:parts[0x58][sb+index*12+6]=num
 out=bytearray(old[:starts[0]])
 for k in fields:struct.pack_into('<I',out,k,len(out));out.extend(parts[k])
 assert len(out)<=len(old);out.extend(bytes(len(old)-len(out)));n=Master(out)
 for tag in m.tables:
  if tag in ['UTbl','Stag','Strg']:continue
  a,size,_=m.tables[tag];b=n.tables[tag][0];assert old[a:a+size]==out[b:b+size],tag
 return bytes(out)

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert state['civil_reinforcements_applied'] and not state.get('civil_guard_applied');prior=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));members=prior['members'];private=prior['private'];scenes=chapters(members);DEST.mkdir(exist_ok=True);edits=[];prepared=[]
 with TARGET.open('rb') as f:
  ua,us=loadarc(f,13);la,ls=loadarc(f,14);mf=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,mf['offset'],mf['size']);_,current=rawmaster(f,'SHARED.BIN');blocked=[(at,at+n) for ks,at,n in us+ls]
  start=0x1ac39800;end=0x1b480000;raw=read(f,start,end-start);gaps=[];first=None
  for i in range(0,len(raw),2048):
   at=start+i;free=not any(raw[i:i+2048]) and all(at+2048<=a or at>=b for a,b in blocked)
   if free and first is None:first=at
   if not free and first is not None:gaps.append([first,at]);first=None
  if first is not None:gaps.append([first,end])
  def edit(at,data,label):
   fn='edit_%03d.bin'%len(edits);(DEST/fn).write_bytes(data);before=read(f,at,len(data));edits.append(dict(offset=at,size=len(data),file=fn,label=label,before_zlib_base64=base64.b64encode(zlib.compress(before,9)).decode('ascii'),after_sha256=hashlib.sha256(data).hexdigest()))
  def alloc(fn,data):
   for g in gaps:
    at=(g[0]+2047)&~2047
    if at+len(data)<=g[1]:break
   else:raise AssertionError(('no free MAP gap',len(data)))
   assert not any(read(f,at,len(data)));g[0]=(at+len(data)+2047)&~2047;(DEST/fn).write_bytes(data);edit(at,data,fn);return dict(file=fn,offset=at,size=len(data))
  def get(entries,key):
   _,at,n=next(e for e in entries if key in e[0]);return read(f,at,n)
  for ar in ['SHARED.BIN','IM.BIN']:
   e,m=rawmaster(f,ar);b=edit_master(m.b,[s['title'] for s in scenes if s['key'] in [2046,2047]],ar=='SHARED.BIN');(DEST/(ar+'.master')).write_bytes(b);edit(e['offset'],b,'Guard chapters/titles/aliases '+ar)
  template=get(ls,2040)
  for ix,s in enumerate(scenes):
   key=s['key'];source=get(us,s['map_from'] if key in [2046,2047] else key);rows=[bytearray(source[44+i*336:44+(i+1)*336]) for i in range(45)];spawn=[]
   if key in [2046,2047]:
    names=['아치볼드','이글렛'] if key==2046 else ['빈델','웬드로'];targets=[private[n] for n in names];enemy_keys=targets+INITIAL_KEYS
   elif key==2044:names=[];targets=RELAY_KEYS[:2];enemy_keys=targets+INITIAL_KEYS
   else:
    old=next(x for x in prior['scenes'] if x['key']==key);targets=old['targets'];enemy_keys=[x['key'] for x in old['spawn']]
   assert len(enemy_keys)==32
   for j,k in enumerate(enemy_keys):
    row=rows[12+j];who=next((n for n,v in private.items() if v==k),None);pk=k if who else 1029
    for off,val in [(0,k),(4,0),(8,2),(12,0),(28,0),(32,pk),(36,-1),(40,-1),(44,-1)]:struct.pack_into('<I',row,off,val&0xffffffff)
    for off in [0x60,0x74,0x88]:struct.pack_into('<I',row,off,0xffff0000|pk)
    level=MOB_LEVEL if k in INITIAL_KEYS else ACE_LEVEL if who and members[who]['team']==REBELS else None
    if level:
     for off in [0x50,0x54,0x58]:struct.pack_into('<I',row,off,(level-1)*500)
    spawn.append(dict(row=12+j,key=k,pilot=pk,who=who,base_grade=6,position=[u32(row,16),u32(row,20)],level=level))
   assert u32(rows[44])==HOSTAGE_KEY
   for j,k in enumerate(KEYS):
    row=bytearray(rows[12]);dx,dy=OFFSETS[j%6]
    for off,val in [(0,k),(4,2+j//6),(32,1029),(16,dx),(20,dy)]:struct.pack_into('<I',row,off,val&0xffffffff)
    for off in [0x50,0x54,0x58]:struct.pack_into('<I',row,off,(MOB_LEVEL-1)*500)
    for off in [0x60,0x74,0x88]:struct.pack_into('<I',row,off,0xffff0000|1029)
    rows.append(row);spawn.append(dict(row=45+j,key=k,pilot=1029,who=None,source=SOURCES[j%6],turn=2+j//6,group=2+j//6,offset=[dx,dy],base_grade=6,level=MOB_LEVEL))
   units=bytearray(source[:44]);units[24:40]=str(key).encode('ascii')+bytes(12);struct.pack_into('<I',units,40,63);units.extend(b''.join(rows));un=alloc(str(key)+'.untd',units)
   nextindex=ORDER[ix+1]-2000 if ix+1<len(ORDER) else 34;logo,note=mission(template,s,members,prior['speakers'],private,u32(units,8),targets,nextindex);logo,wave=append_waves(logo,alert_pilot=1181 if key in [2046,2047] else 1071);lo=alloc(str(key)+'.logo',logo)
   prepared.append(dict(key=key,number=s['number'],title=s['title'],map_key=u32(units,8),untd=un,logo=lo,spawn=spawn,initial_spawn=spawn[:32],wave_spawn=spawn[32:],**note,waves=wave['waves'],alert_messages=wave['messages'],all_messages=note['messages']+wave['messages'],guard_player_only=key in [2046,2047]))
  for slot,arc,kind,leaves in [(13,ua,'untd',us),(14,la,'logo',ls)]:
   count=arc['count'];assert not any(read(f,arc['directory']+8+count*8,16));edit(arc['offset']+8,struct.pack('<I',count+2),'LICE count '+str(slot));edit(arc['directory']+4,struct.pack('<I',count+2),'Wpbb count '+str(slot))
   added=0
   for s in prepared:
    key=s['key'];r=s[kind]
    if key in [2046,2047]:
     assert read(f,arc['offset']+16+key*2,2)==b'\xff\xff';index=count+added;added+=1;edit(arc['offset']+16+key*2,struct.pack('<H',index),kind+' key '+str(key))
    else:index=next(e['index'] for e in arc['entries'] if key in e['keys'])
    edit(arc['directory']+8+index*8,struct.pack('<II',r['offset']-arc['directory'],r['size']),kind+' pointer '+str(key))
   parent=outer['entries'][slot];end=max([at+n for ks,at,n in leaves]+[s[kind]['offset']+s[kind]['size'] for s in prepared]);edit(outer['directory']+8+slot*8+4,struct.pack('<I',max(parent['size'],end-parent['offset'])),'MAP parent span '+str(slot))
 edits.sort(key=lambda e:e['offset']);assert all(a['offset']+a['size']<=b['offset'] for a,b in zip(edits,edits[1:]))
 effective={**prior,'scenes':prepared,'automatic_encounter_pairs':sum(len(s['pairs']) for s in prepared),'new_dialogue_boxes':sum(len(s['all_messages']) for s in prepared),'total_extra_battles':13,'final_display_chapter':49,'chapter_order':ORDER,'mob_level':MOB_LEVEL,'ace_level':ACE_LEVEL}
 result=dict(prepared=True,applied=False,before_sha256=state['current_sha256'],edits=edits,scenes=prepared,effective_civil=effective,new_keys=[2046,2047],chapter_order=ORDER,mob_level=MOB_LEVEL,ace_level=ACE_LEVEL,total_extra_battles=13,final_display_chapter=49)
 (ROOT/'civil_guard_prepared.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['edits','scenes','effective_civil']},indent=2))
if __name__=='__main__':main()
