from inspect_iso import *
sys.path.insert(0,str(ROOT.parent/'work_ogs'))
from ogs_korean_codec import decode,encode
def main():
    inventory=json.loads((OUT/'iso_inventory.json').read_text(encoding='utf-8'))
    with SOURCE.open('rb') as f:
        for name in ('SHARED.BIN','MAP.BIN','IM.BIN','BATTLE.BIN'):
            a=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
            print(name)
            for e in a['entries']:
                b=read(f,e['offset'],min(e['size'],192))
                print(e['index'],hex(e['offset']),hex(e['size']),b[:24].hex())
                sub=lice(f,e['offset'],e['size'])
                if sub:
                    print(' CHILD',sub['count'],sub['slots'],[(x['index'],hex(x['offset']),x['size'],x['head'][:16]) for x in sub['entries'][:4]])
                    (OUT/f"{name}.{e['index']}.json").write_text(json.dumps(sub,ensure_ascii=False,indent=2),encoding='utf-8')
            if name=='SHARED.BIN':
                entry=next(x for x in inventory['files'] if x['name']==name+';1')
                b=read(f,entry['offset'],entry['size']);(OUT/name).write_bytes(b)
                for s in ['그랑존','네오','슈우','다크브레인','잉그램','알카이드','필중','정신']:
                    needle=encode(s);pos=0;found=[]
                    while (pos:=b.find(needle,pos))>=0:
                        found.append((hex(entry['offset']+pos),decode(b[pos:b.find(b'\0',pos)])));pos+=len(needle)
                    print('TEXT',s,found[:20])
if __name__=='__main__':main()
