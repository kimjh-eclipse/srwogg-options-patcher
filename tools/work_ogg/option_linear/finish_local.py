from pathlib import Path
import json,subprocess,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;exe=ROOT/'release_v20261121/patcher/OGG_Options_Patcher.exe'
for image,name in [('SRWOGS_EX_K_TEST.ISO','canonical_verification.json'),('SRWOGS_EX_K.ISO','source_verification.json')]:
    r=subprocess.run([str(exe),'--verify',str(ROOT.parent/image),'--report',str(HERE/name)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,(r.stdout[-1600:],r.stderr[-1600:])
    result=json.loads((HERE/name).read_text(encoding='utf-8-sig'));assert result['passed']
    assert result['mask']==(8191 if name.startswith('canonical') else 0),result
    if name.startswith('canonical'):
        meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'));assert result['sha256']==meta['canonical_iso_sha256']
    print(image,result,flush=True)
# Confirm that the exact pre-update canonical input resolves as its old12-bit
# selection in the new legacy catalogue, without creating an ISO copy.
from pack_io import Pack,fingerprint
import zlib,base64
p=Pack(ROOT/'release_v20261121/patcher/OGG_options.bin');j=json.loads((ROOT/'linear_route_journal.json').read_text(encoding='utf8'))
with (ROOT.parent/'SRWOGS_EX_K_TEST.ISO').open('rb') as f:
    data=[]
    for at,original,base in p.regions:
        f.seek(at);b=bytearray(f.read(len(original)))
        for e in j['edits']:
            a=e['offset'];old=zlib.decompress(base64.b64decode(e['before_zlib_base64']));lo=max(at,a);hi=min(at+len(b),a+len(old))
            if lo<hi:b[lo-at:hi-at]=old[lo-a:hi-a]
        data.append(b)
assert p.legacy[fingerprint(p.regions,data)]==4095
(HERE/'migration_validation.json').write_text(json.dumps(dict(passed=True,exact_previous_canonical_recognized=True,previous_mask=4095,linear_defaults_off_on_import=True,older_public_releases=len(json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))['legacy_release_profiles']),extra_full_ISOs_created=0),indent=2),encoding='utf8')
print('Exact previous canonical selection recognized as 4095; 13 remains OFF on import.',flush=True)
