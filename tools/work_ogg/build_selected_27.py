"""Build only the 27 lineups approved after the user's explicit exclusions."""
from build_all_cast import *
from inspect_ingram_text import texts
import subprocess

TARGET=ROOT/'SRWOGG_27_CH1.iso'
PATCH=ROOT/'OGG_27_CH1.xdelta'

def selection():
 d=json.loads((OUT/'missing_cast_corrected.json').read_text(encoding='utf-8'))
 chosen=d['ship_filter']['cast'];assert len(chosen)==27
 forbidden={'다이테츠','리','리리','마이어','반','아들러','한스','쿠엘보'}
 rows=[]
 for i,v in enumerate(chosen):
  assert v['pilot'] not in forbidden
  rows.append(dict(unit=v['unit_key'],pilot=v['pilot_key'],unit_name=v['unit'],pilot_name=v['pilot'],new_key=0x700+i))
  if v['pilot']=='잉그램':rows[-1]['pilot']=0x3e
 assert len({r['pilot_name'] for r in rows})==27
 return rows

def verify(f,rows):
 bodykeys={k for e in arc('BATTLE.BIN.1')['entries'] if e['size'] for k in e['keys']}
 for name in ['SHARED.BIN','IM.BIN']:
  e=arc(name+'.3')['entries'][0];m=Master(read(f,e['offset'],e['size']))
  for r in rows:
   ui=u16(m.b,m.tables['UTbl'][0]+12+r['new_key']*2);pi=u16(m.b,m.tables['PTbl'][0]+12+r['new_key']*2)
   assert ui<m.tables['Unit'][2] and pi<m.tables['Plot'][2]
   u=m.b[m.tables['Unit'][0]+12+ui*100:m.tables['Unit'][0]+12+(ui+1)*100]
   pilot=m.b[m.tables['Plot'][0]+12+pi*148:m.tables['Plot'][0]+12+(pi+1)*148]
   assert m.text(u16(u,12))==r['unit_name'] and m.text(u16(pilot,4))==r['pilot_name']
   assert u16(u,0x44) in bodykeys
   for w in struct.unpack_from('<16H',u,0x24):
    if w!=65535:assert w<m.tables['WTbl'][2] and u16(m.b,m.tables['WTbl'][0]+12+w*2)!=65535
 for slot,magic in [(13,b'UNTD'),(14,b'LOGO')]:
  a=arc('MAP.BIN.'+str(slot));e=next(e for e in a['entries'] if 2001 in e['keys']);off,n=struct.unpack('<II',read(f,a['directory']+8+e['index']*8,8));b=read(f,a['directory']+off,n);assert b[:4]==magic
  if slot==13:
   assert u32(b,40)==38
   coords=[]
   for i,r in enumerate(rows):
    q=44+(11+i)*336;assert u32(b,q)==u32(b,q+32)==r['new_key'];assert u32(b,q+4)==32 and u32(b,q+8)==0
    coords.append((u32(b,q+16),u32(b,q+20)))
   assert len(set(coords))==27
  else:assert list(struct.unpack_from('<24I',b,u32(b,0x2c)+26*96))==command(0xca,32,0xffffffff)
 # Re-open the actual rebuilt voice directory and compare every audio ID.
 root=arc('BATTLE.BIN');outer=root['entries'][5];span=u32(read(f,root['directory']+8+5*8+4,4));voices=lice(f,outer['offset'],span)
 original=arc('BATTLE.BIN.5');lookup={k:e for e in original['entries'] for k in e['keys']}
 with SOURCE.open('rb') as src:
  for r in rows:
   e=next(e for e in voices['entries'] if r['new_key'] in e['keys']);new=read(f,e['offset'],e['size']);e=lookup[r['pilot']];old=read(src,e['offset'],e['size'])
   a,b=texts(old),texts(new);assert len(a)==len(b)
   assert [x['voice'] for x in a]==[x['voice'] for x in b]
   if r['pilot_name']=='잉그램':assert all(not any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in x['kr']) for x in b)
 return dict(approved_lineups=27,excluded_lineups_absent=True,existing_allies=3,total_initial_allies=30,both_master_name_and_key_checks=True,body_and_weapon_references_valid=True,all_27_placements_verified=True,native_deployment_command_verified=True,all_original_voice_ids_preserved=True,ingram_korean_subtitles_verified=True,live_playthrough_verified=False)

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--resume-unverified-output',action='store_true');args=ap.parse_args()
 rows=selection();assert (not TARGET.exists() or args.resume_unverified_output) and not PATCH.exists()
 if args.resume_unverified_output:assert TARGET.stat().st_size==SOURCE.stat().st_size and not (ROOT/'manifest_selected_27.json').exists()
 print('Checking original ISO...',flush=True)
 with SOURCE.open('rb') as f:
  assert hashlib.file_digest(f,'sha256').hexdigest()==EXPECTED
  p=make_plan(f,rows)
 assert all(not r['silent'] for r in rows)
 print('Creating separate 27-lineup ISO...',flush=True)
 # Always recopy after an interrupted/failed build: earlier clone allocations
 # may occupy different padding ranges and must not survive a rebuild.
 shutil.copyfile(SOURCE,TARGET)
 with TARGET.open('r+b') as f:
  for o,a,b,label in p.edits:
   assert read(f,o,len(a))==a
   f.seek(o);f.write(b)
  f.flush();os.fsync(f.fileno());validation=verify(f,rows)
 print('Data/voice/placement checks passed. Checking complete image...',flush=True)
 inverse=hashlib.sha256();digest=hashlib.sha256();pos=0
 with TARGET.open('rb') as f:
  for o,a,b,label in p.edits:
   while pos<o:
    raw=f.read(min(4<<20,o-pos));assert raw;inverse.update(raw);digest.update(raw);pos+=len(raw)
   assert f.read(len(b))==b;inverse.update(a);digest.update(b);pos+=len(b)
  while raw:=f.read(4<<20):inverse.update(raw);digest.update(raw)
 assert inverse.hexdigest()==EXPECTED
 report=dict(source=str(SOURCE),target=str(TARGET),patch=str(PATCH),source_sha256=EXPECTED,target_sha256=digest.hexdigest(),all_unrelated_bytes_preserved=True,validation=validation,cast=rows,edits=[dict(offset=o,size=len(b),label=l,sha256=hashlib.sha256(b).hexdigest()) for o,a,b,l in p.edits])
 (ROOT/'manifest_selected_27.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 text=['OG외전 1화 27편성 등장 시험판','',f'실행 ISO: {TARGET.name}',f'xdelta 패치: {PATCH.name}','패치 기준: 원본 SRWOGS_EX_K.ISO (이전 시험 ISO가 아님)',f'원본 SHA256: {EXPECTED}',f'수정 ISO SHA256: {digest.hexdigest()}','','추가 27기 + 기존 아군 3기 = 최초 아군 30기。','기함/전함 편성과 쿠엘보 제외。 정신기 SP1, 잉그램 한글 자막 수정 포함。','기존 파일과 세이브는 수정하지 않음。 새 ISO로 부팅하여 새 게임을 시작。','강제저장에는 이전 배치와 데이터가 남을 수 있으므로 시험에 사용하지 말 것。','기체/파일럿 이름, 전투 그래픽/무기 참조, 27개 배치, 등장 명령, 음성 번호 보존 검사 통과。','실제 화면에서 27기 등장, 모든 무기 연출, 이후 본편 진행은 아직 미검증。','잉그램 외 추가 인물의 미번역 전투 자막이 남을 수 있음。','']
 text += [f'{i+1:02}. {r["pilot_name"]} / {r["unit_name"]}' for i,r in enumerate(rows)]
 (ROOT/'27편성_시험판_안내.txt').write_text('\n'.join(text),encoding='utf-8-sig')
 print('Creating xdelta patch...',flush=True)
 subprocess.run([str(ROOT.parent/'xdelta.exe'),'-e','-s',str(SOURCE),str(TARGET),str(PATCH)],check=True)
 print('Verifying xdelta decode checksums...',flush=True)
 subprocess.run([str(ROOT.parent/'xdelta.exe'),'-d','-J','-s',str(SOURCE),str(PATCH)],check=True)
 report['xdelta_decode_verified']=True;report['patch_size']=PATCH.stat().st_size
 (ROOT/'manifest_selected_27.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ('cast','edits')},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
