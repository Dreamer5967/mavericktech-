"""Inspect a SUMO configuration in an INDEPENDENT process, not the live co-sim."""
import argparse,json,os,sys
from pathlib import Path

def main():
    if os.environ.get('SUMO_HOME'):sys.path.append(str(Path(os.environ['SUMO_HOME'])/'tools'))
    import traci
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('sumocfg');p.add_argument('--out',default='tls_inventory.json');a=p.parse_args()
    cfg=Path(a.sumocfg).resolve()
    if not cfg.is_file():raise SystemExit('Config not found: '+str(cfg))
    traci.start(['sumo','-c',str(cfg),'--no-step-log','true'],label='inventory')
    c=traci.getConnection('inventory')
    try:
        rows=[]
        for tls in c.trafficlight.getIDList():
            rows.append({'tls_id':tls,'controlled_lanes':list(c.trafficlight.getControlledLanes(tls)),
                         'programs':[{'program_id':p.programID,'phases':[{'duration_s':x.duration,'state':x.state} for x in p.phases]} for p in c.trafficlight.getAllProgramLogics(tls)]})
        Path(a.out).write_text(json.dumps({'sumo_version':c.getVersion(),'tls':rows},indent=2))
        print('Wrote',len(rows),'signal systems. Check connectivity and geometry manually; count alone is not qualification.')
    finally:c.close()
if __name__=='__main__':main()
