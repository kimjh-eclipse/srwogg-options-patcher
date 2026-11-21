from pathlib import Path
import json,hashlib,shutil,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;VERSION='v20261121.1';DIST=ROOT/('release_'+VERSION);PREV=ROOT/'release_v20261121'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=read(HERE/'build_metadata.json')
for s in meta['dependency']['political_spans']:s.pop('original_hex',None)
(HERE/'build_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
selftest=read(HERE/'selftest.json');native=read(HERE/'dependency_validation.json');canonical=read(HERE/'canonical_verification.json')
assert selftest['passed'] and native['passed'] and canonical['passed']
assert canonical['sha256']==meta['canonical_iso_sha256'] and canonical['mask']==8191
banner='> v20261121.1: 시빌워7편·정치 사전 장면5개는 **1·12번을 함께 켤 때만** 진행합니다. 12번만 켜면 국지전5편·베오울프전1편 후 본편 최종전으로 연결되며 총42화(13번 ON은47화)입니다. 아래 시빌워 포함 진행·화수 설명은 1·12번 ON 기준입니다. 자세한 조건은 `시빌워_의존조건.md`를 보세요.\n\n'
for source in PREV.glob('*.md'):
    (DIST/source.name).write_text(banner+source.read_text(encoding='utf8'),encoding='utf8')
shutil.copytree(PREV/'textures',DIST/'textures',dirs_exist_ok=True)
shutil.copy2(HERE/'dependency_details.md',DIST/'시빌워_의존조건.md')
intro='''슈퍼로봇대전 OG외전 13옵션 패처 v20261121.1

시빌워7부작과 정치 사전 장면5개는 1번 추가 아군과 12번 추가 전장을 함께 켤 때만 진행합니다.
12번만 켜면 국지전5편+베오울프전1편을 진행한 뒤 본편 라그나로크로 이어집니다.
정치 사전 장면과 시빌워용 임시 부대 분리도 함께 건너뜁니다. 1번을 자동으로 켜지 않습니다.

전체 화수
12 OFF / 13 OFF: 36화 (1번 무관)
12 OFF / 13 ON: 41화 (1번 무관)
1 OFF / 12 ON / 13 OFF: 42화
1 OFF / 12 ON / 13 ON: 47화
1 ON / 12 ON / 13 OFF: 49화
1 ON / 12 ON / 13 ON: 54화

적용 방법
1. PCSX2 완전 종료 → ZIP 압축 해제 → 같은 ZIP의 EXE와 BIN을 같은 폴더에 둡니다.
2. 패처 실행 → 기존 ISO 검사 → 기존 선택 확인 → 원하는 옵션 선택 → 패치 적용.
3. 게임을 완전히 새로 부팅하고 일반 세이브로 진행합니다.
4. 1번은 새 게임부터 합류 시나리오를 진행할 때 선택하고 유지합니다. 지나간 합류를 소급 실행하지 않습니다.
5. 12번은 원본34화 종료 전부터, 13번은 원본9화 종료 전부터 유지합니다.
6. 이미 시빌워에 진입한 상태에서 1·12번을 바꾸지 마세요. 지난 장면이나 임시 편성 분리를 소급 복구하지 않습니다.
7. 1번 OFF 사용자는 정치 사전 장면 시작 전의 일반 세이브부터 새 버전을 사용해 주세요.

선택 기능
'''
for x in meta['options']:intro+=str(x['bit']+1)+'. '+x['name']+'\n   '+x['description']+'\n'
intro+='''
유지되는 내용
기존 추가25편성·합류와 후속 대사·기체/정신기/무장 밸런스·선택 보상·숨겨진 요소·공통 설명 수정·지상/우주 교차 진행을 유지합니다.
SP 소모1 옵션은 없습니다. 각 기능은 해당 체크박스에 따릅니다.
1·12번을 모두 켠 게임 데이터는 이전 버전과 같습니다.

선택 HD자료
textures/SLPS-25836/replacements/beowulf_mk3의 PNG27개만 포함합니다.
PCSX2 텍스처 검색 폴더에 합쳐 설치하고 Load Textures를 켜세요. 전체 HD팩은 포함하지 않습니다.

공식 한글패치
제작자: https://github.com/z3oo3z/PS2-SRWOGG-KPatch
공식 릴리즈: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG
직접 다운로드: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z
기준 버전 v1.4.3s. 공식 한글판 MD5 a5254cd5d4deabc57e03a3dcbb6a88d7.

검증 범위
13옵션8,192개 조합과 이전 버전 인식, 내부 명령으로 시빌워 생략·정치 사전 장면 생략·임시 편성 보존·다음 화 처리·화수 표시를 확인했습니다.
실제 PCSX2 전편 플레이·AI·렌더링·메모리카드 입출력을 모두 확인한 것은 아닙니다. 플레이 테스트는 사용자가 진행합니다.
게임 ISO·BIOS·세이브·원본 대사 덤프는 배포하지 않습니다.
'''
(DIST/'읽어주세요.txt').write_text(intro,encoding='utf-8-sig')
validation=dict(passed=True,profile_selftest=selftest,dependency=native,canonical=canonical,
                live_playthrough=False,playtesting_owner='user',prior_validation=read(PREV/'검증결과.json'))
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
info=dict(meta);info.update(prerelease=False,experimental=False,additional_battles=13,
    additional_battles_without_cast=6,total_battles_all_options=54,
    executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'),optional_HD_files=27)
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
assert sum(p.suffix=='.png' for p in files)==27
(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf8')
zip_path=ROOT/('SRWOGG_Options_kr_'+VERSION+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(DIST.rglob('*')):
        if p.is_file():z.write(p,'SRWOGG_Options_kr_'+VERSION+'/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None and not any(Path(n).suffix.lower() in ['.iso','.ps2','.p2s','.oggbak'] for n in z.namelist())
result=dict(passed=True,version=VERSION,zip=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),
            canonical_sha256=canonical['sha256'],canonical_bytes_changed=False,options=13,verified_profiles=8192,
            additional_battles=13,additional_battles_without_cast=6,total_battles_all_options=54,
            experimental=False,live_playthrough=False,optional_HD_files=27,extra_full_ISOs_created=0)
(HERE/'release_completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,indent=2),flush=True)
