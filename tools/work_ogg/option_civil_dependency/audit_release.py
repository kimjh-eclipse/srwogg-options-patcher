from pathlib import Path
import json,hashlib,zipfile,subprocess,re,ast
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parent/'srwogg-options-patcher'
meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'));done=json.loads((HERE/'release_completion.json').read_text(encoding='utf8'));assert done['passed']
assert json.loads((REPO/'patch-data.json').read_text(encoding='utf8'))['sha256']==meta['pack_sha256']
secret=re.compile(r'\bgh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|sk-proj-[A-Za-z0-9_-]{30,}')
files=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=REPO,capture_output=True,text=True,check=True).stdout.rstrip('\0').split('\0');py=0
for name in files:
    p=REPO/name;assert p.suffix.lower() not in ['.iso','.chd','.bin','.elf','.exe','.ps2','.p2s','.oggbak']
    if not p.is_file():continue
    if p.suffix.lower() in ['.py','.cs','.ps1','.md','.txt','.json']:
        s=p.read_text(encoding='utf-8-sig');assert not secret.search(s),name
        if p.suffix=='.py':ast.parse(s,filename=name);py+=1
        if p.suffix=='.json':json.loads(s)
with zipfile.ZipFile(done['zip']) as z:
    assert z.testzip() is None;prefix='SRWOGG_Options_kr_v20261121.1/';names=z.namelist();sums=z.read(prefix+'SHA256SUMS.txt').decode('utf8').splitlines();listed=set()
    for line in sums:
        digest,name=line.split('  ',1);assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest;listed.add(prefix+name)
    assert listed==set(names)-{prefix+'SHA256SUMS.txt'}
    assert sum(n.endswith('.png') for n in names)==27
    assert prefix+'지상우주_교차진행.md' in names and prefix+'시빌워_의존조건.md' in names
    assert hashlib.sha256(z.read(prefix+'patcher/OGG_options.bin')).hexdigest()==meta['pack_sha256']
links=0
for p in [REPO/'README.md',REPO/'tools/README.md']:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
        if '://' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
assert subprocess.run(['git','diff','--check'],cwd=REPO,capture_output=True).returncode==0
# Compile the exact public C# input and compare it with the self-tested input;
# the same 8192-profile test need not be repeated for an identical source copy.
source=(REPO/'src/OggOptionsPatcher.cs').read_text(encoding='utf-8-sig').replace('__PACK_SHA__',meta['pack_sha256'])
assert source==(HERE/'OggOptionsPatcher.generated.cs').read_text(encoding='utf-8-sig')
dist=REPO/'dist';dist.mkdir(exist_ok=True);generated=dist/'OggOptionsPatcher.generated.cs';generated.write_text(source,encoding='utf-8-sig')
r=subprocess.run([r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/target:winexe','/optimize+','/codepage:65001','/out:'+str(dist/'OGG_Options_Patcher.exe'),'/reference:System.dll','/reference:System.Core.dll','/reference:System.Drawing.dll','/reference:System.Windows.Forms.dll',str(generated)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0,(r.stdout,r.stderr)
result=dict(passed=True,source_files=len(files),python_syntax_files=py,local_links=links,zip_members=len(names),zip_checksums=len(sums),no_game_dumps_or_credentials_in_source=True,public_source_compiles=True,compiler_input_identical_to_selftested_binary=True,git_diff_check=True)
(HERE/'source_distribution_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2),flush=True)
