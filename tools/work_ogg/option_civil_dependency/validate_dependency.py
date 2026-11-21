"""Read-only native dependency and previous-profile preservation checks."""
from pathlib import Path
import sys,json,struct,bisect,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT/'option_linear'),str(ROOT)]
# runtime_helpers installs its historical search path, so select the new Pack
# before importing its native machine helpers.
from pack_io import Pack,Image,fingerprint
from runtime_helpers import rawmaster,ram,machine
from audit_story_layout import TARGET,loadarc
from inspect_iso import read,u32
from story_scripts_25 import records,command

def check():
    p=Pack(ROOT/'release_v20261121.1/patcher/OGG_options.bin')
    old=Pack(ROOT/'release_v20261121/patcher/OGG_options.bin')
    meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'))
    cp=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'))['effective_civil']
    assert p.version==2 and p.regions==old.regions and p.features==old.features
    assert p.count==old.count==13 and len(p.conditional)==1
    c=p.conditional[0];assert (c['require'],c['forbid'])==(2048,1)
    assert len(c['edits'])==7 and len(meta['dependency']['political_spans'])==5
    assert all(p.legacy[digest]==mask for digest,mask in old.profiles.items())
    assert all(p.legacy[digest]==mask for digest,mask in old.legacy.items())
    # The exact old 8192 selection signatures are accepted unchanged on import.
    reused=0
    for digest,mask in old.profiles.items():
        if not(mask&2048 and not mask&1):assert p.profiles[digest]==mask;reused+=1
    assert reused==6144
    masks=[0,1,2048,2049,4094,4095,4096,4097,6144,6145,8190,8191]
    noops=route_checks=display_checks=preserved_regions=0;graphs=[]
    for mask in masks:
        enabled=bool(mask&1 and mask&2048);omit=bool(mask&2048 and not mask&1)
        with Image(p,mask,TARGET) as f,Image(old,mask,TARGET) as prior:
            _,m=rawmaster(f,'SHARED.BIN');x=machine(ram(p,mask),m.b)
            # Real native chapter display getter, not a formula-only check.
            expected=36+(6 if mask&2048 else 0)+(7 if enabled else 0)+(5 if mask&4096 else 0)
            assert x.cpu.run(0x2705c0,[x.master,2,34])==expected
            display_checks+=1
            for span in meta['dependency']['political_spans']:
                bridge=next(b for b in cp['bridges'] if b['key']==span['key'])
                item=bridge['logo'];blob=read(f,item['offset'],item['size']);rows=records(blob)
                oldblob=read(prior,item['offset'],item['size'])
                if omit:
                    saved=bytes(x.cpu.mem[x.save:x.save+0x40000]);diff=bytes(x.cpu.mem[x.diff:x.diff+0x1300])
                    for i in range(span['start'],span['end']):
                        assert rows[i]==command(0x8a)
                        assert x.op(rows[i])==10;noops+=1
                    assert bytes(x.cpu.mem[x.save:x.save+len(saved)])==saved
                    assert bytes(x.cpu.mem[x.diff:x.diff+len(diff)])==diff
                else:assert blob==oldblob
                if bridge['key']==2040:
                    row=rows[bridge['route_row']]
                    dest=41 if enabled else 34
                    assert row[0]==0xa1 and row[2]==dest
                    x.cpu.write(x.diff+0xffc,40,4)
                    assert x.op(row)==14 and x.cpu.read(x.diff+0xffc,4)==dest
                    route_checks+=1
            # All other managed bytes must match the previous same-mask profile.
            actual=p.data(mask);previous=old.data(mask)
            if omit:
                from pack_io import setbytes
                for at,b in c['edits']:setbytes(old.regions,previous,at,b)
            assert all(a==b for a,b in zip(actual,previous));preserved_regions+=len(actual)
            assert fingerprint(p.regions,actual) in p.profiles
            if mask&4096:
                route={};blobs={}
                for keys,at,n in loadarc(f,14)[1]:
                    for key in keys:
                        if 2001<=key<=2056 or key==2070:blobs[key]=read(f,at,n)
                for key,blob in blobs.items():
                    targets={r[2]+2000 for r in records(blob) if r[0]==0xa1 and r[2]!=0xffffffff}
                    if len(targets)==1:route[key]=targets.pop()
                route[2008]=2009
                current=2001;visited=[]
                while current in route:
                    assert current not in visited
                    visited.append(current);current=route[current]
                if current not in visited and current in blobs:visited.append(current)
                assert len(visited)==expected and visited[-1]==2034,(mask,visited)
                for key in [2035,2036,2037,2038,2039,2040]:assert (key in visited)==bool(mask&2048)
                for key in [2041,2042,2043,2046,2047,2044,2045]:assert (key in visited)==enabled
                graphs.append(dict(mask=mask,battles=len(visited),civil_war=enabled,final_key=visited[-1]))
        print('Dependency profile',mask,'passed',flush=True)
    result=dict(passed=True,semantic_masks=masks,native_noop_commands=noops,native_next_stage_checks=route_checks,
                native_final_display_checks=display_checks,compared_managed_regions=preserved_regions,
                prior_profiles_recognized=8192,unchanged_profiles=6144,dependency_profiles=2048,
                all_enabled_profile_unchanged=True,political_blocks_removed=5,
                suppressed_temporary_roster_mutations=sum(s['roster_mutations'] for s in meta['dependency']['political_spans']),
                save_and_progress_unchanged_by_skipped_blocks=True,route_graphs=graphs,
                actual_world_AI_GPU_card_IO_tested=False,ISO_writes_performed=False)
    (HERE/'dependency_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':check()
