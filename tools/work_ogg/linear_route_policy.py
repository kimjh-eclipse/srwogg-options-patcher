"""Optional chronological traversal of both native OGG branches.

Only availability is restored at viewpoint switches. Ownership, equipment
and earned training are preserved; off-screen catch-up awards are disabled
when both fronts are played. Original indices stay unchanged; a zero-valued
Stag padding byte supplies display-number offsets.
"""
import struct
from story_scripts_25 import records,command,NONE,DEAD,text_at
from inspect_iso import u32
from story_native_hooks import I,R,J,branch,code,RET

GROUND=list(range(2009,2014))
SPACE=list(range(2051,2056))
ORDER=[k for pair in zip(GROUND,SPACE) for k in pair]
NEXT={2008:2009,**dict(zip(ORDER,ORDER[1:]+[2014]))}
REWARD_FLAGS={11:(40,0),13:(40,1),14:(40,2)}

def availability(rows):
    return [(r[2],r[3],r[4]) for r in rows if r[0] in [0x4a,0xd6]
            and r[2] in [0x100a8,0x100bd] and r[4] in [0,1]]

def entry_states(blobs):
    sequence={k:availability(records(blobs[k])) for k in [2008]+GROUND+SPACE}
    managed=sorted({(t,k) for seq in sequence.values() for t,k,v in seq})
    # Permanent exits (D6 value 0x80) are never reactivated by a switch.
    permanent={(r[2],r[3]) for b in blobs.values() for r in records(b)
               if r[0]==0xd6 and r[4]==0x80}
    managed=[x for x in managed if x not in permanent]
    base=dict.fromkeys(managed,1)
    def apply(state,key):
        for t,k,v in sequence[key]:
            if (t,k) in state:state[t,k]=v
    apply(base,2008)
    result={};ends=[]
    for route in [GROUND,SPACE]:
        state=base.copy()
        for key in route:
            result[key]=[command(0x4a,t,k,v) for (t,k),v in sorted(state.items())]
            apply(state,key)
        ends.append(state)
    merged={x:max(s[x] for s in ends) for x in managed}
    result[2014]=[command(0x4a,t,k,v) for (t,k),v in sorted(merged.items())]
    return result,managed

def jump(source,target):
    assert target>source,'Native conditional skips are forward-only'
    delta=(target-source)&0xffffffff
    # Native comparison resolves both operands to the same register. The
    # not-equal predicate is always false, so its relative skip always runs.
    return command(0x91,0x8000,0x8001,0x8000,1,DEAD,delta)

def append_rows(old,added):
    rows=records(old);end=u32(old,44)+len(rows)*96;extra=len(added)*96
    b=bytearray(old[:end])+bytearray(b''.join(struct.pack('<24I',*r) for r in added))+bytearray(old[end:])
    struct.pack_into('<I',b,40,len(rows)+len(added))
    for at in [52,60,68,76,84,92]:
        assert u32(old,at)>=end
        struct.pack_into('<I',b,at,u32(old,at)+extra)
    for at in [4,108]:struct.pack_into('<I',b,at,len(b))
    assert records(b)[:len(rows)]==rows
    for sid in range(u32(old,64)+u32(old,80)-1):assert text_at(b,sid)==text_at(old,sid)
    return bytes(b)

