from build_selected_27 import *
def has_japanese(s):return any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in s)
def main():
 report=json.loads((ROOT/'manifest_selected_27.json').read_text(encoding='utf-8'));export=[]
 with TARGET.open('rb') as f:
  root=arc('BATTLE.BIN');outer=root['entries'][5];span=u32(read(f,root['directory']+8+5*8+4,4));voices=lice(f,outer['offset'],span)
  for pilot in report['cast']:
   e=next(e for e in voices['entries'] if pilot['new_key'] in e['keys']);blob=read(f,e['offset'],e['size']);seen=set();unique=[]
   for r in texts(blob):
    if r['raw'] in seen:continue
    seen.add(r['raw']);unique.append(r)
   item=dict(pilot=pilot['pilot_name'],unit=pilot['unit_name'],key=pilot['new_key'],entry=e,unique=unique)
   export.append(item);print(item['pilot'],len(texts(blob)),len(unique),'JP',sum(has_japanese(r['kr']) for r in unique))
 (OUT/'subtitles_27.json').write_text(json.dumps(export,ensure_ascii=False,indent=2),encoding='utf-8')
 print('total unique',sum(len(x['unique']) for x in export),'JP',sum(has_japanese(r['kr']) for x in export for r in x['unique']))
if __name__=='__main__':main()
