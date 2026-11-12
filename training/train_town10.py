"""Train and evaluate MAPPO on isolated real SUMO; no CARLA connection."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from training.town10_environment import Town10Environment
from training.mappo.actor import ActorMLP
from training.mappo.critic import CriticMLP
from training.mappo.trainer import MAPPOTrainer
from training.mappo.buffer import RolloutBuffer


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def choose(actor,obs,masks,controller,current,elapsed):
 actions={}
 for jid,vector in obs.items():
  legal=np.flatnonzero(masks[jid])
  if not len(legal):raise ValueError('No legal action.')
  if controller=='fixed_time':
   target=int(next((i for i in legal if i>current[jid]),legal[0])) if elapsed[jid]>=30 else current[jid]
   actions[jid]=target if target in legal else int(legal[0])
  else:actions[jid]=actor.get_action(vector,masks[jid],deterministic=True)[0]
 return actions


def evaluate(actor,args,controller,seeds,faults,prefix):
 rows=[]
 for fault in faults:
  for seed in seeds:
   out=args.output/(prefix+'_'+controller+'_s'+str(seed)+'_f'+str(fault))
   env=Town10Environment(args.network,args.routes,args.sumo,seed=seed,fault_rate=fault,horizon=args.horizon,output=out)
   try:
    obs,masks=env.start();done=False
    while not done:
     actions=choose(actor,obs,masks,controller,env.current,env.elapsed)
     obs,masks,reward,done=env.step(actions)
    rows.append({'controller':controller,'seed':seed,'fault_rate':fault,'split':prefix,
     'network_sha256':env.network_hash,'observation_source':'SUMO_ROI_OCCUPANCY_WITH_SYNTHETIC_CAMERA_DROPOUT',
     **env.metrics()})
   finally:env.close()
   print('EVALUATION',json.dumps(rows[-1]),flush=True)
 return rows


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--network',type=Path,required=True);p.add_argument('--routes',type=Path,required=True)
 p.add_argument('--sumo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--episodes',type=int,default=40);p.add_argument('--horizon',type=int,default=240)
 args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
 source_names=['training/town10_environment.py','training/train_town10.py']
 source_hashes={name:digest(Path(__file__).resolve().parents[1]/name) for name in source_names}
 for name in source_names:
  target=args.output/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((Path(__file__).resolve().parents[1]/name).read_bytes())
 torch.set_num_threads(2);torch.manual_seed(42);np.random.seed(42)
 actor=ActorMLP(25,4,64);critic=CriticMLP(100,128);trainer=MAPPOTrainer(actor,critic,ppo_epochs=4,batch_size=24)
 records=[];initial={k:v.clone() for k,v in actor.state_dict().items()};started=time.monotonic()
 for episode in range(args.episodes):
  seed=1+episode%5;fault=[0,.1,.2,.4][(episode//5)%4]
  env=Town10Environment(args.network,args.routes,args.sumo,seed=seed,fault_rate=fault,horizon=args.horizon)
  steps=args.horizon//5;buffer=RolloutBuffer(steps,4,25,100,4)
  try:
   obs,masks=env.start();total=0
   for step in range(steps):
    order=['J1','J2','J3','J4'];vectors=np.stack([obs[j] for j in order]);joint=vectors.reshape(-1)
    pairs=[actor.get_action(obs[j],masks[j]) for j in order];actions={j:pairs[i][0] for i,j in enumerate(order)}
    mask_array=np.stack([masks[j] for j in order])
    with torch.no_grad():value=critic(torch.as_tensor(joint).unsqueeze(0)).item()
    obs,masks,reward,done=env.step(actions);total+=reward
    buffer.insert(vectors,joint,np.array([a[0] for a in pairs]),mask_array,np.array([a[1] for a in pairs]),reward,value,done)
   buffer.compute_returns_and_advantages(0.0);metrics=trainer.train_step(buffer)
   row={'episode':episode+1,'seed':seed,'fault_rate':fault,'mean_reward':total/steps,**metrics,**env.metrics()};records.append(row)
  finally:env.close()
  (args.output/'learning_curve.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
  print('TRAIN',episode+1,'reward',round(row['mean_reward'],4),'elapsed_s',round(time.monotonic()-started,1),flush=True)
 checkpoint=args.output/'mappo_town10_offline.pt';torch.save({'actor_state_dict':actor.state_dict(),'critic_state_dict':critic.state_dict(),'obs_dim':25,'action_dim':4},checkpoint)
 changed=any(not torch.equal(initial[k],v) for k,v in actor.state_dict().items())
 dev=evaluate(actor,args,'mappo',[6,7],[0,.2],'dev')
 rows=evaluate(actor,args,'fixed_time',[18,19,20],[0,.1,.2,.4],'test')+evaluate(actor,args,'mappo',[18,19,20],[0,.1,.2,.4],'test')
 manifest={'status':'TRAINED_SUMO_OFFLINE_CAMERA_UNVALIDATED','algorithm':'MAPPO','network_sha256':digest(args.network),
  'routes_sha256':digest(args.routes),'checkpoint_sha256':digest(checkpoint),'checkpoint_path':str(checkpoint.resolve()),
  'action_mapping_sha256':digest(Path(__file__).resolve().parents[1]/'configs/action_mapping.json'),
  'observation_schema_sha256':digest(Path(__file__).resolve().parents[1]/'configs/observation_schema.json'),
  'train_seeds':[1,2,3,4,5],'dev_seeds':[6,7],'test_seeds':[18,19,20],'episodes':args.episodes,
  'source_sha256':source_hashes,'environment_decisions':args.episodes*steps,'gradient_parameters_changed':changed,'torch_version':torch.__version__,
  'observation_source':'SUMO_ROI_OCCUPANCY_WITH_SYNTHETIC_CAMERA_DROPOUT','actuation_permitted':False,
  'limitations':['Not a live camera-domain validation.','Training budget is limited; no improvement is assumed.','Recovery evaluation is separate.']}
 (args.output/'model_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 (args.output/'traffic_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');(args.output/'dev_results.json').write_text(json.dumps(dev,indent=2),encoding='utf-8')
 print('COMPLETE',json.dumps(manifest),flush=True)

if __name__=='__main__':main()
