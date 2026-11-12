"""Bounded, explicitly approved clock owner with read-only post-tick checks."""
import argparse
import ast
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def check_lights(synchronization, helper, selected):
    common=synchronization.sumo.traffic_light_ids & synchronization.carla.traffic_light_ids
    missing=sorted(set(selected)-common)
    mismatches=[]
    for landmark in sorted(set(selected)&common):
        expected=helper.get_carla_traffic_light_state(synchronization.sumo.get_traffic_light_state(landmark))
        actual=synchronization.carla.get_traffic_light_state(landmark)
        if actual!=expected:
            mismatches.append({'opendrive_id':landmark,'expected':str(expected),'actual':str(actual)})
    return {'missing_signal_ids':missing,'light_mismatches':mismatches}


def run(scenario, config, seconds, output, policy_checkpoint=None, policy_sha256=None):
    if os.environ.get('AEGIS_APPROVE_LIVE_COSIM')!='yes':
        raise RuntimeError('Explicit approval for live clock advancement is required.')
    if (policy_checkpoint is None)!=(policy_sha256 is None):
        raise ValueError('Read-only policy diagnostics require both checkpoint path and SHA256.')
    import carla
    import sumolib
    import traci
    traci.sumolib=sumolib  # Legacy bundled bridge module alias, process-local.
    source=Path('/workspace/aegis/carla/Co-Simulation/Sumo/run_synchronization.py')
    sys.path.insert(0,str(source.parent))
    spec=importlib.util.spec_from_file_location('aegis_reviewed_bridge',source)
    bridge=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    args=SimpleNamespace(sumo_cfg_file=str(scenario),step_length=0.05,sumo_host=None,
                         sumo_port=None,sumo_gui=False,client_order=1,carla_host='127.0.0.1',
                         carla_port=2000,tls_manager='sumo',sync_vehicle_color=False,sync_vehicle_lights=False)
    tree=ast.parse(source.read_text(encoding='utf-8'))
    loop=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='synchronization_loop')
    required={node.attr for node in ast.walk(loop) if isinstance(node,ast.Attribute) and
              isinstance(node.value,ast.Name) and node.value.id=='args'}
    if required-set(vars(args)):
        raise RuntimeError('Bundled bridge has unreviewed argument requirements: '+str(required-set(vars(args))))
    selected={signal for camera in config['cameras'] for signal in camera['opendrive_signal_ids']}
    output.mkdir(parents=True,exist_ok=False)
    policy=None
    if policy_checkpoint is not None:
        from services.control.live_proposals import BoundedPolicyAdapter
        policy=BoundedPolicyAdapter(policy_checkpoint,policy_sha256,output/'policy',execute=False)
    original=bridge.SimulationSynchronization.tick
    started=None
    samples=[]
    next_sample=0.0
    def tick(sync):
        nonlocal started,next_sample
        if started is None:
            started=time.monotonic()
        elapsed=time.monotonic()-started
        if elapsed>=seconds:
            raise KeyboardInterrupt()
        if policy is not None:
            policy.before_tick(sync,traci)
        original(sync)  # Exactly one owner; the stock implementation steps both.
        if elapsed>=next_sample:
            result=check_lights(sync,bridge.BridgeHelper,selected)
            result.update(wall_elapsed_s=elapsed,sumo_sim_time_s=traci.simulation.getTime(),
                          mirrored_vehicle_count=len(sync.sumo2carla_ids))
            samples.append(result)
            with (output/'runtime_evaluator.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(result)+'\n')
            next_sample=elapsed+1
    bridge.SimulationSynchronization.tick=tick
    error=None
    policy_summary=None
    try:
        bridge.synchronization_loop(args)
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc)
    finally:
        if policy is not None:
            policy_summary=policy.close()
    client=carla.Client('127.0.0.1',2000)
    client.set_timeout(8)
    world=client.get_world()
    summary={'mode':'FIXED_TIME_COSIM_VALIDATION','policy_enabled':False,'policy_diagnostics':policy_summary,'error':error,
             'samples':len(samples),'max_mirrored_vehicle_count':max((s['mirrored_vehicle_count'] for s in samples),default=0),
             'missing_signal_ids':sorted({x for s in samples for x in s['missing_signal_ids']}),
             'light_mismatch_samples':sum(bool(s['light_mismatches']) for s in samples),
             'post_map':world.get_map().name,'post_synchronous_mode':world.get_settings().synchronous_mode,
             'finished_at_utc':datetime.now(timezone.utc).isoformat(),
             'evaluator_only':True,'note':'Reference signal/actor checks must never enter the policy observation input.'}
    summary['passed']=bool(samples) and error is None and not summary['missing_signal_ids'] and not summary['light_mismatch_samples'] and not summary['post_synchronous_mode'] and summary['post_map']==config['map']
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('BRIDGE_VALIDATION',json.dumps(summary),flush=True)
    return 0 if summary['passed'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--policy-checkpoint',type=Path,
                        help='Verified external checkpoint for read-only proposals; no signal actuation.')
    parser.add_argument('--policy-sha256',
                        help='Required SHA256 for --policy-checkpoint.')
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not 1<=args.seconds<=30:
        parser.error('This validation is limited to at most 30 seconds of clock ownership.')
    if not args.execute:
        print('Prepared only: would run one bounded clock owner and inspect selected signal agreement.')
        return 0
    return run(args.scenario,json.loads(args.config.read_text(encoding='utf-8')),args.seconds,args.output,
               args.policy_checkpoint,args.policy_sha256)


if __name__=='__main__':
    raise SystemExit(main())
