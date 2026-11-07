"""Native loss callbacks must wait for deployment and detect transport loss."""
from validate_civil_war import *
def main():
 p=json.loads((ROOT/'civil_war_prepared.json').read_text(encoding='utf8'));base=ram(Profiles(),4095);master=(DEST/'SHARED.BIN.master').read_bytes();cases=0
 for s in p['scenes']:
  blob=(DEST/s['logo']['file']).read_bytes()
  for started_value in [0,1]:
   for allies in [0,12]:
    for hostage in [0,1]:
     for name,should_lose in [('defeat',not allies),('hostage_loss',not hostage)]:
      v=machine(base,master,blob);v.cpu.allies=allies;v.cpu.alive={HOSTAGE_KEY:bool(hostage)}
      if started_value:v.op(command(0xba,0x10071,0,0))
      nxt,shown=walk(v,blob,s['functions'][name]);assert nxt==(0xffffffff if started_value and should_lose else None),(s['key'],name,started_value,allies,hostage,nxt);cases+=1
 result=dict(passed=True,native_loss_cases=cases,predeployment_does_not_fail=True,transport_loss_fails=True,party_annihilation_fails=True,map_actor_service_is_fixture=True)
 (ROOT/'civil_war_failure_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
