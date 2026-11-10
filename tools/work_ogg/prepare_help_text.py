"""Restore official explanation lists while keeping all authored gameplay tables."""
from pathlib import Path
import sys, json, struct, hashlib
ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'upstream_base'), str(ROOT / 'option_civil_reinforcements')]
from source_image import source_image
from build_options import rawmaster
from inspect_iso import inventory, lice, read, u32
from catalog import Master, u16
from explanation_tables import explanation_records, pack_explanations, compact_text, text_records

DEST = ROOT / 'analysis/help_text'
TARGET = ROOT.parent / 'SRWOGS_EX_K_TEST.ISO'

def part(blob, master, tag):
    at, size, count = master.tables[tag]
    return bytes(blob[at:at + size])

def rebuild(current, official):
    cm, om = Master(current), Master(official)
    fields = list(range(0x18, 0x8c, 4))
    starts = [u32(current, k) for k in fields]
    parts = {k: bytes(current[at:(starts[i+1] if i+1 < len(starts) else at+cm.tables['Sent'][1])]) for i,(k,at) in enumerate(zip(fields,starts))}
    expected = explanation_records(part(official, om, 'Expl'))
    parts[0x80] = compact_text(part(current, cm, 'Strg'))
    parts[0x84] = pack_explanations(expected)
    # Keep every sentence byte and ID, including translations, unchanged.
    parts[0x88] += bytes(-len(parts[0x88]) % 4)
    result = bytearray(current[:starts[0]])
    for key in fields:
        struct.pack_into('<I', result, key, len(result))
        result.extend(parts[key])
    nm = Master(result)
    for tag in cm.tables:
        if tag in ['Strg','Expl','Sent']:
            continue
        at = cm.tables[tag][0]
        end = min([v[0] for v in cm.tables.values() if v[0] > at])
        na = nm.tables[tag][0]
        assert current[at:end] == result[na:na+end-at], tag
    assert text_records(part(result,nm,'Strg')) == text_records(part(current,cm,'Strg'))
    assert text_records(part(result,nm,'Sent')) == text_records(part(current,cm,'Sent'))
    assert explanation_records(part(result,nm,'Expl')) == expected
    ea, es, ec = cm.tables['Expl']
    wrong = invalid = 0
    for i, value in enumerate(expected):
        at = ea + u32(current, ea+12+i*4)
        end = at+2+u16(current,at)*2
        invalid += end > ea+es
        wrong += end > ea+es or current[at:end] != value
    return bytes(result), dict(explanations=len(expected),line_references=sum((len(x)-2)//2 for x in expected),wrong_lists_before=wrong,out_of_table_lists_before=invalid,old_bytes=len(current),new_bytes=len(result),all_gameplay_tables_preserved=True,all_names_and_sentence_bytes_preserved=True)

def prepare():
    DEST.mkdir(exist_ok=True)
    state = json.loads((ROOT/'current_target.json').read_text(encoding='utf8'))
    edits=[]; masters={}
    with TARGET.open('rb') as f, source_image() as official:
        for name in ['SHARED.BIN','IM.BIN']:
            file=next(x for x in inventory(f) if x['name']==name+';1')
            outer=lice(f,file['offset'],file['size']);parent=outer['entries'][3];nested=lice(f,parent['offset'],parent['size'])
            entry, cm=rawmaster(f,name);_,om=rawmaster(official,name)
            new, note=rebuild(cm.b,om.b)
            assert entry['offset']+len(new)<=parent['offset']+parent['size'], 'Master exceeds its existing archive'
            growth=len(new)-entry['size'];assert growth>=0 and not any(read(f,entry['offset']+entry['size'],growth))
            path=DEST/(name+'.master');path.write_bytes(new)
            old=read(f,entry['offset'],len(new));assert new!=old
            edits.append(dict(offset=entry['offset'],size=len(new),file=path.name,label=name+' explanation data',before_sha256=hashlib.sha256(old).hexdigest()))
            pointer=nested['directory']+8+entry['index']*8+4
            path=DEST/(name+'.length');path.write_bytes(struct.pack('<I',len(new)))
            edits.append(dict(offset=pointer,size=4,file=path.name,label=name+' master length',before_sha256=hashlib.sha256(read(f,pointer,4)).hexdigest()))
            note.update(offset=entry['offset'],growth_into_verified_zero_padding=growth,parent_span_unchanged=True)
            masters[name]=note
    result=dict(target=str(TARGET),source_sha256=state['current_sha256'],masters=masters,edits=sorted(edits,key=lambda e:e['offset']),ready_to_apply=False,ISO_writes_performed=False)
    (ROOT/'help_text_prepared.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result['masters'],indent=2))
    return result

if __name__=='__main__': prepare()
