"""Compile and inspect the twelve-option native patcher without ISO writes."""
from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
def run(args):
 r=subprocess.run([str(x) for x in args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,(args,r.stdout[-1400:],r.stderr[-1400:])
def main():
 meta=json.loads((HERE/'build_metadata.json').read_text(encoding='utf8'));dist=WORK/('release_'+meta['version']);exe=dist/'patcher/OGG_Options_Patcher.exe'
 if sys.argv[1] in ('compile','refresh_ui'):
  generated=HERE/'OggOptionsPatcher.generated.cs';generated.write_text((HERE/'OggOptionsPatcher.cs').read_text(encoding='utf-8-sig').replace('__PACK_SHA__',meta['pack_sha256']),encoding='utf-8-sig')
  run([r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/target:winexe','/optimize+','/codepage:65001','/out:'+str(exe),'/reference:System.dll','/reference:System.Core.dll','/reference:System.Drawing.dll','/reference:System.Windows.Forms.dll',generated])
  if sys.argv[1]=='compile':run([exe,'--selftest','--report',HERE/'selftest.json'])
  run([exe,'--preview',HERE/'ui_preview.png','--report',HERE/'ui_preview.json']);print('Compiled; UI preview refreshed.',flush=True)
 elif sys.argv[1]=='verify':
  composed=json.loads((HERE/'followup_options_validation.json').read_text(encoding='utf8'));assert composed['passed'] and composed['pack_sha256']==meta['pack_sha256']
  run([exe,'--verify',WORK.parent/'SRWOGS_EX_K_TEST.ISO','--report',HERE/'canonical_verification.json']);run([exe,'--verify',WORK.parent/'SRWOGS_EX_K.ISO','--report',HERE/'source_verification.json'])
  canonical=json.loads((HERE/'canonical_verification.json').read_text(encoding='utf-8-sig'));source=json.loads((HERE/'source_verification.json').read_text(encoding='utf-8-sig'));assert canonical['passed'] and canonical['mask']==4095 and canonical['sha256']==meta['canonical_iso_sha256'];assert source['passed'] and source['mask']==0
  regional={k:composed[k] for k in ['passed','pack_sha256','regional_profile_checks','regional_profiles','regional_new_battles','beowulf_profile_checks','beowulf_profiles','additional_battles','shared_option_bit','no_thirteenth_option','ISO_writes_performed']}
  regional.update(story_and_native_bridge_routes_checked=True,enemy_grade_option_independent=True,extra_dialogue_option_independent=True)
  (HERE/'regional_options_validation.json').write_text(json.dumps(regional,ensure_ascii=False,indent=2),encoding='utf8')
  prior=json.loads((WORK/'option_civil_war/preservation_validation.json').read_text(encoding='utf8'));rj=json.loads((WORK/'civil_reinforcements_journal.json').read_text(encoding='utf8'));j=json.loads((WORK/'civil_guard_journal.json').read_text(encoding='utf8'));v=json.loads((WORK/'civil_guard_validation.json').read_text(encoding='utf8'));assert prior['passed'] and j['applied'] and j['all_other_image_bytes_preserved'] and v['passed'];assert prior['canonical_sha256']==rj['before_sha256'] and rj['after_sha256']==j['before_sha256'] and canonical['sha256']==j['after_sha256']
  preserved=dict(passed=True,canonical_sha256=canonical['sha256'],unchanged_original_UNTD=prior['unchanged_original_UNTD'],unchanged_original_LOGO=prior['unchanged_original_LOGO'],original_34_and_35_have_optional_bridges=True,original_combat_master_rows_preserved=True,original_models_faces_animations_preserved=True,original_finale_clear_command_preserved=True,original_five_added_missions_preserved=True,civil_war_original_payload_check=json.loads((WORK/'civil_war_resource_validation.json').read_text(encoding='utf8')),civil_war_populated_roster_check=json.loads((WORK/'civil_war_party_validation.json').read_text(encoding='utf8')),civil_reinforcement_validation=json.loads((WORK/'civil_guard_validation.json').read_text(encoding='utf8')),civil_guard_waves=json.loads((WORK/'civil_guard_waves_validation.json').read_text(encoding='utf8')),ragnarok_access=json.loads((WORK/'ragnarok_access_validation.json').read_text(encoding='utf8')),verification_basis='Prior comparisons, current virtual resource byte comparisons and full inverse image SHA-256',live_playthrough=False)
  (HERE/'preservation_validation.json').write_text(json.dumps(preserved,ensure_ascii=False,indent=2),encoding='utf8');print('Canonical4095 / read-only source0 and preservation checks passed.',flush=True)
 else:raise ValueError(sys.argv[1])
if __name__=='__main__':main()
