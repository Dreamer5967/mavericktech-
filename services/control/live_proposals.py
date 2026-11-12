"""Bounded policy-test adapter. The bridge alone advances clocks and applies phases.

Policy computation runs outside the tick loop. Only camera counts and public
signal context enter the actor; evaluator vehicle references are never accepted.
"""
import hashlib,json,queue,threading,time
from pathlib import Path
from urllib.request import urlopen
import numpy as np
from services.control.inference_entrypoint import AEGISInferenceEngine
from services.control.contracts import permanent_mask
from services.control.estimator import MissingStateEstimator
from p2.controller_gate import actor_vectors

BOUNDED_CAMERA_FRESHNESS_S=5.0


class BoundedPolicyAdapter:
 def __init__(self,checkpoint,sha256,output,execute=False):
  root=Path(__file__).resolve().parents[2]
  self.config=json.loads((root/'configs/action_mapping.json').read_text(encoding='utf-8'))
  self.schema=json.loads((root/'configs/observation_schema.json').read_text(encoding='utf-8'))
  self.runtime=json.loads((root/'configs/runtime_mapping.json').read_text(encoding='utf-8'))
  self.model=AEGISInferenceEngine(checkpoint_path=str(checkpoint),expected_checkpoint_sha256=sha256,use_planner=False)
  self.programs={p['tls_id']:p for p in self.runtime['programs']};self.estimator=MissingStateEstimator()
  self.output=Path(output);self.execute=execute;self.inbox=queue.Queue(maxsize=1)
  self.lock=threading.Lock();self.context=None;self.stop=threading.Event();self.thread=None
  self.phase_seen={};self.green_seen={};self.pending={};self.last_revision={};self.events=[];self.errors=[]
  self.proposals=0;self.applied=0;self.run_id=None
  self.rejections={}
  # Independently verify every source-green clearance triple before clock ownership.
  for j in self.config['junctions']:
   phases=self.programs[j['sumo_tls_id']]['phases']
   for entry in j['policy_action_phase_mapping'].values():
    if entry is None:continue
    i=entry['sumo_phase_index'];yellow=phases[i+1]['state'];red=phases[i+2]['state']
    if not any(c in yellow for c in 'yY') or any(c in yellow for c in 'gG') or not all(c in 'rR' for c in red):
     raise ValueError('Unreviewed green/yellow/all-red program structure.')

 def set_phase(self,traci,jid,phase,duration,now,reason):
  cfg=next(j for j in self.config['junctions'] if j['alias']==jid);tls=cfg['sumo_tls_id']
  traci.trafficlight.setPhase(tls,phase);traci.trafficlight.setPhaseDuration(tls,duration)
  actual=traci.trafficlight.getRedYellowGreenState(tls);expected=self.programs[tls]['phases'][phase]['state']
  if actual!=expected:raise RuntimeError('Policy signal read-back mismatch.')
  self.events.append({'sim_time_s':now,'junction':jid,'phase':phase,'state':actual,'event':reason})

 def before_tick(self,sync,traci):
  now=traci.simulation.getTime();context={}
  for j in self.config['junctions']:
   jid=j['alias'];phase=traci.trafficlight.getPhase(j['sumo_tls_id'])
   if self.phase_seen.get(jid,(None,))[0]!=phase:self.phase_seen[jid]=(phase,now)
   reverse={entry['sumo_phase_index']:int(slot) for slot,entry in j['policy_action_phase_mapping'].items() if entry is not None}
   if phase in reverse:self.green_seen[jid]=reverse[phase]
   context[jid]={'raw_phase':phase,'green':phase in reverse,'green_action_index':self.green_seen.get(jid,0),
    'elapsed_green_s':now-self.phase_seen[jid][1] if phase in reverse else 0,'neighbor_inflow':[0.]*4}
   if jid in self.pending and now>=self.pending[jid]['until']:
    pending=self.pending[jid];raw,duration=pending['stages'].pop(0)
    self.set_phase(traci,jid,raw,duration,now,'clearance_stage' if pending['stages'] else 'target_green')
    if pending['stages']:pending['until']=now+duration
    else:del self.pending[jid]
  with self.lock:self.context={'sim_time_s':now,'junctions':context}
  if self.thread is None:
   self.thread=threading.Thread(target=self.compute,daemon=True);self.thread.start()
  try:proposal=self.inbox.get_nowait()
  except queue.Empty:return
  if not self.execute:return
  def reject(reason,jid='*'):
   key=jid+':'+reason
   self.rejections[key]=self.rejections.get(key,0)+1
  if now>proposal['expires_at_sim_s']:
   reject('expired');return
  for j in self.config['junctions']:
   jid=j['alias'];target=proposal['proposed'].get(jid);source=proposal['camera_sources'][jid];state=context[jid]
   if target is None: reject('no_target',jid);continue
   if jid in self.pending: reject('clearance_pending',jid);continue
   if not state['green']: reject('not_green_phase',jid);continue
   if state['elapsed_green_s']<j['min_green_s']: reject('minimum_green',jid);continue
   if proposal['expected_phases'][jid]!=state['raw_phase']: reject('phase_changed',jid);continue
   if source['status']!='fresh' or source['time'] is None or not 0<=now-source['time']<=BOUNDED_CAMERA_FRESHNESS_S: reject('camera_stale',jid);continue
   if proposal['revision']<=self.last_revision.get((proposal['run_id'],jid),-1): reject('duplicate_revision',jid);continue
   self.last_revision[(proposal['run_id'],jid)]=proposal['revision']
   if target==state['raw_phase']: reject('target_equals_current',jid);continue
   phases=self.programs[j['sumo_tls_id']]['phases'];current=state['raw_phase']
   # Public green phase to reviewed yellow/all-red to selected target. No direct green jump.
   yellow_duration=max(j['yellow_s'],phases[current+1]['duration_s'])
   red_duration=max(j['all_red_s'],phases[current+2]['duration_s'])
   self.set_phase(traci,jid,current+1,yellow_duration,now,'policy_yellow')
   self.pending[jid]={'stages':[(current+2,red_duration),(target,phases[target]['duration_s'])],'until':now+yellow_duration}
   self.applied+=1

 def compute(self):
  try:
   while not self.stop.is_set():
    with self.lock:context=self.context
    if context is None:self.stop.wait(.2);continue
    try:
     with urlopen('http://127.0.0.1:8765/api/v1/snapshot',timeout=1) as response:snapshot=json.load(response)
    except OSError:self.stop.wait(.2);continue
    if self.run_id is None:self.run_id=snapshot['run_id']
    if snapshot['run_id']!=self.run_id:raise RuntimeError('Observation run changed; stale proposals refused.')
    cameras={c['camera_id']:c for c in snapshot['cameras']};packets={};beliefs={};masks={};sources={}
    for j in self.config['junctions']:
     jid=j['alias'];camera=cameras[j['camera_id']];counts=camera.get('lane_counts') or {};state=context['junctions'][jid]
     packets[jid]=[];beliefs[jid]={};sources[jid]={'time':camera['source_sim_time_s'],'status':camera['status']}
     for lane in j['incoming_lane_ids']:
      count=counts.get(lane);is_green=state['green'] and lane in j['policy_action_phase_mapping'][str(state['green_action_index'])]['served_lanes']
      belief=self.estimator.update_lane(lane,count,context['sim_time_s'],.5,is_green)
      age=max(0,context['sim_time_s']-camera['source_sim_time_s']) if count is not None and camera['source_sim_time_s'] is not None else belief.observation_age_s
      packets[jid].append({'lane_id':lane,'observed_count':count,'missing':count is None,'age_s':age})
      beliefs[jid][lane]=belief.estimated_queue
     mask=permanent_mask(j,4)
     if not state['green'] or state['elapsed_green_s']<j['min_green_s']:
      mask[:]=False;mask[state['green_action_index']]=True
     masks[jid]=mask
    vectors=actor_vectors(packets,beliefs,context['junctions'],self.config,self.schema)
    result=self.model.step({j:np.asarray(v,dtype=np.float32) for j,v in vectors.items()},masks,self.run_id,snapshot['state_revision'],context['sim_time_s'])
    proposal={'run_id':self.run_id,'revision':snapshot['state_revision'],'expires_at_sim_s':context['sim_time_s']+2,
     'proposed':result['proposed_sumo_phases'],'camera_sources':sources,
     'expected_phases':{j:state['raw_phase'] for j,state in context['junctions'].items()}}
    self.proposals+=1
    try:self.inbox.get_nowait()
    except queue.Empty:pass
    self.inbox.put_nowait(proposal);self.stop.wait(.5)
  except Exception as exc:self.errors.append(type(exc).__name__+': '+str(exc));self.stop.set()

 def close(self):
  self.stop.set()
  if self.thread:self.thread.join(timeout=5)
  self.output.mkdir(parents=True,exist_ok=True)
  (self.output/'policy_events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.events),encoding='utf-8')
  summary={'mode':'BOUNDED_POLICY_TEST' if self.execute else 'READ_ONLY_POLICY_TEST','computed_proposals':self.proposals,
   'transitions_started':self.applied,'camera_freshness_window_s':BOUNDED_CAMERA_FRESHNESS_S,
   'rejections':self.rejections,'errors':self.errors,'automatic_deployment_enabled':False}
  (self.output/'policy_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
  return summary
