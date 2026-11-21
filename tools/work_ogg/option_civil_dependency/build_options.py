"""Add a cast dependency to civil war without changing the all-enabled ISO.

Format 2 extends OGGOPT01 with conditional edits after the ordinary features.
Conditions are applied last; previous format-1 profiles remain valid inputs.
"""
from pathlib import Path
import sys, json, struct, zlib, hashlib
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT/'option_linear'),str(ROOT)]
from pack_io import Pack, Image, setbytes, fingerprint
from inspect_iso import read
from audit_story_layout import TARGET
from regional_five_policy import stage_base
from catalog import Master
from story_scripts_25 import records, command

VERSION='v20261121.1'
DIST=ROOT/('release_'+VERSION)
PREVIOUS=ROOT/'release_v20261121/patcher/OGG_options.bin'

def deflate(b):
    c=zlib.compressobj(9,zlib.DEFLATED,-15)
    return c.compress(b)+c.flush()

def build():
    p=Pack(PREVIOUS)
    assert p.count==13 and not p.conditional
    cp=json.loads((ROOT/'civil_guard_prepared.json').read_text(encoding='utf8'))['effective_civil']
    edits=[]; spans=[]
    with Image(p,2048,TARGET) as image:
        for bridge in cp['bridges']:
            item=bridge['logo']; blob=read(image,item['offset'],item['size']); rs=records(blob)
            assert list(bridge['phases'])==['post']
            start,end=[bridge['phases']['post'][x] for x in ['start','end']]
            assert rs[end][0]==0xa1 and start<end
            # This entire newly appended political block includes dialogue AND
            # the temporary roster split. The ordinary operation stays intact.
            at=item['offset']+struct.unpack_from('<I',blob,44)[0]+start*96
            noop=struct.pack('<24I',*command(0x8a))
            edits.append((at,noop*(end-start)))
            spans.append(dict(key=bridge['key'],start=start,end=end,offset=at,rows=end-start,
                              roster_mutations=sum(r[0]==0x4a for r in rs[start:end])))
            if bridge['key']==2040:
                row=bridge['route_row']; assert row==end and rs[row][0]==0xa1 and rs[row][2]==41
                route_at=item['offset']+struct.unpack_from('<I',blob,44)[0]+row*96+8
                edits.append((route_at,struct.pack('<I',34)))
        from runtime_helpers import rawmaster
        final_numbers=[]
        for name in ['SHARED.BIN','IM.BIN']:
            e,m=rawmaster(image,name)
            counts=struct.unpack_from('<3H',m.b,m.tables['Stag'][0]+12)
            if counts[2]<=34:continue
            sb=stage_base(m)
            at=e['offset']+sb+34*12+6
            assert read(image,at,1)==bytes([49])
            edits.append((at,bytes([42]))); final_numbers.append(at)
    edits.sort()
    for (a,b),(c,d) in zip(edits,edits[1:]):assert a+len(b)<=c
    conditions=[dict(require=2048,forbid=1,edits=edits)]
    options=list(p.options)
    options[11]=('추가 전장 6편·시빌워 7편(1번 필요)',
                 '12번만: 국지전5+베오울프1. 1·12번 함께: 정치 사전 장면+시빌워7 추가')
    options[12]=(options[12][0],'원본 9화 종료 전 켜고 유지. 기본41화 / 12번만47화 / 1·12번 함께54화')
    # A temporary in-memory Pack object composes the exact format-2 semantics.
    p.conditional=conditions
    profiles=[]
    # Hash unchanged regional combinations once and reuse the previous catalog
    # for unaffected profiles.
    starts=p.starts
    import bisect
    regional=[{} for _ in p.regions];conditional=[[] for _ in p.regions]
    for bit,es in enumerate(p.features):
        for at,b in es:
            i=bisect.bisect_right(starts,at)-1
            assert at+len(b)<=starts[i]+len(p.regions[i][2])
            regional[i].setdefault(bit,[]).append((at-starts[i],b))
    for at,b in edits:
        i=bisect.bisect_right(starts,at)-1
        assert at+len(b)<=starts[i]+len(p.regions[i][2])
        conditional[i].append((at-starts[i],b))
    caches=[{} for _ in p.regions];bits=[sum(1<<bit for bit in x) for x in regional]
    old_by_mask={mask:h for h,mask in p.profiles.items()}
    for mask in range(8192):
        if mask&2048 and not mask&1:
            # Per-region cache keeps full-catalog hashing bounded.
            h=hashlib.sha256()
            for i,(at,o,b) in enumerate(p.regions):
                key=mask&bits[i]
                if key not in caches[i]:
                    value=bytearray(b)
                    for bit,es in regional[i].items():
                        if mask&(1<<bit):
                            for rel,edit in es:value[rel:rel+len(edit)]=edit
                    for rel,edit in conditional[i]:value[rel:rel+len(edit)]=edit
                    caches[i][key]=hashlib.sha256(value).digest()
                h.update(struct.pack('<QI',at,len(b)));h.update(caches[i][key])
            profiles.append(h.digest())
        else: profiles.append(old_by_mask[mask])
        if mask%1024==0:print('Profile',mask,flush=True)
    assert len(set(profiles))==8192
    legacy=dict(p.legacy)
    legacy.update({digest:mask for digest,mask in p.profiles.items()})
    assert len(legacy)<=65536
    target=DIST/'patcher/OGG_options.bin';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('wb') as f:
        def w(fmt,*v):f.write(struct.pack(fmt,*v))
        def blob(b):w('<I',len(b));f.write(b)
        def write_edits(es):
            w('<I',len(es))
            for at,b in es:w('<QI',at,len(b));f.write(b)
        f.write(b'OGGOPT01');w('<IQ',2,p.size);f.write(p.source_sha);w('<I',13)
        for name,desc in options:blob(name.encode('utf8'));blob(desc.encode('utf8'))
        w('<I',len(p.regions))
        for at,o,b in p.regions:w('<QI',at,len(o));blob(deflate(o));blob(deflate(b))
        for es in p.features:write_edits(es)
        w('<I',len(conditions))
        for c in conditions:w('<II',c['require'],c['forbid']);write_edits(c['edits'])
        w('<I',len(profiles))
        for mask,h in enumerate(profiles):w('<I',mask);f.write(h)
        f.write(p.source_fingerprint);w('<I',len(legacy))
        for digest,mask in legacy.items():f.write(digest);w('<I',mask)
    state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    meta=dict(version=VERSION,format_version=2,options=[dict(bit=i,name=n,description=d) for i,(n,d) in enumerate(options)],
              profile_count=8192,pack_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),pack_size=target.stat().st_size,
              canonical_iso_sha256=state['current_sha256'],iso_size=p.size,original_iso_sha256=p.source_sha.hex(),
              managed_ranges=len(p.regions),managed_bytes=sum(len(b) for at,o,b in p.regions),legacy_profiles=len(legacy),
              dependency=dict(require=2048,forbid=1,political_spans=spans,route_operand=route_at,final_display_offsets=final_numbers,
                              additional_battles_without_cast=6,additional_battles_with_cast=13),
              defaults=0,canonical_bytes_changed=False,extra_full_ISOs_created=0,live_playthrough=False)
    (HERE/'build_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in meta.items() if k not in ['options','dependency']},indent=2),flush=True)

if __name__=='__main__':build()
