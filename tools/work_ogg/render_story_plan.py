import json
from pathlib import Path
from urllib.parse import quote

root=Path(__file__).resolve().parent
path=root/'story_plan_25_v1.json'
plan=json.loads(path.read_text(encoding='utf-8'))
chars=plan['characters']
assert len(chars)==25
assert {c['roster_no'] for c in chars}==set(range(1,26))
assert all(3<=c['arrival']<=c['playable']<=31 for c in chars)
assert max(c['arrival'] for c in chars)==29
assert len({c['name'] for c in chars})==25
assert not ({c['name'] for c in chars}&{'쿠엘보','리리','마이어','반','아기라','셉타긴','세프타킨'})

sources={}
for c in chars:
 c['source_urls']=['https://namu.wiki/w/'+quote(n,safe='/') for n in c['source_pages']]
 sources.update(zip(c['source_pages'],c['source_urls']))
records=[]
for f in sorted((root/'story_research').glob('*.json')):
 d=json.loads(f.read_text(encoding='utf-8'))
 if 'text' not in d: continue
 records.append({'file':f.name,'title':d['title'],'url':d.get('url'),
                 'characters':len(d['text']),
                 'missing': '해당 문서를 찾을 수 없습니다' in d['text']})
(root/'story_research'/'research_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

# Ensure every character page was actually read, including shared articles and redirects.
aliases={'카와이 라우':'가루인 메하벨','메키보스 보르퀘데':'메키보스'}
for c in chars:
 for name in c['source_pages']:
  candidates=[root/'story_research'/(name+'.json'),root/'story_research'/('robot_'+name+'.json')]
  if name in aliases: candidates.append(root/'story_research'/(aliases[name]+'.json'))
  matches=[x for x in candidates if x.exists()]
  assert matches,(c['name'],name,'unread source')
  assert any('해당 문서를 찾을 수 없습니다' not in json.loads(x.read_text(encoding='utf-8'))['text'] for x in matches)

chapter_records=[]
for c in chars:
 jp=c['chapter'].split(' / ')[1]
 f=root/'story_research'/('chapter_'+jp+'.json')
 assert f.exists(),f
 d=json.loads(f.read_text(encoding='utf-8'))
 c['chapter_source_url']=d['url']
 chapter_records.append((c['arrival'],jp,d['url']))
path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

out=[plan['title'],f"작성일: {plan['date']} / {plan['status']}",'',
     '읽는 기준: [자료]는 실제 읽은 문서의 요약이며, [각색]은 이번 개조판을 위해 새로 쓴 사건과 대사다.',
     '화명은 원문과 함께 이 문서의 한국어 번역을 병기했다. 인물·기체 표기는 현 패치의 25편성 목록을 우선한다.',
     '레몬 자매 관계는 사용자 지정 방향을 최우선으로 반영했다. 자세한 장면안은 문서 후반에 있다.','',
     '전체 줄거리',plan['premise'],'',
     '새 목숨을 얻는 것과 과거를 용서받는 것은 별개의 문제다. 구조받은 인물이 무엇을 지키고 어떤 책임을 질지 선택하는 이야기를 중심에 둔다.','',
     '공통 설정']
out += [f'{i}. {s}' for i,s in enumerate(plan['rules'],1)]
out += ['', '등장·출격 배치표', '최초 출현 | 인물 / 기체 | 출격 가능 | 삽입편 제목']
for c in chars:
 out.append(f"{c['arrival']:02d}화 | {c['name']} / {c['robot']} | {c['playable']:02d}화 | {c['episode_title']}")
out += ['', '모든 편성은 29화까지 등장하고 31화까지 출격 가능해진다. 10~14화 분기와 16~18화 독립 전개는 기존 흐름을 유지한다.',
        '수용 중이거나 정비 중인 인물도 대화와 갈등에는 등장한다. 부대에 기체가 추가되는 것과 모든 맵에 강제 출격하는 것은 구분한다.','',
        '인물별 상세 시나리오']
fields=[('facts','[자료] 성격·관계·원작 행적'),('departure','[각색] 죽기 직전의 출발점'),
        ('entrance','[각색] 등장 장면'),('relationship','[각색] 핵심 관계'),
        ('choice','[각색] 합류까지의 선택'),('robot_story','기체 운용과 설정 경계'),('followup','[각색] 후속 전개')]
for c in chars:
 out += ['', '='*64,
         f"{c['arrival']}화 출현 / {c['playable']}화 출격 — {c['name']} / {c['robot']}",
         f"자료명: {c['canonical_name']} / 기존 편성 번호: {c['roster_no']}",
         c['chapter'],f"추가편: {c['episode_title']}",'']
 for key,label in fields: out += [label,c[key],'']
 out+=['[각색] 대사 예시']+c['dialogue']+['','자료 출처']
 out += [f'{n}: {u}' for n,u in zip(c['source_pages'],c['source_urls'])]
 out += ['화별 출격 근거: '+c['chapter_source_url']]

arc=plan['lemon_sister_arc']
out+=['','='*64,'레몬·액셀렌 자매의 인연 — 연속 장면안','',arc['direction'],'','원작과 각색의 경계',arc['canon_boundary']]
for beat in arc['beats']: out+=['',f"{beat['chapter']}화 — {beat['name']}",beat['scene']]
out+=['','23화 대화 초안']+arc['sample_scene']
out+=['','전체 사건을 잇는 줄기']+plan['throughline']
out+=['','후반부와 엔딩']+plan['later_story']
out+=['','향후 구현 메모 — 이번에는 미적용']+plan['implementation_notes']
out+=['','자료 조사 범위',plan['research']['character_source'],plan['research']['chapter_source'],
      '화별 목록: '+plan['research']['chapter_list_url'],
      '출격 시기: '+plan['research']['timetable_url'],
      '나무위키 개요: '+plan['research']['namu_overview'],
      '나무위키 공략: '+plan['research']['namu_guide'],
      '인물과 기체 출처:']
out += [f'{n}: {u}' for n,u in sorted(sources.items())]
out += ['','조사일: 2026-11-06. 위키 서술은 시리즈·매체에 따라 차이가 있으므로 게임 구현 전에 원본 이벤트와 기체 자산을 추가 대조한다.',
        '각색 대사는 인용문이 아니라 새로 작성한 문장이다. ISO 변경·실행 검증은 이번 작업에 포함되지 않는다.']
target=root/'OG외전_25편성_등장시나리오_초안.txt'
target.write_text('\n'.join(out)+'\n',encoding='utf-8-sig')

audit={'count':len(chars),'roster_numbers':sorted(c['roster_no'] for c in chars),
       'first_arrival':min(c['arrival'] for c in chars),'last_arrival':max(c['arrival'] for c in chars),
       'last_playable':max(c['playable'] for c in chars),
       'new_arrival_in_route_split':any(10<=c['arrival']<=14 for c in chars),
       'new_arrival_in_wolves_arc':any(16<=c['arrival']<=18 for c in chars),
       'source_pages':len(sources),'text_file':str(target),'text_characters':len('\n'.join(out)),
       'iso_modified':False}
(root/'story_plan_25_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
