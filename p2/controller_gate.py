"""Pure offline integration checks. This module never imports simulator clients."""
import hashlib
import json
import math
from pathlib import Path


EXPECTED_SIGNALS={'cam_g1':'719','cam_g3':'23','cam_g4':'189','cam_g5':'468'}


def audit_controller(action_mapping, observation_schema, model_manifest, checkpoint=None, runtime_map=None):
    from services.control.contracts import dimensions, lane_groups, phase_mapping
    blockers=[]
    rows=action_mapping.get('junctions',[])
    if not isinstance(rows,list) or len(rows)!=4:
        blockers.append('junction_configuration_must_be_four_objects')
        rows=rows if isinstance(rows,list) else []
    pairs={row.get('camera_id'):str(row.get('sumo_tls_id')) for row in rows}
    if pairs!=EXPECTED_SIGNALS:blockers.append('camera_signal_mapping_mismatch')
    slots,actions=dimensions(observation_schema)
    programs={p['tls_id']:p for p in runtime_map.get('programs',[])} if runtime_map else {}
    if runtime_map is None:blockers.append('runtime_network_manifest_required')
    elif runtime_map.get('network_sha256')!=model_manifest.get('network_sha256',model_manifest.get('network_hash')):
        blockers.append('runtime_network_hash_mismatch')
    for row in rows:
        alias=str(row.get('alias'))
        try:groups=lane_groups(row,slots)
        except (ValueError,KeyError):
            blockers.append(alias+':reviewed_lane_order_required');groups=[]
        if row.get('lane_mapping_reviewed') is not True:blockers.append(alias+':lane_calibration_required')
        if row.get('phase_mapping_reviewed') is not True:blockers.append(alias+':phase_mapping_review_required')
        if row.get('transition_paths_reviewed') is not True:blockers.append(alias+':reviewed_clearance_paths_required')
        if runtime_map:
            program=programs.get(str(row.get('sumo_tls_id')))
            if program is None:
                blockers.append(alias+':signal_program_missing');continue
            incoming={link['from_lane_id'] for link in program.get('controlled_links',[])}
            if set(lane for group in groups for lane in group)!=incoming:
                blockers.append(alias+':physical_lane_aggregation_mismatch')
            try:mapping=phase_mapping(row)
            except (ValueError,KeyError):
                blockers.append(alias+':explicit_action_phase_indices_required');continue
            actual={i for i,p in enumerate(program['phases']) if any(c in p['state'] for c in 'gG') and not any(c in p['state'] for c in 'yY')}
            indices={i for i in mapping.values() if i is not None}
            if actual!=indices:blockers.append(alias+':green_phase_inventory_mismatch')
    if model_manifest.get('status') not in ('TRAINED_FROZEN','TRAINED_SUMO_OFFLINE_CAMERA_UNVALIDATED'):
        blockers.append('compatible_retraining_required')
    elif model_manifest.get('status')=='TRAINED_SUMO_OFFLINE_CAMERA_UNVALIDATED':
        blockers.append('camera_domain_policy_validation_required')
    if checkpoint is None or not Path(checkpoint).is_file():blockers.append('verified_external_checkpoint_required')
    elif hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()!=model_manifest.get('checkpoint_sha256'):
        blockers.append('checkpoint_hash_mismatch')
    blockers.append('live_transition_executor_not_enabled')
    return {'source':'offline_configuration_audit','ready_for_live_policy':False,'blockers':blockers,
            'signal_mapping':pairs,'simulation_started':False,'actuation_permitted':False}


def actor_vectors(lane_packets, beliefs, phase_context, action_mapping, schema, capacity=15.0):
    """Aggregate explicit physical lane beliefs; any unavailable member masks its slot."""
    from services.control.contracts import dimensions, lane_groups
    if isinstance(capacity,bool) or not isinstance(capacity,(int,float)) or not math.isfinite(capacity) or capacity<=0:
        raise ValueError('Positive queue normalization capacity required.')
    slots,maximum=dimensions(schema);junctions=action_mapping['junctions'];vectors={}
    allowed={'lane_id','observed_count','missing','age_s'}
    for position,junction in enumerate(junctions):
        jid=junction['alias'];groups=lane_groups(junction,slots)
        packets=lane_packets[jid]
        if any(set(packet)!=allowed for packet in packets):raise ValueError('Unexpected lane field; simulator truth is not accepted.')
        by_id={packet['lane_id']:packet for packet in packets}
        if len(by_id)!=len(packets) or set(by_id)!={lane for group in groups for lane in group}:
            raise ValueError('Physical lane data/order mismatch.')
        normalized=[];missing=[];ages=[]
        for group in groups:
            if not group:
                normalized.append(0.0);missing.append(1.0);ages.append(0.0);continue
            values=[];flags=[];times=[]
            for lane in group:
                packet=by_id[lane];count=packet['observed_count'];flag=packet['missing']
                if not isinstance(flag,bool):raise ValueError('Missing flag must be boolean.')
                if flag and count is not None:raise ValueError('Missing lane must have null raw count.')
                if not flag and (isinstance(count,bool) or not isinstance(count,int) or count<0):
                    raise ValueError('Available lane requires a measured nonnegative integer count.')
                belief=beliefs[jid][lane];age=packet['age_s']
                if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in (belief,age)):
                    raise ValueError('Finite nonnegative belief and age required.')
                values.append(belief);flags.append(flag);times.append(age)
            normalized.append(min(1.0,sum(values)/(capacity*len(group))))
            missing.append(float(any(flags)));ages.append(max(times)/30.0)
        context=phase_context[jid];index=context['green_action_index'];elapsed=context['elapsed_green_s']
        active=junction.get('num_model_action_slots',junction.get('num_phases',maximum))
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<active:
            raise ValueError('Reviewed active green action index required.')
        mapping=junction.get('policy_action_phase_mapping')
        if mapping is not None and mapping.get(str(index)) is None:raise ValueError('Active phase is structurally masked.')
        if isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or elapsed<0:
            raise ValueError('Invalid phase age.')
        inflows=context['neighbor_inflow']
        if len(inflows)!=len(junctions) or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in inflows):
            raise ValueError('Explicit nonnegative observation-derived neighbor inflow required.')
        vectors[jid]=normalized+missing+ages+[float(i==index) for i in range(maximum)]+[elapsed/junction['max_green_s']]+list(inflows)+[float(i==position) for i in range(len(junctions))]
    return vectors


if __name__=='__main__':
    import argparse
    root=Path(__file__).resolve().parent.parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--runtime-map',type=Path,default=root/'configs/runtime_mapping.json')
    args=parser.parse_args()
    load=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
    print(json.dumps(audit_controller(load('configs/action_mapping.json'),load('configs/observation_schema.json'),
                                     load('manifests/model_manifest.json'),checkpoint=args.checkpoint,
                                     runtime_map=json.loads(args.runtime_map.read_text(encoding='utf-8'))
                                     if args.runtime_map.is_file() else None),indent=2))
