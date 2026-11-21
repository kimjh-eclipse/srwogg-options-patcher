from pathlib import Path
import json,subprocess,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parent/'srwogg-options-patcher'
meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))
source=(REPO/'src/OggOptionsPatcher.cs').read_text(encoding='utf8')
(HERE/'OggOptionsPatcher.cs').write_text(source,encoding='utf8')
generated=HERE/'OggOptionsPatcher.generated.cs'
generated.write_text(source.replace('__PACK_SHA__',meta['pack_sha256']),encoding='utf-8-sig')
exe=ROOT/('release_'+meta['version'])/'patcher/OGG_Options_Patcher.exe'
def run(args):
    r=subprocess.run([str(x) for x in args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,(r.stdout[-2000:],r.stderr[-2000:])
run([r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/target:winexe','/optimize+','/codepage:65001','/out:'+str(exe),'/reference:System.dll','/reference:System.Core.dll','/reference:System.Drawing.dll','/reference:System.Windows.Forms.dll',generated])
run([exe,'--preview',HERE/'ui_preview.png','--report',HERE/'ui_preview.json'])
print('Compiled conditional patcher; testing 8192 profiles.',flush=True)
run([exe,'--selftest','--report',HERE/'selftest.json'])
run([exe,'--verify',ROOT.parent/'SRWOGS_EX_K_TEST.ISO','--report',HERE/'canonical_verification.json'])
assert json.loads((HERE/'canonical_verification.json').read_text(encoding='utf-8-sig'))==dict(passed=True,mask=8191,sha256=meta['canonical_iso_sha256'])
(HERE/'selftest_attestation.json').write_text(json.dumps(dict(passed=True,pack_sha256=meta['pack_sha256'],executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),profiles=8192,format_version=2),indent=2),encoding='utf8')
print('8192-profile self-test and unchanged canonical verification passed.',flush=True)
