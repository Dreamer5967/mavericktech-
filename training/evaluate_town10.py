"""Matched real-SUMO evaluation with belief-initialized isolated recovery workers."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np,torch
from training.town10_environment import Town10Environment
from training.mappo.actor import ActorMLP
from training.train_town10 import choose
from services.planner.isolated_sumo import IsolatedSUMOPlanner


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['network','routes','sumo','checkpoint','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--seeds',default='18,19,20');p.add_argument('--faults',default='0,0.1,0.2,0.4');p.add_argument('--horizon',type=int,default=240)
 args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1)
 digest=hashlib.sha256(args.checkpoint.read_bytes()).hexdigest();actor=ActorMLP(25,4,64)
 actor.load_state_dict(torch.load(args.checkpoint,map_location='cpu',weights_only=True)['actor_state_dict']);actor.eval()
 planner=IsolatedSUMOPlanner(args.network,args.sumo,args.checkpoint,digest,horizon=20,deadline_s=5)
 rows=[];plans=[]
 try:
  for fault in [float(x) for x in args.faults.split(',')]:
   for seed in [int(x) for x in args.seeds.split(',')]:
    for controller in ['fixed_time','mappo','mappo_recovery']:
     out=args.output/(controller+'_s'+str(seed)+'_f'+str(fault))
     env=Town10Environment(args.network,args.routes,args.sumo,seed,fault,args.horizon,out)
     try:
      obs,masks=env.start();done=False;revision=0;next_plan=30;used=0;timeouts=0
      while not done:
       revision+=1;sim=env.connection.simulation.getTime()
       actions=choose(actor,obs,masks,'fixed_time' if controller=='fixed_time' else 'mappo',env.current,env.elapsed)
       # Recovery budget/trigger is declared and identical across matched episodes.
       if controller=='mappo_recovery' and sim>=next_plan and any(np.any(v[4:8]>.5) for v in obs.values()) and any(np.count_nonzero(mask)>1 for mask in masks.values()):
        plan=planner.plan(obs,masks,out.name,revision,sim);next_plan=sim+60
        for jid,index in plan['first_actions'].items():
         if not masks[jid][index]:raise ValueError('Planner proposed a masked action.')
        actions=plan['first_actions'];used+=plan['selected_candidate']!='masked_fallback';timeouts+=plan['selected_candidate']=='masked_fallback'
        plan.update(controller=controller,seed=seed,fault_rate=fault,executed_first_actions=dict(actions));plans.append(plan)
        (args.output/'planner_results.json').write_text(json.dumps(plans,indent=2),encoding='utf-8')
       obs,masks,reward,done=env.step(actions)
      row={'controller':controller,'seed':seed,'fault_rate':fault,'checkpoint_sha256':digest,
       'network_sha256':env.network_hash,'source':'REAL_SUMO_ROI_SENSOR_MODEL','recovery_plans_applied':used,'planner_fallbacks':timeouts,**env.metrics()}
      rows.append(row);print('MATCHED_RESULT',json.dumps(row),flush=True)
      (args.output/'traffic_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
     finally:env.close()
 finally:planner.close()

if __name__=='__main__':main()
