"""Apply validated description resources only to the canonical image, with rollback."""
from prepare_help_text import *
import os,ctypes,msvcrt,zlib,base64

def sha(f):
    f.seek(0)
    return hashlib.file_digest(f,'sha256').hexdigest()

def packed(b):
    return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def main():
    state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    p=json.loads((ROOT/'help_text_prepared.json').read_text(encoding='utf8'))
    assert p['ready_to_apply'] and not state.get('help_text_fix_applied')
    assert json.loads((ROOT/'help_text_validation.json').read_text(encoding='utf8'))['passed']
    assert state['current_sha256']==p['source_sha256'] and Path(state['canonical_iso'])==TARGET
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    k.CreateFileW.restype=ctypes.c_void_p
    handle=k.CreateFileW(str(TARGET),0xc0000000,0,None,3,0,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    with os.fdopen(msvcrt.open_osfhandle(handle,os.O_RDWR|os.O_BINARY),'r+b') as f:
        assert sha(f)==p['source_sha256']
        edits=[]
        for e in p['edits']:
            old=read(f,e['offset'],e['size']);new=(DEST/e['file']).read_bytes()
            assert hashlib.sha256(old).hexdigest()==e['before_sha256'] and len(new)==len(old)
            edits.append((e['offset'],old,new,e['label']))
        assert all(a[0]+len(a[1])<=b[0] for a,b in zip(edits,edits[1:]))
        journal=ROOT/'help_text_journal.json'
        report=dict(applied=False,before_sha256=p['source_sha256'],edits=[dict(offset=at,before_zlib_base64=packed(a),after_zlib_base64=packed(b),label=label) for at,a,b,label in edits])
        journal.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        try:
            for at,a,b,label in edits:
                assert read(f,at,len(a))==a;f.seek(at);assert f.write(b)==len(b)
            f.flush();os.fsync(f.fileno());digest=hashlib.sha256();inverse=hashlib.sha256();f.seek(0);pos=0
            for at,a,b,label in edits:
                while pos<at:
                    data=f.read(min(8<<20,at-pos));assert data;digest.update(data);inverse.update(data);pos+=len(data)
                assert f.read(len(b))==b;digest.update(b);inverse.update(a);pos+=len(b)
            while data:=f.read(8<<20):digest.update(data);inverse.update(data)
            assert inverse.hexdigest()==p['source_sha256']
            for arc in p['masters']:
                e,m=rawmaster(f,arc);assert m.b==(DEST/(arc+'.master')).read_bytes()
            after=digest.hexdigest()
        except BaseException:
            for at,a,b,label in edits:f.seek(at);f.write(a)
            f.flush();os.fsync(f.fileno());assert sha(f)==p['source_sha256'];raise
    report.update(applied=True,after_sha256=after,all_other_image_bytes_preserved=True,extra_full_ISOs_created=0)
    journal.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    state.update(current_sha256=after,last_edit_journal=str(journal),help_text_fix_applied=True,help_text_explanation_records=4568)
    (ROOT/'current_target.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='edits'},indent=2))

if __name__=='__main__':main()
