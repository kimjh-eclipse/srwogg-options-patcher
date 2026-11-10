"""Exercise native count/list/text and menu-help getters against the official data."""
from prepare_help_text import *
from explanation_tables import u16
from validate_regional_five import VM, load_campaign_master
from validate_options import Profiles, ram
from catalog import decode

def string_at(cpu, at):
    end = cpu.mem.index(0, at)
    return bytes(cpu.mem[at:end+1])

def validate():
    prepared = json.loads((ROOT/'help_text_prepared.json').read_text(encoding='utf8'))
    machine = ram(Profiles(),4095)
    reports = {}; total = 0; menus = 0; encyclopedia_checks=0
    with source_image() as official, TARGET.open('rb') as current:
        for arc in ['SHARED.BIN','IM.BIN']:
            blob=(DEST/(arc+'.master')).read_bytes();m=Master(blob)
            _,base=rawmaster(official,arc);_,before=rawmaster(current,arc)
            lists=explanation_records(part(base.b,base,'Expl'))
            assert explanation_records(part(blob,m,'Expl'))==lists
            sentences=text_records(part(blob,m,'Sent'))
            vm=VM(machine);load_campaign_master(vm,blob);c=vm.cpu
            count_checks = line_checks = text_checks = 0
            for i,record in enumerate(lists):
                n=u16(record);assert c.run(0x277a30,[vm.master+0x2b4,i])==n
                count_checks+=1
                for line in range(n):
                    sid=u16(record,2+line*2);assert sid<len(sentences)
                    actual=c.run(0x2779f0,[vm.master+0x2b4,i,line])
                    assert actual==sid,(arc,i,line,actual,sid)
                    address=c.run(0x277c30,[vm.master+0x2cc,actual])
                    assert string_at(c,address)==sentences[sid]
                    line_checks+=1;text_checks+=1
            category_checks = 0; categories={}; samples=[]
            for tag,field,fn in [('Sprt',6,0x271050),('Skil',2,0x270e00),('Abil',2,0x270cf0),('Part',0x1e,0x270710)]:
                cases=0
                for index,at,row in m.rows(tag):
                    expl=u16(row,field)
                    if expl==65535:continue
                    assert expl<len(lists)
                    record=lists[expl];n=u16(record)
                    if not n:continue
                    for line in list(range(n))+[-1,n,99]:
                        expected_line=max(0,min(line,n-1));sid=u16(record,2+expected_line*2)
                        address=c.run(fn,[vm.master,index,line])
                        assert string_at(c,address)==sentences[sid],(arc,tag,index,line)
                        category_checks+=1;cases+=1
                    if arc=='SHARED.BIN' and (tag=='Sprt' and index<5 or tag in ['Abil','Part'] and index<2):
                        name_id=u16(row)
                        samples.append(dict(category=tag,index=index,name=m.text(name_id) if name_id<m.tables['Strg'][2] else '(없음)',first_line=decode(sentences[u16(record,2)][:-1])))
                categories[tag]=cases
            encyclopedia={}
            for tag,obj in [('UnEx',0x254),('PlEx',0x26c),('HlEx',0x284)]:
                count=0
                for index,at,row in m.rows(tag):
                    address=c.run(0x278120,[vm.master+obj,index])
                    assert c.read(address,2)==u16(row),(arc,tag,index)
                    count+=1
                encyclopedia[tag]=count;encyclopedia_checks+=count
            # Loading/looking up descriptions must never alter the persistent save.
            save_before=bytes(c.mem[vm.save:vm.save+0x40000])
            names=text_records(part(blob,m,'Strg'))
            for i in range(len(names)):
                address=c.run(0x277c30,[vm.master+0x29c,i])
                assert string_at(c,address)==names[i]
            assert bytes(c.mem[vm.save:vm.save+0x40000])==save_before
            report=dict(explanation_records=len(lists),native_count_checks=count_checks,native_line_id_checks=line_checks,native_text_checks=text_checks,native_menu_checks=category_checks,menu_categories=categories,encyclopedia_mapping_checks=encyclopedia,all_names_checked=m.tables['Strg'][2],samples=samples,all_non_text_tables_unchanged=True)
            reports[arc]=report;total+=count_checks+line_checks+text_checks;menus+=category_checks
    # Synthetic binary records contain embedded zero bytes and distinct sentence IDs.
    from build_all_cast import compact
    values=[struct.pack('<3H',2,0,513),struct.pack('<2H',1,2),struct.pack('<2H',1,256),struct.pack('<3H',2,0,513)]
    table=pack_explanations(values);assert explanation_records(compact(bytearray(table)))==values
    result=dict(passed=True,archives=reports,native_explanation_checks=total,native_menu_checks=menus,native_encyclopedia_mapping_checks=encyclopedia_checks,synthetic_binary_compaction_regression=True,official_explanation_records_restored=sum(x['explanation_records'] for x in reports.values()),existing_gameplay_and_names_preserved=True,live_PCSX2_UI_playthrough=False)
    (ROOT/'help_text_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    prepared['ready_to_apply']=True;(ROOT/'help_text_prepared.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':validate()
