from pathlib import Path
import subprocess,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))
source=ROOT/'option_help_text/OggOptionsPatcher.cs'
if not source.exists():source=ROOT.parent.parent/'src/OggOptionsPatcher.cs'
s=source.read_text(encoding='utf-8-sig')
s=s.replace('v20261110','v20261121').replace('if(count!=12)','if(count!=13)').replace('new CheckBox[12]','new CheckBox[13]')
s=s.replace('설명 오류는 공통 수정됩니다. 기존 ISO를 검사하고 같은 옵션으로 재적용하세요.','13번은 원본 9화 종료 전에 켜고 유지하세요. 양쪽 분기를 교차 진행합니다.')
s=s.replace('12번은 34화 종료 전 켜고','12번은 원본 34화 종료 전 켜고')
s=s.replace('v20261121: 정신기·특수능력·강화파츠·도감 설명을 공통 수정합니다.','v20261121: 13번 독립 옵션으로 지상·우주 루트를 모두 진행할 수 있습니다.')
s=s.replace('new Size(900,880)','new Size(900,960)').replace('new Size(800,820)','new Size(800,900)')
(HERE/'OggOptionsPatcher.cs').write_text(s,encoding='utf8')
generated=HERE/'OggOptionsPatcher.generated.cs';generated.write_text(s.replace('__PACK_SHA__',meta['pack_sha256']),encoding='utf-8-sig')
exe=ROOT/'release_v20261121/patcher/OGG_Options_Patcher.exe'
def run(args):
    r=subprocess.run([str(x) for x in args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,(r.stdout[-1500:],r.stderr[-1500:])
run([r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/target:winexe','/optimize+','/codepage:65001','/out:'+str(exe),'/reference:System.dll','/reference:System.Core.dll','/reference:System.Drawing.dll','/reference:System.Windows.Forms.dll',generated])
run([exe,'--preview',HERE/'ui_preview.png','--report',HERE/'ui_preview.json'])
print('Compiled 13-option patcher; testing 8192 profiles.',flush=True)
run([exe,'--selftest','--report',HERE/'selftest.json'])
import hashlib
(HERE/'selftest_attestation.json').write_text(json.dumps(dict(passed=True,pack_sha256=meta['pack_sha256'],executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),profiles=8192),indent=2),encoding='utf8')
print('8192-profile executable self-test passed.',flush=True)
