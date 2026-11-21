"""Extend the last verified pack with an independent branch traversal option."""
from pathlib import Path
import sys,json,struct,hashlib,zlib,bisect,io,base64
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT),str(ROOT/'upstream_base')]
from pack_io import Pack,Image,setbytes,fingerprint
from source_image import source_image,DATA as BASE_INFO
from inspect_iso import SOURCE,read
from audit_story_layout import TARGET
VERSION='v20261121'
DIST=ROOT/('release_'+VERSION)
PREVIOUS=ROOT/'release_v20261110/patcher/OGG_options.bin'
DEST=ROOT/'analysis/linear_route'

def bytesof(e):return bytes.fromhex(e['hex']) if 'hex' in e else (DEST/e['file']).read_bytes()

def merge(spans):
    out=[]
    for lo,hi in sorted(spans):
        if out and lo<=out[-1][1]:out[-1]=(out[-1][0],max(hi,out[-1][1]))
        else:out.append((lo,hi))
    return out

def signer(regions,base,features):
    starts=[r[0] for r in regions];dirty={bisect.bisect_right(starts,at)-1 for es in features for at,b in es}
    fixed={i:hashlib.sha256(b).digest() for i,b in enumerate(base) if i not in dirty}
    def sign(data):
        h=hashlib.sha256()
        for i,((at,*unused),b) in enumerate(zip(regions,data)):
            h.update(struct.pack('<QI',at,len(b)));h.update(fixed[i] if i in fixed else hashlib.sha256(b).digest())
        return h.digest()
    return sign,dirty

def compose(regions,base,features,mask,dirty=None):
    data=[bytearray(b) if dirty is None or i in dirty else b for i,b in enumerate(base)]
    for bit,es in enumerate(features):
        if mask&(1<<bit):
            for at,b in es:setbytes(regions,data,at,b)
    return data

def catalog(regions,base,features):
    """Hash each distinct regional combination once; preserve exact format."""
    starts=[r[0] for r in regions];affected=[{} for _ in regions]
    for bit,es in enumerate(features):
        for at,b in es:
            i=bisect.bisect_right(starts,at)-1
            assert at+len(b)<=starts[i]+len(base[i])
            affected[i].setdefault(bit,[]).append((at-starts[i],b))
    lookup=[]
    for i,edits in enumerate(affected):
        bits=sorted(edits);bitmask=sum(1<<bit for bit in bits);hashes={}
        for local in range(1<<len(bits)):
            mask=sum(1<<bit for j,bit in enumerate(bits) if local&(1<<j))
            b=bytearray(base[i])
            for bit in bits:
                if mask&(1<<bit):
                    for rel,value in edits[bit]:b[rel:rel+len(value)]=value
            hashes[mask]=hashlib.sha256(b).digest()
        lookup.append((struct.pack('<QI',starts[i],len(base[i])),bitmask,hashes))
    for mask in range(1<<len(features)):
        h=hashlib.sha256()
        for prefix,bitmask,hashes in lookup:h.update(prefix);h.update(hashes[mask&bitmask])
        yield mask,h.digest()

