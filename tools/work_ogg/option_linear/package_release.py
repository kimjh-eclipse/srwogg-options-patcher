from pathlib import Path
import json,hashlib,shutil,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;VERSION='v20261121';DIST=ROOT/('release_'+VERSION)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def report(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))
meta=report('build_metadata.json');assert report('selftest.json')['passed'] and report('linear_validation.json')['passed'] and report('migration_validation.json')['passed']
canonical=report('canonical_verification.json');assert canonical['sha256']==meta['canonical_iso_sha256'] and canonical['mask']==8191
previous=ROOT/'release_v20261110'
for source in previous.glob('*.md'):
    text=source.read_text(encoding='utf8')
    note='> 화수 안내: 기존 추가 전장 안내의 표시 화수는 13번 OFF 기준입니다. 13번 ON에서는 원본 15화 이후 +5이며, 원본 34화는 표시 39화·베오울프전은 46화·시빌워는 47~53화·최종전은 54화입니다. 자세한 내용은 `지상우주_교차진행.md`를 보세요.\n\n'
    (DIST/source.name).write_text(note+text,encoding='utf8')
shutil.copy2(HERE/'linear_route_details.md',DIST/'지상우주_교차진행.md')
shutil.copytree(previous/'textures',DIST/'textures',dirs_exist_ok=True)
intro='''슈퍼로봇대전 OG외전 13옵션 패처 v20261121

13번 「지상·우주 루트 교차 진행」을 추가했습니다.
원본 9화 → 지상10 → 우주10 → 지상11 → 우주11 → … → 지상14 → 우주14 → 원본15화.
13번을 끄면 원래 분기 선택으로 진행합니다. 기존 1~12번 선택과 설명 오류 수정을 유지합니다.
기체·파일럿을 새로 지급하지 않고 각 부대의 사용 가능 상태를 정리하며, 육성·PP·격추수·개조·장비를 보존합니다.
양쪽에 공통인 같은 보급 이벤트는 한 번만 지급하고, 각 전투의 정상 보상은 유지합니다.
미선택 부대용 자동 EXP·격추수·PP 성장 보정은 교차 진행에서 제외하여 실제 전투 성장과 겹치지 않게 했습니다.

적용 방법
1. 공식 한글패치 v1.4.3s가 적용된 ISO를 준비합니다.
2. PCSX2를 완전히 종료하고 ZIP을 풉니다. patcher 폴더의 EXE와 BIN을 같은 폴더에 둡니다.
3. 패처 실행 → ISO 선택 → 검사 → 기존 옵션 확인 → 원하는 옵션 선택 → 패치 적용.
4. 양쪽 분기를 모두 진행하려면 13번을 켜세요. 원본 9화 종료 이전의 일반 세이브부터 적용하고 최종전까지 유지하세요.
5. 게임을 완전히 새로 부팅하고 일반 세이브를 사용하세요. 이전 상태 저장에는 수정 전 자료가 남습니다.

기존 세이브와 옵션
- 이전 버전의 선택값을 인식합니다. 새 13번은 자동으로 켜지지 않습니다.
- 이미 지나간 합류·보상·전장 진입 이벤트를 소급 실행하지 않습니다.
- 추가 25편성 시나리오를 처음 사용하는 경우는 기존과 같이 새 게임부터 1번을 유지하세요.
- 12번 추가 전장은 원본 34화(13번 ON 시 표시 39화) 종료 전부터 모든 추가 전장 종료까지 유지하세요.
- 13번을 진행 중에 바꾸지 마세요. 부대 전환과 표시 화수·후반 정비 시점이 함께 바뀝니다.

전체 화수
12 OFF / 13 OFF: 36화
12 OFF / 13 ON: 41화
12 ON / 13 OFF: 49화
12 ON / 13 ON: 54화

12·13번 ON 진행: 원본34화(표시39) → 국지전40~44 → 원본35화(표시45)
→ 베오울프46 → 시빌워47~53 → 라그나로크54.
후반 정비는 원본30화, 교차 진행에서는 표시35화부터입니다.
동봉된 기존 전장 가이드의 화수는 13번 OFF 기준이며, 자세한 대응표는 지상우주_교차진행.md에 있습니다.

선택 기능
'''
for x in meta['options']:intro+=str(x['bit']+1)+'. '+x['name']+'\n   '+x['description']+'\n'
intro+='''
설명 수정
정신기·특수능력·강화파츠·도감 설명 연결 수정은 공통 적용입니다. 이 수정만을 위해 새 게임을 시작할 필요는 없습니다.
정신기 SP 소모 1 옵션은 없습니다. 기존 밸런스·추가25편성·추가 전장13편을 유지합니다.

선택 HD자료
textures/SLPS-25836/replacements/beowulf_mk3의 PNG27개만 포함합니다.
PCSX2 텍스처 검색 폴더에 합쳐 설치하고 Load Textures를 켜세요. 전체 HD팩은 포함하지 않습니다.

공식 한글패치
제작자: https://github.com/z3oo3z/PS2-SRWOGG-KPatch
공식 릴리즈: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/tag/SRWOGG
직접 다운로드: https://github.com/z3oo3z/PS2-SRWOGG-KPatch/releases/download/SRWOGG/OGGv1.4.3sta.7z
기준 버전 v1.4.3s. 공식 한글판 MD5 a5254cd5d4deabc57e03a3dcbb6a88d7.

검증 범위
13옵션 8192조합, 이전 공개 버전 인식, 게임 내부의 전환·편성 활성·보상 중복 방지·화수 조회·후반 정비를 검사했습니다.
원래 대사·기체·파일럿·무장·설명 정보와 전장 배치의 보존을 비교했습니다.
실제 PCSX2 전편 플레이·AI·화면·메모리카드 입출력을 모두 확인한 것은 아닙니다. 플레이 테스트는 사용자가 진행합니다.
게임 ISO·BIOS·세이브·원본 대사 덤프는 배포하지 않습니다.
'''
(DIST/'읽어주세요.txt').write_text(intro,encoding='utf-8-sig')
validation=dict(passed=True,live_playthrough=False,playtesting_owner='user',profile_selftest=report('selftest.json'),linear_route=report('linear_validation.json'),migration=report('migration_validation.json'),canonical=canonical,readonly_source=report('source_verification.json'),previous_features_preserved=True,prior_validation=json.loads((previous/'검증결과.json').read_text(encoding='utf8')))
(DIST/'검증결과.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
info=dict(meta);info.update(prerelease=False,experimental=False,additional_battles=13,total_battles_all_options=54,executable_sha256=sha(DIST/'patcher/OGG_Options_Patcher.exe'),optional_HD_files=27)
(DIST/'PATCH_INFO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
assert sum(p.suffix=='.png' for p in files)==27
(DIST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DIST).as_posix()+'\n' for p in files),encoding='utf8')
zip_path=ROOT/('SRWOGG_Options_kr_'+VERSION+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(DIST.rglob('*')):
        if p.is_file():z.write(p,'SRWOGG_Options_kr_'+VERSION+'/'+p.relative_to(DIST).as_posix())
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None and not any(Path(n).suffix.lower() in ['.iso','.p2s','.ps2','.oggbak'] for n in z.namelist())
result=dict(passed=True,version=VERSION,zip=str(zip_path),zip_bytes=zip_path.stat().st_size,zip_sha256=sha(zip_path),canonical_sha256=meta['canonical_iso_sha256'],options=13,verified_profiles=8192,additional_battles=13,total_battles_all_options=54,experimental=False,live_playthrough=False,optional_HD_files=27,extra_full_ISOs_created=0)
(HERE/'release_completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
