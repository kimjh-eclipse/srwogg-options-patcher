"""Read-only audit for the authorized five-part civil-war insertion."""
from pathlib import Path
import sys,json,struct,collections
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT/('option_intermission' if (ROOT/'option_intermission').exists() else 'option_release'))]
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32,inventory,lice
from build_options import rawmaster
from catalog import u16

def main():
 plan=json.loads((ROOT/'CIVIL_WAR_CAST_PLAN_DRAFT.json').read_text(encoding='utf8'));cast=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'))['cast'];added={x['pilot_name']:x for x in cast if x['pilot_name'] not in ['아기라','세프타킨']}
 speakers=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))['speakers'];speakers.update({'레피나':1209,'숀':1119,'윤':1181,'에이타':1071,'알피미':1347})
 aliases={'아라도':'아라드','액셀렌':'엑셀렌','제올라':'제오라','불릿':'브릿트'};result={};templates={}
 with TARGET.open('rb') as f:
  _,m=rawmaster(f,'SHARED.BIN');_,us=loadarc(f,13);la,ls=loadarc(f,14)
  pn={}
  for k in range(m.tables['PTbl'][2]):
   ix=u16(m.b,m.tables['PTbl'][0]+12+k*2)
   if ix!=65535:pn[k]=m.text(u16(m.b,m.tables['Plot'][0]+12+ix*148+4))
  for ks,p,n in us:
   b=read(f,p,n)
   if len(b)!=44+u32(b,40)*336:continue
   for i in range(u32(b,40)):
    r=b[44+i*336:44+(i+1)*336];pk=u32(r,32);uk=u32(r)
    if pk in pn and 0<uk<1792 and u16(m.b,m.tables['UTbl'][0]+12+uk*2)!=65535 and u32(r,8)==0:
     templates.setdefault(pk,[]).append((max(ks or [0]),uk,r))
  for team,items in plan['teams'].items():
   for who in items['기존']+items['추가']:
    if who in added:
     key=added[who]['new_key'];uk=key;row=None
    else:
     name=aliases.get(who,who);keys=[k for k,n in pn.items() if n==name and 1000<=k<1792]
     key=speakers.get(who, min(keys) if keys else None)
     if key is None:continue
     choices=[t for k in keys for t in templates.get(k,[])];choices.sort(key=lambda t:t[0],reverse=True)
     uk=choices[0][1] if choices else None;row=choices[0][2].hex() if choices else None
    result[who]=dict(team=team,pilot=key,unit=uk,template=row,added=who in added)
  used=set()
  for ks,p,n in ls:
   for r in __import__('story_scripts_25').records(read(f,p,n)):
    if r[0] in [0x93,0xba,0x7e,0x2b,0x79] and r[2]==0x100c1 and r[3]<64 and r[4]<8:used.add((r[3],r[4]))
  freeflags=[(g,b) for g in range(36,56) for b in range(8) if (g,b) not in used]
  blocked=[(at,at+n) for ks,at,n in us+ls];start=0x1ac39800;end=0x1b480000;f.seek(start);raw=f.read(end-start);runs=[];first=None
  for i in range(0,len(raw),2048):
   at=start+i;empty=not any(raw[i:i+2048]) and all(at+2048<=a or at>=b for a,b in blocked)
   if empty and first is None:first=at
   if not empty and first is not None:
    if at-first>=16384:runs.append([first,at])
    first=None
  if first is not None:runs.append([first,end])
  summary=dict(members=result,speakers=speakers,free_global_flags=freeflags,zero_map_gaps=runs,master_bytes=len(m.b),stage_counts=list(struct.unpack_from('<3H',m.b,m.tables['Stag'][0]+12)))
 (ROOT/'civil_war_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 print('Combat bodies:',[(n,x['pilot'],x['unit']) for n,x in result.items() if x['unit'] is not None]);print('MAP zero gaps:',[(hex(a),b-a) for a,b in runs]);print('Free flags:',len(freeflags),'stage counts',summary['stage_counts'])
if __name__=='__main__':main()
