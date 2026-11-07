"""Prepare the requested unmanned bosses, plus validated map coordinates."""
from pathlib import Path
import sys,json,struct,copy,collections
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT/('option_regional' if (ROOT/'option_regional').exists() else 'option_release')),str(ROOT)]
from build_options import rawmaster
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32
from catalog import decode,u16
from regional_five_content import SCENARIOS
from regional_five_policy import mission_logo
from regional_boss_policy import rebuild_master,OPENING,STORY_OPENING,ENDING

DEST=ROOT/'analysis/regional_bosses';START=0x1ae60000;LIMIT=0x1af00000

def main():
 state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'));assert not state.get('regional_bosses_applied');oldprep=json.loads((ROOT/'regional_five_prepared.json').read_text(encoding='utf8'));p=copy.deepcopy(oldprep);DEST.mkdir(exist_ok=True)
 speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers'];speakers['알피미']=0x543;speakers['레피나']=0x4b9
 scenarios=copy.deepcopy(SCENARIOS);scenarios[3]['map_source']=40;scenarios[3]['map_slot']=0
 cursor=START;notes=[]
 with TARGET.open('rb') as f:
  e,m=rawmaster(f,'SHARED.BIN');master,mnote=rebuild_master(m.b);(DEST/'SHARED.BIN.master').write_bytes(master)
  _,mi=loadarc(f,10);_,mt=loadarc(f,11);_,terrain=loadarc(f,12);_,units=loadarc(f,13);_,logos=loadarc(f,14)
  terrain=read(f,terrain[0][1],terrain[0][2]);names={i:decode(terrain[8+i*52:40+i*52].split(b'\0')[0]).split('@')[0].replace('　',' ') for i in range(1024)}
  tilesraw={k:read(f,at,n) for keys,at,n in mt for k in keys};tiles={}
  for keys,at,n in mi:
   info=read(f,at,n)
   if u32(info,12) in tilesraw:
    for k in keys:tiles[k]=tilesraw[u32(info,12)]
  def live(entries,key):
   _,at,n=next(e for e in entries if key in e[0]);return read(f,at,n)
  template=live(logos,2032)
  for index,(scene,content) in enumerate(zip(p['scenes'],scenarios)):
   old=live(units,scene['key']);b=bytearray(old);mapkey=40 if index==3 else scene['map_key'];t=tiles[mapkey];w,h=u32(t,8),u32(t,12)
   def terrain_name(x,y):return names.get(u32(t,32+(y*w+x)*8)&65535,'')
   def valid(x,y):return 1<=x<w-1 and 1<=y<h-1 and terrain_name(x,y) not in ['','영역 밖'] and ('우주' in terrain_name(x,y) if index==3 else True)
   candidates=[(x,y) for y in range(1,h-1) for x in range(1,w-1) if valid(x,y)];assert len(candidates)>=50
   rows=[bytearray(old[44+i*336:44+(i+1)*336]) for i in range(u32(old,40))];occupied=set();repaired=[]
   for i,row in enumerate(rows[:26]):
    previous=(u32(row,16),u32(row,20));desired=previous if index!=3 else (w//2+(i%5)-2,h-7+i//5 if i<12 else 6+(i-12)//5)
    chosen=min((c for c in candidates if c not in occupied),key=lambda c:abs(c[0]-desired[0])+abs(c[1]-desired[1]));occupied.add(chosen)
    for off,v in [(16,chosen[0]),(20,chosen[1])]:struct.pack_into('<I',row,off,v)
    if chosen!=previous:repaired.append(dict(row=i,before=list(previous),after=list(chosen),terrain=terrain_name(*chosen)))
   allies=[(u32(r,16),u32(r,20)) for r in rows[:12]]
   bosses=mnote['units'][index*2:index*2+2]
   for j,(row,boss) in enumerate(zip(rows[26:28],bosses)):
    desired=(w//2+(-7 if j==0 else 7),5)
    choices=[c for c in candidates if c not in occupied and min(abs(c[0]-x)+abs(c[1]-y) for x,y in allies)>=8 and (index!=1 or all(s not in terrain_name(*c) for s in ['바다','수중','호수']))]
    assert choices;chosen=min(choices,key=lambda c:abs(c[0]-desired[0])+abs(c[1]-desired[1]));occupied.add(chosen)
    for off,v in [(0,boss['key']),(4,0),(8,2),(12,0),(16,chosen[0]),(20,chosen[1]),(28,0),(32,1029)]:struct.pack_into('<I',row,off,v)
    for off in [0x60,0x74,0x88]:struct.pack_into('<I',row,off,0xffff0000|1029)
    for off in [0x50,0x54,0x58]:struct.pack_into('<I',row,off,(49+index)*500)
    boss.update(position=list(chosen),terrain=terrain_name(*chosen),row=26+j);scene['enemies'][14+j].update(unit=boss['key'],pilot=1029,position=list(chosen),boss=True,name=boss['name'])
   for i,row in enumerate(rows[12:26]):scene['enemies'][i]['position']=[u32(row,16),u32(row,20)]
   struct.pack_into('<4I',b,8,mapkey,0xffffffff,0xffffffff,0xffffffff);b=b[:44]+b''.join(rows);assert len(b)==len(old)
   (DEST/f'{scene["key"]}.untd').write_bytes(b)
   content['opening']+=OPENING[index];content['story_opening']+=STORY_OPENING[index];content['ending']=ENDING[index]+content['ending']
   logo,lnote=mission_logo(template,content,speakers,mapkey,scene['key']-1999 if index<4 else 33);cursor=(cursor+2047)&~2047;assert cursor+len(logo)<=LIMIT and not any(read(f,cursor,len(logo)))
   assert all(cursor+len(logo)<=at or cursor>=at+n for _,at,n in units+logos)
   (DEST/f'{scene["key"]}.logo').write_bytes(logo);oldlogo=scene['logo'];scene['logo']=dict(file=f'{scene["key"]}.logo',offset=cursor,size=len(logo));cursor+=len(logo)
   scene.update(lnote);scene.update(map_source=content['map_source'],map_slot=content['map_slot'],map_key=mapkey,dimensions=[w,h],bosses=bosses)
   for r in p['resources']:
    if r['file']==scene['logo']['file']:r.update(scene['logo'])
   notes.append(dict(key=scene['key'],old_logo=oldlogo,logo=scene['logo'],untd=scene['untd'],bosses=bosses,repaired_positions=repaired,all_positions_valid=True))
 p['masters']['SHARED.BIN']['used_bytes']=mnote['used_bytes'];p.update(allocation_end=cursor,regional_bosses=True,unmanned_boss_count=10,playthrough_verified=False)
 report=dict(prepared=True,before_sha256=state['current_sha256'],unmanned_only=True,masters={'SHARED.BIN':dict(offset=e['offset'],size=e['size'],file='SHARED.BIN.master',**mnote)},scenes=notes,scenario_content=scenarios,new_regional_prepared=p,allocation_start=START,allocation_end=cursor,allocation_limit=LIMIT,map38_corrected_from=151,map38_corrected_to=40,map39_invalid_placements_repaired=True,extra_full_ISOs_created=0)
 (ROOT/'regional_bosses_prepared.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(dict(prepared=True,bosses=10,private_weapons=mnote['weapon_count'],master_used=mnote['used_bytes'],allocation_end=hex(cursor),image_modified=False),ensure_ascii=False))

if __name__=='__main__':main()
