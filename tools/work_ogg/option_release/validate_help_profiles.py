"""Check common help resources under the same semantic option combinations."""
from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from validate_options import Profiles,Image
from build_options import rawmaster,source_image
from explanation_tables import explanation_records,text_records

def table(master,tag):
    at,n,_=master.tables[tag]
    return master.b[at:at+n]

def main():
    profile=Profiles()
    masks=sorted(set([0,1,16,17,2048,2049,2064,2065]+[4095^x for x in [0,1,16,17,2048,2049,2064,2065]]))
    with source_image() as f:
        expected={arc:explanation_records(table(rawmaster(f,arc)[1],'Expl')) for arc in ['SHARED.BIN','IM.BIN']}
    count=0; protected=[]
    for mask in masks:
        image=Image(profile,mask)
        try:
            for arc in expected:
                entry,m=rawmaster(image,arc)
                assert explanation_records(table(m,'Expl'))==expected[arc],(mask,arc)
                count+=len(expected[arc])
                if mask==0:
                    protected.append((entry['offset']+m.tables['Strg'][0],entry['offset']+entry['size']))
        finally:image.f.close()
    # No checkbox may overwrite the repaired dictionaries or explanation lists.
    for edits in profile.features:
        for at,b in edits:
            assert all(at+len(b)<=lo or at>=hi for lo,hi in protected)
    result=dict(passed=True,pack_sha256=hashlib.sha256((HERE.parent/'release_v20261110/patcher/OGG_options.bin').read_bytes()).hexdigest(),semantic_masks=masks,explanation_record_comparisons=count,help_repair_independent_of_all_12_options=True,no_feature_overwrites_help_tables=True,ISO_writes_performed=False)
    (HERE/'help_text_profiles_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
