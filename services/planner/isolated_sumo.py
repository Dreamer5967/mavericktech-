"""Independent SUMO recovery rollouts initialized only from observed beliefs.

Three real worker processes share belief samples and estimated arrivals. No live
TraCI connection, exact vehicle state or hidden demand is passed to workers.
"""
from concurrent.futures import ProcessPoolExecutor,wait
import multiprocessing
import hashlib,json,math,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np


def pressure_actions(config,obs,masks):
 result={}
 for j in config['junctions']:
  jid=j['alias'];groups=j['lane_slot_aggregation'];scores={}
  for slot,entry in j['policy_action_phase_mapping'].items():
   if entry is None or not masks[jid][int(slot)]:continue
   served=set(entry['served_lanes']);score=0
   for index in range(4):
    lanes=groups.get('slot_'+str(index)) or []
    if set(lanes)&served:score+=float(obs[jid][index])*len(lanes)
   scores[int(slot)]=score
  if not scores:raise ValueError('No legal pressure action.')
  result[jid]=max(scores,key=lambda action:(scores[action],-action))
 return result


def estimated_routes(network,config,obs,seed,horizon,path):
 root=ET.parse(network).getroot();edges={e.get('id'):e for e in root.findall('edge') if e.get('function')!='internal'}
 graph={edge:set() for edge in edges};lanes={l.get('id'):(edge,l) for edge,e in edges.items() for l in e.findall('lane')}
 for c in root.findall('connection'):
  if c.get('from') in edges and c.get('to') in edges:graph[c.get('from')].add(c.get('to'))
 def onward(edge):
  queue=[(edge,[edge])]
  while queue:
   last,route=queue.pop(0)
   if len(route)>=4:return route
   for child in sorted(graph[last]):
    if child not in route:queue.append((child,route+[child]))
  raise ValueError('No estimated shadow route from '+edge)
 output=ET.Element('routes');ET.SubElement(output,'vType',id='shadow',vClass='passenger',length='4.69',minGap='2.5',maxSpeed='13.9')
 rng=np.random.RandomState(seed);departures=[];route_index=0
 for j in config['junctions']:
  for slot in range(4):
   group=j['lane_slot_aggregation'].get('slot_'+str(slot)) or []
   for lane in group:
    edge,element=lanes[lane];route=onward(edge);route_id='r'+str(route_index);route_index+=1
    ET.SubElement(output,'route',id=route_id,edges=' '.join(route))
    queued=min(5,max(0,int(round(float(obs[j['alias']][slot])*15))))
    length=float(element.get('length'))
    for number in range(queued):departures.append((0,route_id,element.get('index'),max(.1,length-8-number*6)))
    # Common estimated arrival process for every candidate, not actual scenario demand.
    for t in range(1,horizon):
     if rng.random()<.10:departures.append((t,route_id,element.get('index'),.1))
 for index,(depart,route,lane,position) in enumerate(sorted(departures)):
  ET.SubElement(output,'vehicle',id='belief_'+str(index),type='shadow',route=route,depart=str(depart),departLane=lane,departPos=str(position),departSpeed='0')
 ET.ElementTree(output).write(path,encoding='utf-8',xml_declaration=True)


