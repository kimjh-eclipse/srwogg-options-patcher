"""Localize the requested help page and remove Agira/Septuagint deployments."""
from catalog import *
import re,os

WORDS={
 'フリーカーソル':'프리 커서',
 '左スティックを倒す、または方向キーで':'왼쪽 스틱 또는 방향키로',
 'カーソルを移動させます。':'커서를 이동합니다。',
 '操作可能なユニットにカーソルが合った状態で':'조작 가능한 유닛에 커서를 맞추고 ',
 'を押すと':' 누르면',
 '「個別コマンド」':'「개별 명령」',
 'が表示され、ユニットが無い場所で':'이 표시되며、빈 지형에서 ',
 '「全体コマンド」':'「전체 명령」',
 'が表示されます。':'이 표시됩니다。',
 '個別コマンド':'개별 명령',
 '…そのユニットを操作するためのコマンドです。':'…해당 유닛을 조작하는 명령입니다。',
 '全体コマンド':'전체 명령',
 '…情報確認、ゲーム設定、セーブ等を行うためのコマンドです。':'…정보 확인、게임 설정、저장 등을 수행합니다。',
 '操作可能なユニットには':'조작 가능한 아군은 ',
 'を押すことによって、':' 버튼으로、',
 '敵のユニットには':'적 유닛은 ',
 'を押すことによって、素早くカーソルを':' 버튼으로 커서를 빠르게',
 '合わせることができます。':'맞출 수 있습니다。',
 'マップ全体の状況を把握するためには？':'맵 전체의 상황을 파악하려면？',
 'を押すとマップの表示モード（通常表示と全体表示）の':' 누르면 맵 표시 모드（일반／전체）를',
 '切り換えを行うことができます。':'전환할 수 있습니다。',
}
def help_text(raw):
 old=raw.decode('cp932');parts=re.split(r'(<[^>]+>)',old);count=0
 for i,t in enumerate(parts):
  if t in WORDS:parts[i]=WORDS[t].replace(' ','　');count+=1
 text=''.join(parts);encoded=encode(text)
 assert re.findall(r'<[^>]+>',text)==re.findall(r'<[^>]+>',old)
 assert text.count('#')==old.count('#')
 assert not any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in text)
 assert decode(encoded)==text and len(encoded)<=len(raw),(len(encoded),len(raw))
 return encoded+bytes(len(raw)-len(encoded)),dict(text_segments=count,before_bytes=len(raw),after_bytes=len(encoded),all_layout_and_button_tags_preserved=True)

