"""Native route, availability, reward and display checks, plus resource parity.

Map actors and rendered battles are not emulated. Actual save setters, script
branches, acquisition handlers, getters and next-stage handlers are executed.
"""
from runtime_helpers import *
from audit_story_layout import loadarc
import json,hashlib,collections
from linear_route_policy import *
from regional_five_policy import stage_base
from explanation_tables import explanation_records,text_records
P=ROOT/'linear_route_prepared.json';DEST=ROOT/'analysis/linear_route'

def check():
    p=Pack(ROOT/'release_v20261121/patcher/OGG_options.bin');old=Pack(ROOT/'release_v20261110/patcher/OGG_options.bin')
    prepared=json.loads(P.read_text(encoding='utf8'));base=ram(p,8191)
    with Image(p,8191,TARGET) as f:_,master=rawmaster(f,'SHARED.BIN')
    v=machine(base,master.b);checks=0
    for value in [0,1,7,0xffffffff]:
        for start,end in [(100,200),(200,400)]:
            v.reg(0x8000,value);v.cpu.write(v.ctx+0x48d0,start,4)
            assert v.op(jump(start,end))==10
            assert (v.cpu.read(v.ctx+0x48d0,4)+1)&0xffffffff==end;checks+=1
    # Original and added owned records with deliberately non-default training.
    story=json.loads((ROOT/'story_25_prepared.json').read_text(encoding='utf8'))
    for ch in story['chapters']:
        for r in ch['recruits']:assert v.birth(bytes.fromhex(r['row_hex']))==1
    cp=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'))
    for name,x in cp['members'].items():
        if x['added']:continue
        if x['template']:
            row=bytearray.fromhex(x['template']);struct.pack_into('<I',row,8,0)
            for at in range(0x38,0x50,4):struct.pack_into('<I',row,at,0)
            for at in [0x50,0x54,0x58]:struct.pack_into('<I',row,at,5000)
            struct.pack_into('<I',row,32,x['pilot']);assert v.birth(row)==1
        elif x['pilot'] is not None and v.cpu.run(0x244a40,[v.save,x['pilot'],1,0])<0:
            slot=v.cpu.run(0x24b180,[v.save,x['pilot'],0]);assert slot>=0
            v.cpu.run(0x247c60,[v.save,2,slot,1,0])
    for typ,key in prepared['managed_targets']:
        if typ==0x100bd:
            if v.cpu.run(0x244c20,[v.save,key,0,0])<0:assert v.op(command(0x5f,key,NONE,NONE,NONE))==10
        elif v.cpu.run(0x244a40,[v.save,key,1,0])<0:
            slot=v.cpu.run(0x24b180,[v.save,key,0]);assert slot>=0
            v.cpu.run(0x247c60,[v.save,2,slot,1,0])
    refs=[]
    for i in range(128):
        at=v.save+0x6efc+i*216
        if v.cpu.read(at,2)!=65535:refs.append((at,216,42))
    for i in range(192):
        at=v.save+0x25cfc+i*92
        if v.cpu.read(at,2)!=65535:
            v.cpu.write(at+6,30+i,2);v.cpu.write(at+8,500+i*3,2);v.cpu.write(at+10,15000+i*50,2)
            refs.append((at,92,2))
    def snapshot():return [bytes(v.cpu.mem[a:a+n]) for a,n,x in refs]
    before=snapshot();availability_checks=0
    # Prove what the original off-screen awards do before asserting that the
    # new no-op replacements preserve already-earned training.
    kai=v.cpu.run(0x244a40,[v.save,0x442,1,0]);assert kai>=0
    pilot=v.save+0x25cfc+kai*92;saved=bytes(v.cpu.mem[v.save:v.save+0x40000]);growth_checks=0
    for attr,value,field,delta in [(0x1006f,3,10,1500),(0x100c6,3,6,3),(0x100ac,6,12,6)]:
        v.cpu.mem[v.save:v.save+len(saved)]=saved;amount=v.cpu.read(pilot+field,2)
        assert v.op(command(0xc6,0x100a8,0x442,attr,value))==10
        assert v.cpu.read(pilot+field,2)==amount+delta
        v.cpu.mem[v.save:v.save+len(saved)]=saved
        assert v.op(command(0x8a))==10 and bytes(v.cpu.mem[v.save:v.save+len(saved)])==saved;growth_checks+=1
    for key in ORDER+[2014]:
        for r in prepared['entry_commands'][str(key)]:
            assert r[0]==0x4a and r[4] in [0,1];assert v.op(r)==10
            after=snapshot()
            for oldb,newb,(a,n,allowed) in zip(before,after,refs):
                assert all(x==y for i,(x,y) in enumerate(zip(oldb,newb)) if i!=allowed),(key,hex(a))
            availability_checks+=1
    # Unit-only duplicate grants preserve the same owned machine and training.
    assert v.op(command(0x5f,1410,NONE,NONE,NONE))==10
    slot=v.cpu.run(0x244c20,[v.save,1410,0,0]);at=v.save+0x6efc+slot*216
    v.cpu.write(at+0x30,7,1);unit=bytes(v.cpu.mem[at:at+216])
    assert v.op(command(0x5f,1410,NONE,NONE,NONE))==10
    assert unit==bytes(v.cpu.mem[at:at+216]);checks+=1
    print('Native availability and duplicate unit preservation passed.',flush=True)
    # Native relative branches run from each actual replacement into its
    # appended availability/reward block and back, under arbitrary register0.
    trampoline_checks=0;reward_checks=0;disabled_growth=0
    for rsrc in prepared['resources']:
        blob=(DEST/(rsrc['file']+'.on')).read_bytes();rows=records(blob)
        assert not any(r[0]==0xc6 and r[2]==0x100a8 and r[4] in [0x1006f,0x100c6,0x100ac] for r in rows) or rsrc['key']==2014
        disabled_growth+=sum(r['record'][0]==0x8a for r in rsrc['replacements'])
        for hook in rsrc['hooks']:
            for value in [0,1,7]:
                x=machine(base,master.b);x.reg(0x8000,value);x.cpu.write(x.ctx+0x48d0,hook['row'],4)
                assert x.op(rows[hook['row']])==10
                assert (x.cpu.read(x.ctx+0x48d0,4)+1)&0xffffffff==hook['start'];trampoline_checks+=1
            if hook['kind']=='availability':
                cp=next(cp for cp in rsrc['copies'] if cp['source_start']==hook['row'])
                copied=rows[cp['dest_start']]
                oldrows=records((DEST/rsrc['file']).read_bytes())
                assert cp['source_start']==next(i+1 for i,r in enumerate(oldrows) if r[0]==0xbd)
                assert copied==oldrows[cp['source_start']]
                assert rows[hook['end']-1][0]==0x25;trampoline_checks+=1
    # Shared reward guards allow the first native event and skip the complete
    # mirrored block after Save_Diff state is reloaded into a new VM.
    for chapter in [11,13,14]:
        pair=[next(r for r in prepared['resources'] if r['key']==key) for key in [2009+chapter-10,2051+chapter-10]]
        x=machine(base,master.b);group,bit=REWARD_FLAGS[chapter]
        for step,resource in enumerate(pair+pair):
            rows=records((DEST/(resource['file']+'.on')).read_bytes());h=next(h for h in resource['hooks'] if h['kind']=='shared-reward-'+str(chapter));at=h['start']
            x.cpu.write(x.ctx+0x48d0,at,4);assert x.op(rows[at])==10
            x.cpu.write(x.ctx+0x48d0,at+1,4);assert x.op(rows[at+1])==10
            pc=(x.cpu.read(x.ctx+0x48d0,4)+1)&0xffffffff
            if step==0:
                assert pc==at+2;assert x.op(rows[at+2])==10
                assert rows[at+3][0] in [0x60,0x64];assert x.op(rows[at+3])==10
            else:
                assert pc==at+1+rows[at+1][7]
                assert pc>at+3 and pc<h['end']
            save=bytes(x.cpu.mem[x.save:x.save+0x40000]);diff=bytes(x.cpu.mem[x.diff:x.diff+0x1300])
            fresh=machine(base,master.b);fresh.cpu.mem[fresh.save:fresh.save+len(save)]=save;fresh.cpu.mem[fresh.diff:fresh.diff+len(diff)]=diff;x=fresh;reward_checks+=1
    # The native getter stays identical for every valid row of OG1 and OG2.
    # OGG offsets add to whichever optional base number is currently selected.
    display_checks=0;route_checks=0;resource_checks=0;help_checks=0
    masks=[0,1,2,3,2048,2049,4095,4096,4097,4098,4099,6144,6145,8191]
    graph_results=[]
    for mask in masks:
        print('Semantic profile',mask,flush=True)
        with Image(p,mask,TARGET) as f,Image(old,mask&4095,TARGET) as prior:
            _,m=rawmaster(f,'SHARED.BIN');_,om=rawmaster(prior,'SHARED.BIN')
            x=machine(ram(p,mask),m.b);sx=m.tables['Stag'][0];counts=struct.unpack_from('<3H',m.b,sx+12);index=0
            for game,n in enumerate(counts):
                for stage in range(n):
                    at=sx+32+index*12;index+=1
                    if struct.unpack_from('<H',m.b,at)[0]==65535:continue
                    number=m.b[at+6]+(m.b[at+11] if game==2 and mask&4096 else 0)
                    assert x.cpu.run(0x2705c0,[x.master,game,stage])==number,(mask,game,stage,number)
                    display_checks+=1
            a,es=loadarc(f,14);oa,oes=loadarc(prior,14)
            route={};blobs={}
            for ks,at,n in es:
                for key in ks:
                    if key in [2000+i for i in range(1,57)]+[2070]:blobs[key]=read(f,at,n)
            for key,b in blobs.items():
                rr=records(b);active=list({tuple(r) for r in rr if r[0]==0xa1 and r[2]!=0xffffffff})
                if key in NEXT and mask&4096:
                    if key==2008:assert any(r[0]==0xa1 and r[2]==9 for r in rr)
                    else:assert len(active)==1 and active[0][2]==NEXT[key]-2000
                if key==2008 and mask&4096:route[key]=2009
                elif len(active)==1:route[key]=2000+active[0][2]
            if mask&4096:
                current=2001;visited=[]
                while current in route:
                    assert current not in visited;visited.append(current);current=route[current]
                if current not in visited and current in blobs:visited.append(current)
                assert all(key in visited for key in ORDER)
                assert len(visited)==(54 if mask&2048 else 41),(mask,len(visited),visited)
                assert visited[visited.index(2009):visited.index(2055)+1]==ORDER
                graph_results.append(dict(mask=mask,battles=len(visited),final_key=visited[-1]))
            for key in prepared['keys']:
                _,oldat,oldn=next(e for e in oes if key in e[0]);ob=read(prior,oldat,oldn);nb=blobs[key]
                rr=records(nb);original=records(ob);changes={r['row'] for v in prepared['resources'] if v['key']==key for r in v['replacements']} if mask&4096 else set()
                for i,row in enumerate(original):
                    if i not in changes:assert rr[i]==row,(mask,key,i)
                for sid in range(u32(ob,64)+u32(ob,80)-1):assert text_at(nb,sid)==text_at(ob,sid);resource_checks+=1
                assert read(f,next(e[1] for e in loadarc(f,13)[1] if key in e[0]),next(e[2] for e in loadarc(f,13)[1] if key in e[0]))==read(prior,next(e[1] for e in loadarc(prior,13)[1] if key in e[0]),next(e[2] for e in loadarc(prior,13)[1] if key in e[0]))
            for arc in ['SHARED.BIN','IM.BIN']:
                _,nm=rawmaster(f,arc);_,bm=rawmaster(prior,arc)
                for tag in nm.tables:
                    if tag=='Stag':continue
                    a,n,_=nm.tables[tag];b,bn,_=bm.tables[tag];assert n==bn and nm.b[a:a+n]==bm.b[b:b+bn],(mask,arc,tag)
                a,n,_=nm.tables['Expl'];help_checks+=len(explanation_records(nm.b[a:a+n]))
            # Real next-stage handler on a persistent roster; counts are native.
            for key in ORDER:
                x.cpu.write(x.diff+0xffc,key-2000,4)
                dest=NEXT[key]-2000
                assert x.op(command(0xa1,dest,0))==14
                assert x.cpu.read(x.diff+0xffc,4)==dest;route_checks+=1
    # Private maintenance shifts five clears only when both options are active.
    phase_checks=0
    tuning=json.loads((ROOT/'support_overhaul_prepared.json').read_text(encoding='utf8'))['masters']['SHARED.BIN']['units']
    for mask in [0,256,4096,4352,4095,8191]:
        with Image(p,mask,TARGET) as f:_,m=rawmaster(f,'SHARED.BIN')
        x=machine(ram(p,mask),m.b)
        for u in tuning:
            for progress in [28,29,30,33,34,35,36]:
                x.cpu.write(x.diff+0x1000,progress,4)
                threshold=34 if mask&4096 else 29
                expected=u['full_index'] if not mask&256 or progress>=threshold else u['early_index']
                at=x.cpu.run(0x278880,[x.master+0x40,u['full_index']])
                assert at==0x1900000+m.tables['Unit'][0]+12+expected*100,(mask,u['name'],progress)
                for w in u['weapons']:
                    weapon=x.cpu.read(at+0x24+w['slot']*2,2)
                    assert weapon==(w['new_key'] if mask&256 and progress>=threshold else w['old_key'])
                phase_checks+=1
    result=dict(passed=True,native_jump_and_duplicate_grant_checks=checks,native_availability_commands=availability_checks,
                tracked_unit_and_pilot_slots=len(refs),slot_comparison_includes_vacant=True,all_training_equipment_and_ownership_preserved=True,
                native_trampoline_checks=trampoline_checks,persistent_mirrored_reward_guard_checks=reward_checks,
                native_growth_compensation_attribute_checks=growth_checks,disabled_offscreen_growth_commands=disabled_growth,
                native_display_getters=display_checks,native_next_stage_checks=route_checks,
                logical_script_text_comparisons=resource_checks,explanation_records_checked=help_checks,
                semantic_masks=masks,route_graphs=graph_results,actual_map_actor_AI_GPU_card_IO_tested=False,
                private_maintenance_checks=phase_checks,ISO_writes_performed=False)
    (HERE/'linear_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return result

if __name__=='__main__':check()
