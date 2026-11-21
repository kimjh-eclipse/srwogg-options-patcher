"""Apply the validated all-options profile to the one authorized ISO."""
from pathlib import Path
import json,hashlib,zlib,base64,os,ctypes,msvcrt
ROOT=Path(__file__).resolve().parent;HERE=ROOT/'option_linear';DEST=ROOT/'analysis/linear_route'
TARGET=ROOT.parent/'SRWOGS_EX_K_TEST.ISO'

def digest(f):f.seek(0);return hashlib.file_digest(f,'sha256').hexdigest()
def packed(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def main():
    state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    plan=json.loads((ROOT/'linear_route_application.json').read_text(encoding='utf8'))
    metadata=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))
    assert json.loads((HERE/'linear_validation.json').read_text(encoding='utf8'))['passed']
    assert json.loads((HERE/'selftest.json').read_text(encoding='utf-8-sig'))==dict(passed=True,profiles=8192,checkboxes=13)
    attested=json.loads((HERE/'selftest_attestation.json').read_text(encoding='utf8'))
    assert attested['passed'] and attested['pack_sha256']==metadata['pack_sha256']
    assert attested['executable_sha256']==hashlib.sha256((ROOT/'release_v20261121/patcher/OGG_Options_Patcher.exe').read_bytes()).hexdigest()
    assert not state.get('linear_route_applied') and state['current_sha256']==plan['source_sha256']
    assert Path(state['canonical_iso']).resolve()==TARGET.resolve()
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    k.CreateFileW.restype=ctypes.c_void_p
    handle=k.CreateFileW(str(TARGET),0xc0000000,0,None,3,0,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    with os.fdopen(msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY),'r+b') as f:
        assert digest(f)==plan['source_sha256']
        edits=[]
        for e in plan['edits']:
            before=zlib.decompress(base64.b64decode(e['before_zlib_base64']));after=(DEST/e['file']).read_bytes()
            f.seek(e['offset']);assert f.read(e['size'])==before
            assert hashlib.sha256(after).hexdigest()==e['after_sha256'] and len(before)==len(after)
            edits.append((e['offset'],before,after))
        journal=ROOT/'linear_route_journal.json'
        report=dict(applied=False,before_sha256=plan['source_sha256'],edits=[dict(offset=at,before_zlib_base64=packed(a),after_zlib_base64=packed(b),label='13-option profile composition') for at,a,b in edits])
        journal.write_text(json.dumps(report,indent=2),encoding='utf8')
        try:
            for at,a,b in edits:f.seek(at);assert f.write(b)==len(b)
            f.flush();os.fsync(f.fileno());f.seek(0);position=0;after=hashlib.sha256();inverse=hashlib.sha256()
            for at,a,b in edits:
                while position<at:
                    data=f.read(min(8<<20,at-position));assert data;after.update(data);inverse.update(data);position+=len(data)
                assert f.read(len(b))==b;after.update(b);inverse.update(a);position+=len(b)
            while data:=f.read(8<<20):after.update(data);inverse.update(data)
            assert after.hexdigest()==metadata['canonical_iso_sha256'] and inverse.hexdigest()==plan['source_sha256']
        except BaseException:
            for at,a,b in edits:f.seek(at);f.write(a)
            f.flush();os.fsync(f.fileno());assert digest(f)==plan['source_sha256'];raise
    report.update(applied=True,after_sha256=metadata['canonical_iso_sha256'],all_other_image_bytes_preserved=True,extra_full_ISOs_created=0,profile_mask=8191)
    journal.write_text(json.dumps(report,indent=2),encoding='utf8')
    state.update(current_sha256=metadata['canonical_iso_sha256'],last_edit_journal=str(journal),linear_route_applied=True,linear_route_option=13,patcher_options=13,final_display_chapter=54,linear_route_order=[2009,2051,2010,2052,2011,2053,2012,2054,2013,2055])
    (ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
    with (ROOT/'AGENTS.md').open('a',encoding='utf8') as out:out.write('\n\n- ACTIVE 20261121: user authorized independent option13 for chronological ground/space10..14 and release+cafe update. linear_route_journal APPLIED, currentSHA '+metadata['canonical_iso_sha256']+'. 14 LOGO variants safely relocated/recycled, forward-only native skips, availability-only74targets, shared11/13/14 supply flags40,0..2, native Mironga57,3 fallback, display getter sums previously-zero Stag byte11, originalindices intact. Original30 maintenance threshold29->34 onlywhenoption13ON. 13options8192profiles/selftest/nativevalidation passed. No extraISO; originalreadonly. DO NOT rerun prepare/build/apply on the applied state. Finish exactpack verify, package/source/publicrelease and cafe51461 update. Browser TaskSpace5 active p1readonly article. User owns actualPCSX2playtesting.\n')
    print(json.dumps({k:v for k,v in report.items() if k!='edits'},indent=2),flush=True)

if __name__=='__main__':main()
