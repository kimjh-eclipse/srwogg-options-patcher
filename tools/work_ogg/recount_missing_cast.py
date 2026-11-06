"""Read-only cast audit; never builds or modifies a game image."""
from audit_missing_cast import *
import re,unicodedata

GENERIC={'스태프','오퍼레이터','용호왕','？？？','무인','ＡＩ','ＨＡＩ','자율회로','제어병','양산형Ｗ','Ｍ칠드런','일반병','엘리트병','연방병','연방함장','Ｃ군함장','ＤＣ병','ＤＣ잔당병','ＬＢ병','Ｓ미러병','트로이에병'}
def norm(s):
 return re.sub(r'[\s・·－ー\-]','',unicodedata.normalize('NFKC',s))
def main():
 data=json.loads((OUT/'missing_cast.json').read_text(encoding='utf-8'));pilots={int(k):v for k,v in data['ogg_pilots'].items()};units={int(k):v for k,v in data['ogg_units'].items()}
 deployment={};subs={};speakers={};prefixes={};mentions={};all_lines=[]
 with SOURCE.open('rb') as f:
  for slot in [13,14]:
   a=json.loads((OUT/f'MAP.BIN.{slot}.json').read_text())
   for e in a['entries']:
    if not any(2001<=k<=2034 or 2050<=k<=2056 or k==1199 for k in e['keys']):continue
    b=read(f,e['offset'],e['size'])
    if slot==13 and b[:4]==b'UNTD' and len(b)==44+u32(b,40)*336:
     for i in range(u32(b,40)):
      row=b[44+i*336:44+(i+1)*336]
      for field,store in [(32,deployment),(36,subs),(40,subs),(44,subs)]:
       p=u32(row,field)
       if p in pilots:store.setdefault(pilots[p]['name'],[]).append(dict(stage=e['keys'],row=i,field=field))
    if slot==14 and b[:4]==b'LOGO':
     n=u32(b,0x40)+u32(b,0x50);base=u32(b,0x4c);table=u32(b,0x44)
     def text(k):
      if k>=n:return ''
      p=base+u32(b,table+k*4)
      return decode(b[p:b.index(0,p)])
     for i in range(u32(b,0x28)):
      p=u32(b,0x2c)+i*96
      if u32(b,p)!=0x30:continue
      line=text(u32(b,p+8));who=u32(b,p+16);ev=dict(stage=e['keys'],record=i,text=line)
      all_lines.append(ev)
      if who in pilots:speakers.setdefault(pilots[who]['name'],[]).append(ev)
      pre=re.match(r'^([^：:]{1,16})[：:]',line)
      if pre:prefixes.setdefault(pre.group(1).strip('　「 '),[]).append(ev)
 names={x['pilot_name'] for x in data['missing'] if x['missing_pilot']}
 found=set(deployment)|set(subs)|set(speakers)|set(prefixes)
 # Alternate names/personae are not additional people.
 aliases={'엘잠':'레첼','레비':'마이'}
 known_aliases={name:other for name,other in aliases.items() if other in found}
 candidates=sorted(names-GENERIC-found-set(known_aliases))
 # Name mentions are evidence to review, not evidence of actual character appearance.
 for name in candidates:
  matches=[r for r in all_lines if name in r['text']]
  if matches:mentions[name]=matches
 unit_names={r['unit_name'] for r in data['missing'] if r['missing_unit']};present_units={norm(s) for s in data['ogg_story_unit_names']}
 missing_units=sorted(s for s in unit_names if norm(s) not in present_units and s!='ダミー')
 result=dict(scope='OGG story keys 1199,2001..2034,2050..2056; primary/subpilots and actual dialogue speakers; name mentions do not count as appearances',named_pilot_candidates=candidates,named_pilot_candidate_count=len(candidates),prior_missing_but_confirmed_present=sorted(names&found),aliases_already_present=known_aliases,generic_names_excluded=sorted(names&GENERIC),unit_names_not_deployed=missing_units,unit_name_count=len(missing_units),character_evidence=dict(primary=deployment,subpilots=subs,speakers=speakers,prefixes=prefixes),candidate_name_mentions=mentions)
 (OUT/'missing_cast_corrected.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('named candidates',len(candidates),candidates);print('confirmed present',sorted(names&found));print('aliases',known_aliases);print('generic excluded',len(names&GENERIC));print('unit names not deployed',len(missing_units),missing_units)
 print('mentions',[(k,len(v),v[0]) for k,v in mentions.items()])
if __name__=='__main__':main()
