"""Isolated real-SUMO environment on the verified Town10 network.

Training/evaluation sensors use SUMO halting counts with explicit synthetic camera
masking. This is not proof of live YOLO queue accuracy. No CARLA imports or calls.
"""
import hashlib,json,math,uuid
from pathlib import Path
import numpy as np
from services.control.contracts import lane_groups,phase_mapping,permanent_mask
from services.control.estimator import MissingStateEstimator
from p2.controller_gate import actor_vectors

ROOT=Path(__file__).resolve().parents[1]

class Town10Environment:
 def __init__(self,network,routes,sumo_binary,seed=1,fault_rate=0,horizon=240,output=None):
  import traci
  self.traci=traci;self.network=Path(network);self.routes=Path(routes);self.binary=str(sumo_binary)
  self.config=json.loads((ROOT/'configs/action_mapping.json').read_text(encoding='utf-8'))
  self.schema=json.loads((ROOT/'configs/observation_schema.json').read_text(encoding='utf-8'))
  self.runtime=json.loads((ROOT/'configs/runtime_mapping.json').read_text(encoding='utf-8'))
  self.network_hash=hashlib.sha256(self.network.read_bytes()).hexdigest()
  if self.network_hash!=self.runtime['network_sha256']:raise ValueError('Network hash mismatch.')
  self.junctions=self.config['junctions'];self.seed=seed;self.rng=np.random.RandomState(seed+1000)
  self.fault_rate=fault_rate;self.horizon=horizon;self.output=Path(output) if output else None
  self.connection=None;self.label='aegis_isolated_'+uuid.uuid4().hex
  self.programs={p['tls_id']:p for p in self.runtime['programs']}
  self.groups={j['alias']:lane_groups(j) for j in self.junctions}
  self.maps={j['alias']:phase_mapping(j) for j in self.junctions}
  self.structural={j['alias']:permanent_mask(j) for j in self.junctions}
  calibration=json.loads((ROOT/'configs/lane_regions.coverage.json').read_text(encoding='utf-8'))
  self.sensor_regions={r['lane_id']:r for c in calibration['cameras'] for r in c['regions']}
  self.transitions=self.review_paths()
  self.estimator=MissingStateEstimator();self.events=[];self.closed=False
  self.current={j['alias']:0 for j in self.junctions};self.elapsed={j['alias']:0. for j in self.junctions}
  self.pending={};self.last_queues=None;self.waiting_vehicle_seconds=0.;self.fuel_mg=0.;self.teleports=0;self.arrived=0;self.switches=0

 def review_paths(self):
  result={}
  for j in self.junctions:
   program=self.programs[j['sumo_tls_id']];phases=program['phases'];mapping=self.maps[j['alias']]
   table={}
   for action,green in mapping.items():
    if green is None:continue
    # The verified converter creates green/yellow/all-red triples.
    if green+2>=len(phases):raise ValueError('Missing clearance triple.')
    yellow,red=phases[green+1],phases[green+2]
    if not any(c in yellow['state'] for c in 'yY') or any(c in yellow['state'] for c in 'gG') or not all(c in 'rR' for c in red['state']):
     raise ValueError('Clearance program is not yellow then all-red.')
    for target,target_green in mapping.items():
     if target_green is not None and target!=action:
      table[(action,target)]=[(green+1,max(3.,yellow['duration_s'])),(green+2,max(2.,red['duration_s'])),(target_green,3600.)]
   result[j['alias']]=table
  return result

 def start(self):
  args=[self.binary,'-n',str(self.network.resolve()),'-r',str(self.routes.resolve()),'--step-length','0.5',
   '--seed',str(self.seed),'--no-step-log','true','--duration-log.disable','true','--no-warnings','true','--time-to-teleport','-1']
  if self.output:
   self.output.mkdir(parents=True,exist_ok=True);args+=['--tripinfo-output',str((self.output/'trips.xml').resolve())]
  self.traci.start(args,label=self.label,verbose=False);self.connection=self.traci.getConnection(self.label)
  for j in self.junctions:self.set_raw(j['alias'],self.maps[j['alias']][0],3600,'initial')
  return self.observe()

 def set_raw(self,jid,index,duration,reason):
  j=next(j for j in self.junctions if j['alias']==jid);tls=j['sumo_tls_id']
  self.connection.trafficlight.setPhase(tls,index);self.connection.trafficlight.setPhaseDuration(tls,duration)
  observed=self.connection.trafficlight.getPhase(tls)
  expected=self.programs[tls]['phases'][index]['state']
  actual=self.connection.trafficlight.getRedYellowGreenState(tls)
  if observed!=index or actual!=expected:raise RuntimeError('Independent signal read-back mismatch.')
  self.events.append({'sim_time_s':self.connection.simulation.getTime(),'junction':jid,'phase':index,'reason':reason,'observed_phase':observed,'observed_state':actual})

 def masks(self):
  result={}
  for j in self.junctions:
   jid=j['alias'];mask=self.structural[jid].copy()
   if jid in self.pending or self.elapsed[jid]<j['min_green_s']:
    mask[:]=False;mask[self.pending[jid]['target'] if jid in self.pending else self.current[jid]]=True
   elif self.elapsed[jid]>=j['max_green_s']:
    mask[self.current[jid]]=False
   result[jid]=mask
  return result

 def observe(self):
  packets={};beliefs={};context={};t=self.connection.simulation.getTime()
  for j in self.junctions:
   jid=j['alias'];drop=self.rng.random()<self.fault_rate
   served=set(j['policy_action_phase_mapping'][str(self.current[jid])]['served_lanes']) if jid not in self.pending else set()
   packets[jid]=[];beliefs[jid]={}
   for lane in j['incoming_lane_ids']:
    region=self.sensor_regions[lane];lower,upper=region['sumo_lane_interval_m']
    raw=sum(lower<=self.connection.vehicle.getLanePosition(v)<=upper for v in self.connection.lane.getLastStepVehicleIDs(lane))
    missing=drop or not region['usable_for_counts']
    observed=None if missing else raw
    belief=self.estimator.update_lane(lane,observed,t,5,lane in served)
    packets[jid].append({'lane_id':lane,'observed_count':observed,'missing':missing,'age_s':belief.observation_age_s})
    beliefs[jid][lane]=belief.estimated_queue
   context[jid]={'green_action_index':self.current[jid],'elapsed_green_s':self.elapsed[jid],'neighbor_inflow':[0.]*4}
  # No hidden reference state is passed to actor_vectors or the actor.
  obs=actor_vectors(packets,beliefs,context,self.config,self.schema)
  return {jid:np.asarray(value,dtype=np.float32) for jid,value in obs.items()},self.masks()

 def request_actions(self,actions):
  masks=self.masks()
  for jid,index in actions.items():
   if isinstance(index,bool) or not isinstance(index,(int,np.integer)) or not 0<=index<4 or not masks[jid][index]:raise ValueError('Illegal masked action.')
   if jid not in self.pending and index!=self.current[jid]:
    stages=list(self.transitions[jid][(self.current[jid],index)]);raw,duration=stages.pop(0)
    self.pending[jid]={'target':int(index),'stages':stages,'remaining':duration}
    self.set_raw(jid,raw,duration,'yellow');self.switches+=1
 def step(self,actions):
  self.request_actions(actions)
  for _ in range(10):
   self.connection.simulationStep()
   self.waiting_vehicle_seconds+=.5*sum(self.connection.lane.getLastStepHaltingNumber(lane) for j in self.junctions for lane in j['incoming_lane_ids'])
   self.arrived+=self.connection.simulation.getArrivedNumber();self.teleports+=self.connection.simulation.getStartingTeleportNumber()
   self.fuel_mg+=.5*sum(self.connection.vehicle.getFuelConsumption(v) for v in self.connection.vehicle.getIDList())
   for jid in self.current:
    if jid in self.pending:
     pending=self.pending[jid];pending['remaining']-=.5
     if pending['remaining']<=0:
      raw,duration=pending['stages'].pop(0)
      self.set_raw(jid,raw,duration,'clearance' if pending['stages'] else 'target_green')
      if not pending['stages']:
       self.current[jid]=pending['target'];self.elapsed[jid]=0;del self.pending[jid]
      else:pending['remaining']=duration
    else:
     self.elapsed[jid]+=.5
     config=next(j for j in self.junctions if j['alias']==jid)
     if self.elapsed[jid]>=config['max_green_s']:
      legal=np.flatnonzero(self.masks()[jid])
      target=int(next((v for v in legal if v>self.current[jid]),legal[0]))
      self.request_actions({jid:target})
  queues=sum(self.connection.lane.getLastStepHaltingNumber(lane) for j in self.junctions for lane in j['incoming_lane_ids'])
  reward=-queues/360.
  obs,masks=self.observe();done=self.connection.simulation.getTime()>=self.horizon
  return obs,masks,reward,done

 def metrics(self):
  return {'waiting_vehicle_seconds':self.waiting_vehicle_seconds,'completed_trips':self.arrived,
   'remaining_vehicles':self.connection.simulation.getMinExpectedNumber(),'active_vehicles':len(self.connection.vehicle.getIDList()),
   'fuel_mg':self.fuel_mg,'teleports':self.teleports,'switches':self.switches,'sim_time_s':self.connection.simulation.getTime()}

 def close(self):
  if self.connection is not None:
   self.connection.close();self.connection=None
  if self.output:(self.output/'signal_events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.events),encoding='utf-8')
  self.closed=True