def main():
 statefile=ROOT/'current_target.json';state=json.loads(statefile.read_text(encoding='utf8'));target=Path(state['canonical_iso']);assert target==ROOT.parent/'SRWOGS_EX_K_TEST.ISO'
 journal=ROOT/'help_and_lineups_25_journal.json';assert not journal.exists()
 manifest=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf8'));drop={'아기라','세프타킨'};removed=[r for r in manifest['cast'] if r['pilot_name'] in drop];assert len(removed)==2
 dropkeys={r['new_key'] for r in removed};remaining=[r for r in manifest['cast'] if r['new_key'] not in dropkeys];assert len(remaining)==25
 source=(OUT/'free_cursor_help_original.bin').read_bytes();replacement,help_check=help_text(source);edits=[]
 print('Preparing requested help translation and 25-lineup deployment...',flush=True)
 with target.open('rb') as f:
  for archive in ['SHARED.BIN','IM.BIN']:
   root=json.loads((OUT/(archive+'.json')).read_text());e=root['entries'][10];data=read(f,e['offset'],e['size']);where=data.find(source);assert where>=0 and data.count(source)==1
   edits.append((e['offset']+where,source,replacement,archive+' free-cursor help page'))
  a=json.loads((OUT/'MAP.BIN.13.json').read_text());e=next(e for e in a['entries'] if 2001 in e['keys']);dp=a['directory']+8+e['index']*8;offset,length=struct.unpack('<II',read(f,dp,8));at=a['directory']+offset;old=read(f,at,length)
  assert old[:4]==b'UNTD' and u32(old,40)==38 and len(old)==44+38*336
  rows=[old[44+i*336:44+(i+1)*336] for i in range(38)];deleted=[r for r in rows if u32(r) in dropkeys];assert len(deleted)==2
  kept=[r for r in rows if u32(r) not in dropkeys];new=bytearray(old[:44]+b''.join(kept));struct.pack_into('<I',new,40,len(kept));assert len(kept)==36
  assert new[44:44+11*336]==old[44:44+11*336]
  assert {u32(r) for r in kept[11:]}=={r['new_key'] for r in remaining}
  edits.append((at,old,bytes(new)+bytes(length-len(new)),'remove Agira and Septuagint from chapter-one deployment'))
  edits.append((dp+4,struct.pack('<I',length),struct.pack('<I',len(new)),'scenario entry length'))
 edits.sort()
 for l,r in zip(edits,edits[1:]):assert l[0]+len(l[1])<=r[0]
 # Open for writing only after the concrete edit plan has passed all checks.
 with target.open('r+b') as f:
  print('Verifying the single canonical ISO...',flush=True);assert hashlib.file_digest(f,'sha256').hexdigest()==state['current_sha256']
  record=dict(target=str(target),source_sha256=state['current_sha256'],applied=False,help_page='free cursor',help_copies=2,help_check=help_check,removed=[dict(pilot=r['pilot_name'],unit=r['unit_name'],key=r['new_key']) for r in removed],additional_lineups=25,initial_allies=28,edits=[dict(offset=o,before=b.hex(),after=c.hex(),label=l) for o,b,c,l in edits])
  journal.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   for o,b,c,l in edits:assert read(f,o,len(b))==b;f.seek(o);f.write(c)
   f.flush();os.fsync(f.fileno());inverse=hashlib.sha256();digest=hashlib.sha256();pos=0;f.seek(0)
   print('Checking the complete image and preserved game data...',flush=True)
   for o,b,c,l in edits:
    while pos<o:
     raw=f.read(min(4<<20,o-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
    assert f.read(len(c))==c;inverse.update(b);digest.update(c);pos+=len(c)
   while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
   assert inverse.hexdigest()==state['current_sha256']
  except BaseException:
   for o,b,c,l in edits:f.seek(o);f.write(b)
   f.flush();os.fsync(f.fileno());raise
 record.update(applied=True,target_sha256=digest.hexdigest(),all_other_image_data_preserved=True,live_display_verified=False)
 journal.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
 state.update(current_sha256=record['target_sha256'],lineups=25,free_cursor_help_localized=True,last_edit_journal=str(journal));statefile.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 guide=ROOT/'AGENTS.md';s=guide.read_text(encoding='utf8').replace(record['source_sha256'],record['target_sha256']).replace('selected 27 chapter-one lineups','selected 25 chapter-one lineups');s+='\n- Agira and Septuagint were removed from initial deployment by user request. Current additional lineups: 25. The free-cursor help page is Korean in both SHARED and IM archives.\n';guide.write_text(s,encoding='utf8')
 listing=json.loads((OUT/'missing_cast_corrected.json').read_text(encoding='utf8'));flt=listing['ship_filter'];flt['cast']=[r for r in flt['cast'] if r['pilot'] not in drop];flt['remaining_count']=25;flt.setdefault('user_excluded_pairs',[]).extend([dict(pilot=r['pilot_name'],unit=r['unit_name']) for r in removed]);(OUT/'missing_cast_corrected.json').write_text(json.dumps(listing,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'현재_25편성_목록.txt').write_text('\n'.join([f'{i+1:02}. {r["pilot_name"]} / {r["unit_name"]}' for i,r in enumerate(remaining)]),encoding='utf-8-sig')
 print(json.dumps({k:v for k,v in record.items() if k!='edits'},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
