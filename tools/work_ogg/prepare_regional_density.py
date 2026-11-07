"""Double only the five added missions:30 ordinary enemies and2 bosses each."""
from pathlib import Path
import sys,json,struct,copy
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32
from catalog import decode

DEST=ROOT/'analysis/regional_density';START=0x1ae80000;LIMIT=0x1af00000

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('regional_density_applied');p=copy.deepcopy(json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8')));DEST.mkdir(exist_ok=True);cursor=START;changes=[]
 with TARGET.open('rb') as f:
  ua,units=loadarc(f,13);_,logos=loadarc(f,14);_,terrain=loadarc(f,12);b=read(f,terrain[0][1],terrain[0][2]);names={i:decode(b[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);raw={k:read(f,at,n) for ks,at,n in mt for k in ks};tiles={}
  for ks,at,n in mi:
   info=read(f,at,n)
   if u32(info,12) in raw:
    for k in ks:tiles[k]=raw[u32(info,12)]
  for scene in p['scenes']:
   _,at,n=next(e for e in units if scene['key'] in e[0]);old=read(f,at,n);assert len(old)==44+28*336 and u32(old,40)==28
   rows=[old[44+i*336:44+(i+1)*336] for i in range(28)];regular=[(i,r) for i,r in enumerate(rows) if u32(r,8)==2 and not 0x780<=u32(r)<0x78a];assert len(regular)==14
   t=tiles[scene['map_key']];w,h=u32(t,8),u32(t,12)
   def tid(x,y):return u32(t,32+(y*w+x)*8)&65535
   def valid(x,y):
    name=names.get(tid(x,y),'')
    return name not in ['','영역 밖'] and ('우주' in name if scene['key']==2038 else not any(s in name for s in ['바다','호수','수중','용암']))
   positions={(u32(r,16),u32(r,20)) for r in rows};allies=[(u32(r,16),u32(r,20)) for r in rows if u32(r,8)==6];bosses=[(u32(r,16),u32(r,20)) for r in rows if 0x780<=u32(r)<0x78a]
   candidates=[(x,y) for y in range(1,h-1) for x in range(1,w-1) if valid(x,y) and min(abs(x-a)+abs(y-b) for a,b in allies)>=8 and min(abs(x-a)+abs(y-b) for a,b in bosses)>=3]
   additions=[]
   for j in range(16):
    index,source=regular[j%14];sx,sy=u32(source,16),u32(source,20);st=tid(sx,sy)
    available=[c for c in candidates if c not in positions and min(abs(c[0]-x)+abs(c[1]-y) for x,y in positions)>=2];assert available,(scene['key'],j)
    x,y=min(available,key=lambda c:(tid(*c)!=st,abs(c[0]-sx)+abs(c[1]-sy),c[1],c[0]));positions.add((x,y));row=bytearray(source)
    struct.pack_into('<II',row,16,x,y);rows.append(row);extra=dict(source_row=index,row=28+j,unit=u32(row),pilot=u32(row,32),position=[x,y],terrain=names[tid(x,y)]);additions.append(extra)
    record=copy.deepcopy(scene['enemies'][index-12]);record.update(position=[x,y],boss=False,additional=True);scene['enemies'].append(record)
   new=bytearray(old[:44]);struct.pack_into('<I',new,40,44);new.extend(b''.join(rows));assert new[44:44+28*336]==old[44:]
   cursor=(cursor+2047)&~2047;assert cursor+len(new)<=LIMIT and not any(read(f,cursor,len(new)));assert all(cursor+len(new)<=p or cursor>=p+n for _,p,n in units+logos)
   (DEST/f'{scene["key"]}.untd').write_bytes(new);previous=scene['untd'];scene['untd']=dict(file=f'{scene["key"]}.untd',offset=cursor,size=len(new));scene.update(enemy_count=32,ordinary_enemy_count=30,boss_count=2)
   for entry in p['resources']:
    if entry['file']==scene['untd']['file']:entry.update(scene['untd'])
   ix=next(e['index'] for e in ua['entries'] if scene['key'] in e['keys']);changes.append(dict(key=scene['key'],previous_untd=previous,untd=scene['untd'],directory_pointer=ua['directory']+8+ix*8,pointer_hex=struct.pack('<II',cursor-ua['directory'],len(new)).hex(),added=additions,original_rows_preserved=28));cursor+=len(new)
 p.update(enemies_per_mission=32,ordinary_enemies_per_mission=30,allocation_end=cursor,regional_density=True)
 report=dict(prepared=True,before_sha256=state['current_sha256'],scenes=changes,new_regional_prepared=p,allocation_start=START,allocation_end=cursor,allocation_limit=LIMIT,added_enemies=80,enemies_per_mission=32,ordinary_enemies_per_mission=30,bosses_per_mission=2,masters_and_LOGO_unchanged=True,extra_full_ISOs_created=0)
 (ROOT/'regional_density_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ['scenes','new_regional_prepared']},ensure_ascii=False))

if __name__=='__main__':main()