def rollout(payload):
 import torch
 from training.town10_environment import Town10Environment
 from training.mappo.actor import ActorMLP
 torch.set_num_threads(1);started=time.monotonic()
 obs={j:np.asarray(v,dtype=np.float32) for j,v in payload['belief'].items()}
 masks={j:np.asarray(v,dtype=bool) for j,v in payload['masks'].items()}
 config=json.loads((Path(__file__).resolve().parents[2]/'configs/action_mapping.json').read_text(encoding='utf-8'))
 actor=None
 if payload['candidate']=='learned':
  checkpoint=Path(payload['checkpoint'])
  if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!=payload['checkpoint_sha256']:raise ValueError('Shadow model hash mismatch.')
  actor=ActorMLP(25,4,64);state=torch.load(checkpoint,map_location='cpu',weights_only=True);actor.load_state_dict(state['actor_state_dict']);actor.eval()
 with tempfile.TemporaryDirectory(prefix='aegis-shadow-owned-') as directory:
  routes=Path(directory)/'belief.rou.xml';estimated_routes(payload['network'],config,obs,payload['seed'],payload['horizon'],routes)
  env=Town10Environment(payload['network'],routes,payload['sumo'],seed=payload['seed'],horizon=payload['horizon'])
  try:
   env.start()
   for j in config['junctions']:
    jid=j['alias'];current=int(np.argmax(obs[jid][12:16]));current=current if env.structural[jid][current] else 0
    env.current[jid]=current;env.elapsed[jid]=max(0,float(obs[jid][16])*60)
    env.set_raw(jid,env.maps[jid][current],3600,'belief_initial_phase')
   first=None;done=False
   while not done:
    if payload['candidate']=='pressure':actions=pressure_actions(config,obs,masks)
    elif actor is not None:actions={jid:actor.get_action(vector,masks[jid],deterministic=True)[0] for jid,vector in obs.items()}
    else:
     actions={}
     for jid,mask in masks.items():
      valid=np.flatnonzero(mask);current=env.current[jid]
      target=int(next((v for v in valid if v>current),valid[0])) if env.elapsed[jid]>=30 else current
      actions[jid]=target if target in valid else int(valid[0])
    if first is None:first=dict(actions)
    obs,masks,reward,done=env.step(actions)
   return {'candidate':payload['candidate'],'first_actions':first,'cost':env.waiting_vehicle_seconds,
    'wall_ms':(time.monotonic()-started)*1000,'status':'COMPLETED','mode':'BELIEF_INITIALIZED_SHADOW_SUMO',
    'belief_hash':payload['belief_hash'],'sample_seed':payload['seed'],'horizon_s':payload['horizon']}
  finally:env.close()


class IsolatedSUMOPlanner:
 def __init__(self,network,sumo,checkpoint,checkpoint_sha256,horizon=20,deadline_s=5):
  self.base={'network':str(Path(network).resolve()),'sumo':str(Path(sumo).resolve()),'checkpoint':str(Path(checkpoint).resolve()),
    'checkpoint_sha256':checkpoint_sha256,'horizon':horizon}
  self.deadline=deadline_s;self.pool=ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'))
 def plan(self,obs,masks,run_id,revision,sim_time_s):
  if set(obs)!=set(masks):raise ValueError('Belief and mask junction sets differ.')
  for jid,value in obs.items():
   vector=np.asarray(value);mask=np.asarray(masks[jid])
   if vector.shape!=(25,) or not np.isfinite(vector).all():raise ValueError('Finite 25-dimensional beliefs required.')
   if mask.shape!=(4,) or mask.dtype!=np.bool_ or not mask.any():raise ValueError('No valid boolean action mask.')
  started=time.monotonic();belief={j:np.asarray(v).tolist() for j,v in obs.items()}
  token=hashlib.sha256(json.dumps(belief,sort_keys=True).encode()).hexdigest()
  common={**self.base,'belief':belief,'belief_hash':token,'masks':{j:np.asarray(v).tolist() for j,v in masks.items()},'seed':10000+revision}
  jobs={self.pool.submit(rollout,{**common,'candidate':candidate}):candidate for candidate in ['learned','conservative','pressure']}
  done,pending=wait(jobs,timeout=self.deadline);results=[]
  for future in done:
   try:results.append(future.result())
   except Exception as exc:results.append({'candidate':jobs[future],'status':'UNAVAILABLE','error':type(exc).__name__+': '+str(exc)})
  for future in pending:future.cancel();results.append({'candidate':jobs[future],'status':'TIMEOUT'})
  available=[r for r in results if r['status']=='COMPLETED']
  best=min(available,key=lambda row:row['cost']) if available else None
  actions=best['first_actions'] if best else {jid:int(np.flatnonzero(mask)[0]) for jid,mask in masks.items()}
  return {'run_id':run_id,'based_on_revision':revision,'expires_at_sim_s':sim_time_s+5,
   'first_actions':actions,'selected_candidate':best['candidate'] if best else 'masked_fallback',
   'candidate_results':results,'belief_hash':token,'wall_ms':(time.monotonic()-started)*1000,'actuation_permitted':False}
 def close(self):self.pool.shutdown(wait=True,cancel_futures=True)
