"""Prepare reversible additions for both branch paths; never writes an ISO."""
from pathlib import Path
import sys,json,struct,hashlib,zlib,base64
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'option_linear'),str(ROOT/'option_help_text'),str(ROOT)]
from pack_io import Pack,Image
from runtime_helpers import rawmaster
from audit_story_layout import TARGET,loadarc
from inspect_iso import inventory,lice,read,u32
from catalog import u16
from regional_five_policy import stage_base
from linear_route_policy import *
DEST=ROOT/'analysis/linear_route'
PREVIOUS=ROOT/'release_v20261110/patcher/OGG_options.bin'

def packed(b):return base64.b64encode(zlib.compress(b,9)).decode('ascii')

def prepare():
    state=json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    assert not state.get('linear_route_applied')
    p=Pack(PREVIOUS);DEST.mkdir(exist_ok=True);resources=[];edits=[];common=[];on=[]
    with TARGET.open('rb') as f,Image(p,0,TARGET) as zero,Image(p,4095,TARGET) as full:
        _,la=loadarc(full,14);directory=loadarc(full,14)[0]
        blobs={key:read(full,at,n) for key in [2008,2070,*GROUND,*SPACE,2014]
               for ks,at,n in la if key in ks}
        states,managed=entry_states(blobs)
        choice=[r for r in records(blobs[2070]) if r[0]==0xc6 or (r[0]==0xba and r[2:5]==[0x100c1,10,0])]
        assert len(choice)==4 and choice[0][2:5]==[0x100c1,10,0]
        # Guard flags are persistent, shared by both counterparts, and were
        # absent from every current script (including all added missions).
        used=set()
        for ks,at,n in la:
            b=read(full,at,n)
            if b[:4]!=b'LOGO':continue
            for r in records(b):
                for j in range(2,22):
                    if r[j]==0x100c1:used.add((r[j+1],r[j+2]))
        assert not used.intersection(REWARD_FLAGS.values())
        variants={}
        keys=[2008,*ORDER,2014]
        for mask in [0,1,2,3,4095]:
            with Image(p,mask,TARGET) as image:
                a,es=loadarc(image,14)
                for key in keys:
                    ks,at,n=next(e for e in es if key in e[0])
                    variants.setdefault(at,dict(key=key,old_offset=at,old_size=n))
        # Recycle selected LOGO payload slots only after all their variants
        # have been captured. Their directory references all move together.
        # Every other active UNTD/LOGO stays protected.
        _,units=loadarc(f,13);_,logos=loadarc(f,14)
        retired=[(at,at+v['old_size']) for at,v in variants.items()]
        for mask in [0,4095]:
            with Image(p,mask,TARGET) as image:
                _,ls=loadarc(image,14)
                assert all(set(ks)<=set(keys) for ks,at,n in ls if at in variants)
        blocked=[(at,at+n) for ks,at,n in units+logos if at not in variants]
        start,end=min(0x1ac39800,min(variants)),0x1b594000
        start=(start//2048)*2048;raw=read(full,start,end-start);gaps=[];first=None
        for i in range(0,len(raw),2048):
            at=start+i;reuse=any(lo<=at and at+2048<=hi for lo,hi in retired)
            free=(reuse or (at>=0x1ac39800 and not any(raw[i:i+2048]))) and all(at+2048<=lo or at>=hi for lo,hi in blocked)
            if free and first is None:first=at
            if not free and first is not None:gaps.append([first,at]);first=None
        if first is not None:gaps.append([first,end])
        def alloc(size):
            fits=[(hi-lo,i,lo) for i,(lo,hi) in enumerate(gaps) if hi-lo>=size]
            assert fits,('Insufficient verified MAP padding',size,sum(hi-lo for lo,hi in gaps))
            unused,i,at=min(fits);gaps[i][0]=(at+size+2047)&~2047
            assert not any(read(full,at,size)) or any(lo<=at and at+size<=hi for lo,hi in retired)
            return at
        def saveedit(at,b,label):
            old=read(f,at,len(b))
            if old==b:return
            fn='edit_%03d.bin'%len(edits);(DEST/fn).write_bytes(b)
            edits.append(dict(offset=at,size=len(b),file=fn,label=label,before_zlib_base64=packed(old),after_sha256=hashlib.sha256(b).hexdigest()))
        for at,v in sorted(variants.items(),key=lambda item:item[1]['old_size'],reverse=True):
            old=read(zero,at,v['old_size']);current=read(full,at,v['old_size'])
            assert old[:4]==current[:4]==b'LOGO' and u32(old,40)==u32(current,40)
            base,replacements,hooks,copies=script(old,v['key'],states.get(v['key']),choice)
            canonical,cr,ch,ccp=script(current,v['key'],states.get(v['key']),choice)
            assert hooks==ch and copies==ccp and set(replacements)==set(cr)
            b=bytearray(canonical);co=u32(b,44)
            for index,row in cr.items():struct.pack_into('<24I',b,co+index*96,*row)
            newat=alloc(len(base));name=str(v['key'])+'_'+str(at)+'.logo'
            (DEST/name).write_bytes(base);(DEST/(name+'.on')).write_bytes(b)
            v.update(offset=newat,size=len(base),file=name,co=co,hooks=hooks,copies=copies,
                     replacements=[dict(row=i,record=r) for i,r in replacements.items()])
            resources.append(v)
            common.append(dict(offset=newat,file=name,size=len(base)))
            on.extend(dict(offset=newat+co+i*96,hex=struct.pack('<24I',*r).hex(),label='linear '+str(v['key'])+' row '+str(i)) for i,r in replacements.items())
            saveedit(newat,b,'Relocated branch script '+str(v['key']))
        mapping={v['old_offset']:v for v in resources}
        for key in keys:
            e=next(e for e in directory['entries'] if key in e['keys'])
            at=e['offset'];v=mapping[at]
            saveedit(directory['directory']+8+e['index']*8,struct.pack('<II',v['offset']-directory['directory'],v['size']),'Relocated script directory '+str(key))
        elf=next(e for e in inventory(f) if e['name'].startswith('SLPS_'))
        for va,b in number_hook():
            at=elf['offset']+0x180+va-0x100000
            if va==0x270694:assert not any(read(f,at,len(b)))
            common.append(dict(offset=at,hex=b.hex(),size=len(b)));saveedit(at,b,'Equivalent chapter display accessor')
        for va,b in phase_option():
            at=elf['offset']+0x180+va-0x100000
            on.append(dict(offset=at,hex=b.hex(),label='Original chapter30 maintenance timing'))
            saveedit(at,b,'Linear maintenance threshold')
        numbers=[]
        for arc in ['SHARED.BIN','IM.BIN']:
            e,m=rawmaster(f,arc);p0=m.tables['Stag'][0];counts=struct.unpack_from('<3H',m.b,p0+12)
            assert all(m.b[p0+32+i*12+11]==0 for i in range(sum(counts)) if u16(m.b,p0+32+i*12)!=65535)
            s=p0+32+sum(counts[:2])*12
            for i in range(counts[2]):
                at=s+i*12
                if u16(m.b,at)==65535:continue
                value=display_offset(2000+i,m.b[at+6])
                if value:
                    off=e['offset']+at+11;on.append(dict(offset=off,hex=bytes([value]).hex(),label='Linear display offset '+str(2000+i)))
                    saveedit(off,bytes([value]),'Displayed chapter '+str(2000+i)+' '+arc)
                if arc=='SHARED.BIN':numbers.append(dict(key=2000+i,old=m.b[at+6],linear=m.b[at+6]+value,title=m.text(u16(m.b,at))))
        # Allocations remain inside the existing parent span. No header or
        # other archive, geometry, UNTD, combat table or string is modified.
        mapfile=next(e for e in inventory(f) if e['name']=='MAP.BIN;1');outer=lice(f,mapfile['offset'],mapfile['size'])
        parent=outer['entries'][14]
        assert all(parent['offset']<=v['offset'] and v['offset']+v['size']<=mapfile['offset']+mapfile['size'] for v in resources)
        span=max(parent['size'],max(v['offset']+v['size'] for v in resources)-parent['offset'])
        if span!=parent['size']:
            data=struct.pack('<I',span);at=outer['directory']+8+14*8+4
            common.append(dict(offset=at,hex=data.hex(),size=4));saveedit(at,data,'Expanded script parent span')
    edits.sort(key=lambda e:e['offset'])
    assert all(a['offset']+a['size']<=b['offset'] for a,b in zip(edits,edits[1:]))
    result=dict(ready_to_apply=False,source_sha256=state['current_sha256'],resources=resources,common=common,on=on,
                directory=directory['directory'],keys=keys,order=ORDER,managed_targets=[list(x) for x in managed],
                entry_commands={str(k):v for k,v in states.items()},choice_commands=choice,
                reward_flags={str(k):list(v) for k,v in REWARD_FLAGS.items()},numbers=numbers,edits=edits,
                logical_campaign_indices_preserved=True,new_full_ISOs_created=0)
    (ROOT/'linear_route_prepared.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(resources=len(resources),new_resource_bytes=sum(v['size'] for v in resources),managed_availability_targets=len(managed),edits=len(edits),order=ORDER),indent=2))
    return result

if __name__=='__main__':prepare()