def script(old,key,entry=None,choice=None):
    rows=records(old);added=[];replacements={};hooks=[];copies=[]
    def start(index,body,label,source=None,dest=None,count=None):
        at=len(rows)+len(added)
        replacements[index]=jump(index,at)
        added.extend(body)
        hooks.append(dict(row=index,start=at,end=len(rows)+len(added),kind=label))
        if source is not None:copies.append(dict(source_start=source,dest_start=dest,count=count))
        return at
    def tail(index):
        end=next(i for i in range(index,len(rows)) if rows[i][0]==0x25)+1
        result=[r.copy() for r in rows[index:end]]
        # Native structured skips must stay inside this copied function tail.
        for j,r in enumerate(result):
            if r[0] in [0x90,0x91]:
                for field in ([6,7] if r[0]==0x90 else [7]):
                    if r[field]<0x80000000:assert index+j+r[field]<=end,(key,index,j,r[field],end)
        return result
    if entry:
        # BD loads the map's initialization record. Some space stages have
        # no difficulty query here; their first 8013 query is a later battle
        # event and must never be used as the availability restoration point.
        index=next(i+1 for i,r in enumerate(rows) if r[0]==0xbd)
        assert rows[index][0] not in [0x25,0x26,0x3e]
        at=len(rows)+len(added)
        copied=tail(index)
        start(index,entry+copied,'availability',index,at+len(entry),len(copied))
    if key==2008:
        index=next(i for i,r in enumerate(rows) if r[0]==0xa1 and r[2]==70)
        start(index,choice+[command(0xa1,9,0)],'ground-first-choice')
    elif key in NEXT:
        index=next(i for i,r in enumerate(rows) if r[0]==0xa1 and r[2]!=0xffffffff)
        r=rows[index].copy();r[2]=NEXT[key]-2000;replacements[index]=r
    chapter=10+((key-2009) if key in GROUND else (key-2051)) if key in ORDER else None
    if chapter in REWARD_FLAGS:
        grants=[i for i,r in enumerate(rows) if r[0] in [0x60,0x64]]
        if grants:
            first,last=grants[0],grants[-1];group,bit=REWARD_FLAGS[chapter]
            at=len(rows)+len(added)
            copied=tail(first)
            body=[command(0x93,0x100c1,group,bit,0x800f,NONE,NONE,NONE),
                  command(0x91,0x800f,0x8000,0,1,DEAD,last-first+3),
                  command(0xba,0x100c1,group,bit)]+copied
            start(first,body,'shared-reward-'+str(chapter),first,at+3,len(copied))
    # The ground recovery already sets 57,3. Reuse that native acquisition bit
    # for the optional space fallback rather than repeating its recovery speech.
    if key==2054:
        for i,r in enumerate(rows):
            if r[0]==0x93 and r[2:5]==[0x100c1,63,6]:
                r=r.copy();r[3:5]=[57,3];replacements[i]=r
    common=append_rows(old,added)
    # Copies terminate through their original return/next-stage commands;
    # they never rely on unsupported negative relative skips.
    for cp in copies:
        for j in range(cp['count']):
            row=rows[cp['source_start']+j]
            if key in NEXT and row[0]==0xa1 and row[2]!=0xffffffff:
                row=row.copy();row[2]=NEXT[key]-2000
                replacements[cp['dest_start']+j]=row
    # These three original C6 attributes grant off-screen EXP, kills and PP.
    # Both fronts are now played, so their normal battle earnings replace
    # compensation for the route the player used to skip.
    if key in ORDER+[2008]:
        for i,row in enumerate(records(common)):
            if row[0]==0xc6 and row[2]==0x100a8 and row[4] in [0x1006f,0x100c6,0x100ac]:
                replacements[i]=command(0x8a)
    return common,replacements,hooks,copies

def display_offset(key,oldnumber):
    if key in GROUND:return key-2009
    if key in SPACE:return key-2051+1
    return 5 if oldnumber>=15 else 0

def number_hook():
    # All valid Stag rows in all three campaigns have byte11 == 0. The new
    # checkbox changes only that byte in OGG; other games remain identical.
    return [(0x2705d4,code([I(36,2,1,11),J(2,0x270694)])),
            (0x270694,code([I(36,2,2,6),R(31,0,0,8),R(2,1,2,33)]))]

def phase_option():
    # The only nonzero private phase threshold is 29. Five newly played
    # branch stages move original chapter30 to displayed chapter35.
    return [(0x20637c,code([I(11,1,1,34)]))]