def build():
    prepared=json.loads((ROOT/'linear_route_prepared.json').read_text(encoding='utf8'))
    state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    assert not state.get('linear_route_applied') and state['current_sha256']==prepared['source_sha256'],'Historical authoring: do not rebuild against the applied image'
    old=Pack(PREVIOUS);resources=prepared['resources'];directory=prepared['directory']
    def relocate(at,b):
        # Native script row indices and offsets within the command area do not
        # move. Only resource directory targets and sizes need rebasing.
        if directory+8<=at<directory+8+4096 and len(b)==8:
            rel,n=struct.unpack('<II',b);target=directory+rel
            v=next((v for v in resources if v['old_offset']==target),None)
            if v:return at,struct.pack('<II',v['offset']-directory,v['size'])
        touched=[v for v in resources if at<v['old_offset']+v['old_size'] and at+len(b)>v['old_offset']]
        if touched:
            assert len(touched)==1;v=touched[0]
            assert v['old_offset']<=at and at+len(b)<=v['old_offset']+v['old_size']
            assert at-v['old_offset']>=v['co'],'Only existing command operands may be remapped'
            return v['offset']+at-v['old_offset'],b
        return at,b
    features=[]
    with Image(old,0,TARGET) as zero:
        for es in old.features:
            minimal=[]
            for at,b in es:
                newat,b=relocate(at,b);za,zb=relocate(at,read(zero,at,len(b)))
                assert newat==za and len(b)==len(zb)
                start=None
                for i,(x,y) in enumerate(zip(zb,b)):
                    if x!=y and start is None:start=i
                    if x==y and start is not None:minimal.append((newat+start,b[start:i]));start=None
                if start is not None:minimal.append((newat+start,b[start:]))
            copies=[]
            for at,b in minimal:
                for v in resources:
                    for cp in v['copies']:
                        start=v['offset']+v['co']+cp['source_start']*96;end=start+cp['count']*96
                        if at<end and at+len(b)>start:
                            lo=max(at,start);hi=min(at+len(b),end)
                            copies.append((v['offset']+v['co']+cp['dest_start']*96+lo-start,b[lo-at:hi-at]))
            features.append(minimal+copies)
    features.append([(e['offset'],bytesof(e)) for e in prepared['on']])
    flat=sorted((at,at+len(b),bit) for bit,es in enumerate(features) for at,b in es)
    for a,b in zip(flat,flat[1:]):assert a[1]<=b[0],('Feature overlap',a,b)
    spans=[(at,at+len(o)) for at,o,b in old.regions]
    spans.extend((e['offset']//4096*4096,(e['offset']+e['size']+4095)//4096*4096) for e in prepared['edits'])
    regions=[]
    with source_image() as official,Image(old,0,TARGET) as zero,TARGET.open('rb') as current:
        for lo,hi in merge(spans):regions.append((lo,read(official,lo,hi-lo),read(zero,lo,hi-lo)))
        base=[bytearray(b) for at,o,b in regions]
        for e in prepared['common']:setbytes(regions,base,e['offset'],bytesof(e))
        # The old OFF directory selections also point at relocated, optional
        # trampoline-capable copies. Their original scripts remain unchanged.
        for key in prepared['keys']:
            from audit_story_layout import loadarc
            a,es=loadarc(zero,14);entry=next(e for e in a['entries'] if key in e['keys'])
            v=next(v for v in resources if v['old_offset']==entry['offset'])
            setbytes(regions,base,a['directory']+8+entry['index']*8,struct.pack('<II',v['offset']-a['directory'],v['size']))
        base=[bytes(b) for b in base]
        full=compose(regions,base,features,8191)
        # Every authored edit must match exactly. As with prior pack updates,
        # applying the profile also normalizes unused shadow payloads left by
        # historical canonical edits to the release's defined profile bytes.
        starts=[r[0] for r in regions]
        for e in prepared['edits']:
            i=bisect.bisect_right(starts,e['offset'])-1;rel=e['offset']-starts[i]
            assert bytes(full[i][rel:rel+e['size']])==bytesof(e),('Prepared edit mismatch',e['label'])
        application=[]
        for i,((at,o,b),actual) in enumerate(zip(regions,full)):
            before=read(current,at,len(actual))
            if before!=actual:
                name='apply_%03d.bin'%i;(DEST/name).write_bytes(actual)
                application.append(dict(offset=at,size=len(actual),file=name,before_zlib_base64=base64.b64encode(zlib.compress(before,9)).decode('ascii'),after_sha256=hashlib.sha256(actual).hexdigest()))
        (ROOT/'linear_route_application.json').write_text(json.dumps(dict(source_sha256=prepared['source_sha256'],edits=application),indent=2),encoding='utf8')
        digest=hashlib.sha256();inverse=hashlib.sha256();position=0;current.seek(0)
        for e in application:
            at=e['offset']
            while position<at:
                b=current.read(min(8<<20,at-position));assert b;digest.update(b);inverse.update(b);position+=len(b)
            b=current.read(e['size']);new=bytesof(e);digest.update(new);inverse.update(b);position+=len(b)
        while b:=current.read(8<<20):digest.update(b);inverse.update(b)
        assert inverse.hexdigest()==prepared['source_sha256']
        canonical_sha=digest.hexdigest()
    profiles=[]
    for mask,h in catalog(regions,base,features):
        profiles.append(h)
        if mask%1024==0:print('Current profile',mask,flush=True)
    legacy={};legacy_counts={}
    # Recreate every released profile using its own complete base and native
    # feature list. New resource slots have their pre-release source bytes.
    official_base=[r[1] for r in regions]
    with SOURCE.open('rb') as f:old_source=[read(f,at,len(o)) for at,o,b in regions]
    for path in sorted(ROOT.glob('release_v*/patcher/OGG_options.bin')):
        if path.parent.parent.name=='release_'+VERSION:continue
        prev=Pack(path);data=[bytearray(b) for b in (official_base if prev.source_sha==old.source_sha else old_source)]
        for at,o,b in prev.regions:setbytes(regions,data,at,b)
        prior_base=[bytes(b) for b in data]
        for mask,h in catalog(regions,prior_base,prev.features):
            legacy[h]=mask if prev.count>=9 else mask&127
        legacy_counts[path.parent.parent.name]=1<<prev.count
        print('Recognized',path.parent.parent.name,1<<prev.count,flush=True)
    legacy[fingerprint(regions,old_source)]=0
    # Canonical historical edits are recorded independently of release labels.
    with TARGET.open('rb') as f:history=[bytearray(read(f,at,len(o))) for at,o,b in regions]
    legacy[fingerprint(regions,history)]=4095
    history_names=['help_text_journal.json','civil_guard_journal.json','civil_reinforcements_journal.json','civil_war_journal.json','intermission_six_journal.json','beowulf_stage_journal.json','regional_density_journal.json','regional_bosses_journal.json','regional_five_journal.json','followup_refinement_journal.json','huckebein_r_weapons_journal.json','huckebein_r_early_journal.json','early_equipment_journal.json','followup_story_journal.json','support_overhaul_journal.json','story_consistency_journal.json','party_25_journal.json','spirit_balance_25_journal.json','upstream_rebase_journal.json','sp_and_prices_revision_journal.json']
    masks=[4095]*8+[2047]*2+[1023]*2+[511]*2+[127]*6
    for name,mask in zip(history_names,masks):
        for e in json.loads((ROOT/name).read_text(encoding='utf8'))['edits']:
            b=bytes.fromhex(e['before']) if 'before' in e else zlib.decompress(base64.b64decode(e['before_zlib_base64']))
            setbytes(regions,history,e['offset'],b)
        legacy[fingerprint(regions,history)]=mask
    assert len(legacy)<=65536
    options=old.options+[("지상·우주 루트 교차 진행","원본 9화 종료 전 켜고 유지. 양쪽 10~14화를 교차 진행하며 전체 41화·추가 전장 포함 54화")]
    options[8]=(options[8][0].replace('30화','원본 30화'),options[8][1]+' 교차 진행 시 표시 35화부터.')
    def deflate(b):
        c=zlib.compressobj(9,zlib.DEFLATED,-15);return c.compress(b)+c.flush()
    patcher=DIST/'patcher';patcher.mkdir(parents=True,exist_ok=True);path=patcher/'OGG_options.bin'
    with path.open('wb') as f:
        def w(fmt,*v):f.write(struct.pack(fmt,*v))
        def blob(b):w('<I',len(b));f.write(b)
        f.write(b'OGGOPT01');w('<IQ',1,old.size);f.write(old.source_sha);w('<I',13)
        for name,desc in options:blob(name.encode('utf8'));blob(desc.encode('utf8'))
        w('<I',len(regions))
        for (at,o,b),z in zip(regions,base):w('<QI',at,len(o));blob(deflate(o));blob(deflate(z))
        for es in features:
            w('<I',len(es))
            for at,b in es:w('<QI',at,len(b));f.write(b)
        w('<I',len(profiles))
        for mask,h in enumerate(profiles):w('<I',mask);f.write(h)
        f.write(fingerprint(regions,official_base));w('<I',len(legacy))
        for h,mask in legacy.items():f.write(h);w('<I',mask)
    metadata=dict(version=VERSION,original_iso_sha256=old.source_sha.hex(),canonical_iso_sha256=canonical_sha,previous_canonical_sha256=prepared['source_sha256'],
                  iso_size=old.size,defaults=0,options=[dict(bit=i,name=n,description=d) for i,(n,d) in enumerate(options)],profile_count=8192,
                  managed_ranges=len(regions),managed_bytes=sum(len(o) for at,o,b in regions),pack_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pack_size=path.stat().st_size,
                  legacy_profiles=len(legacy),legacy_release_profiles=legacy_counts,upstream_base={k:v for k,v in BASE_INFO.items() if k!='changes'},
                  branch_order=prepared['order'],linear_option_bit=12,logical_indices_preserved=True,playtesting_owner='user',live_playthrough=False)
    (HERE/'build_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in metadata.items() if k not in ['options','upstream_base','legacy_release_profiles']},indent=2),flush=True)
    return metadata

if __name__=='__main__':build()
