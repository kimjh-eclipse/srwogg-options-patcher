"""Audit the assembled release and public source without changing game files."""
from pathlib import Path
import ast, hashlib, json, re, subprocess, zipfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
REPO = WORK.parent / 'srwogg-options-patcher'

def main():
    completion = json.loads((HERE / 'release_completion.json').read_text(encoding='utf8'))
    metadata = json.loads((HERE / 'build_metadata.json').read_text(encoding='utf8'))
    assert completion['passed'] and completion['additional_battles'] == 13
    assert metadata['canonical_iso_sha256'] == 'c1ef60d889e52fe48d242228e084b44ffc8c683b6426f6acd7962ae47cbf6716'
    assert metadata['legacy_profiles'] <= 32768
    secret = re.compile(r'\bgh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|sk-proj-[A-Za-z0-9_-]{30,}')
    files = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=REPO, capture_output=True, text=True, check=True).stdout.rstrip('\0').split('\0')
    python_files = 0
    for name in files:
        f = REPO / name
        assert f.suffix.lower() not in {'.iso', '.chd', '.bin', '.elf', '.p2s', '.ps2', '.oggbak', '.exe'}
        if not f.is_file():
            continue
        if f.suffix.lower() in {'.py', '.cs', '.ps1', '.md', '.txt', '.json'}:
            text = f.read_text(encoding='utf-8-sig')
            assert not secret.search(text), 'Unexpected credential-shaped content in ' + name
            if f.suffix == '.py':
                ast.parse(text, filename=name)
                python_files += 1
            if f.suffix == '.json':
                json.loads(text)
    with zipfile.ZipFile(completion['zip']) as z:
        assert z.testzip() is None
        names = z.namelist()
        root = 'SRWOGG_Options_kr_v20261107.8/'
        sums = z.read(root + 'SHA256SUMS.txt').decode('utf8').splitlines()
        listed = set()
        for line in sums:
            digest, name = line.split('  ', 1)
            assert hashlib.sha256(z.read(root + name)).hexdigest() == digest, name
            listed.add(root + name)
        assert listed == set(names) - {root + 'SHA256SUMS.txt'}
        assert root + '시빌워7부작_대사와편성.md' in names
        assert not any('시빌워5부작' in n for n in names)
        assert sum(n.endswith('.png') for n in names) == 27
    links = 0
    for f in [REPO / 'README.md', REPO / 'tools/README.md']:
        for target in re.findall(r'\]\(([^)]+)\)', f.read_text(encoding='utf8')):
            if '://' not in target and not target.startswith('#'):
                assert (f.parent / target.split('#', 1)[0]).exists(), (f, target)
                links += 1
    diff = subprocess.run(['git', 'diff', '--check'], cwd=REPO, capture_output=True, text=True)
    assert diff.returncode == 0, diff.stdout
    result = dict(passed=True, source_files=len(files), python_syntax_files=python_files,
                  local_markdown_links=links, zip_members=len(names), zip_checksums=len(sums),
                  no_tracked_game_binary_or_credentials=True, git_diff_check=True)
    (HERE / 'source_distribution_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
