"""Pure offline integration checks. This module never imports simulator clients."""
import hashlib
import json
import math
from pathlib import Path


EXPECTED_SIGNALS={'cam_g1':'719','cam_g3':'23','cam_g4':'189','cam_g5':'468'}


def audit_controller(action_mapping, observation_schema, model_manifest,
                     checkpoint=None, runtime_map=None):
    blockers=[]
    rows=action_mapping.get('junctions',[])
    if not isinstance(rows,list):
        blockers.append('junction_configuration_must_be_four_objects')
        rows=[]
    elif len(rows)!=4:
        blockers.append('junction_configuration_must_be_four_objects')
    pairs={row.get('camera_id'):str(row.get('sumo_tls_id')) for row in rows}
    if pairs!=EXPECTED_SIGNALS:
        blockers.append('camera_signal_mapping_mismatch')
    meta=observation_schema.get('_metadata',{})
    lanes=observation_schema.get('num_lanes_per_junction',meta.get('num_lanes_per_junction'))
    phases={}
    for row in rows:
        alias=row.get('alias')
        lane_ids=row.get('lane_ids')
        if not isinstance(lane_ids,list) or len(lane_ids)!=lanes or len(set(lane_ids))!=lanes:
            blockers.append(str(alias)+':reviewed_lane_order_required')
        if row.get('lane_mapping_reviewed') is not True:
            blockers.append(str(alias)+':lane_calibration_required')
        if row.get('phase_mapping_reviewed') is not True:
            blockers.append(str(alias)+':phase_mapping_review_required')
        phases[alias]=row.get('sumo_green_phase_indices')
    if runtime_map is None:
        blockers.append('runtime_network_manifest_required')
    else:
        if runtime_map.get('network_sha256')!=model_manifest.get('network_hash'):
            blockers.append('runtime_network_hash_mismatch')
        programs={row['tls_id']:row for row in runtime_map.get('programs',[])}
        for row in rows:
            program=programs.get(str(row['sumo_tls_id']))
            indices=phases[row.get('alias')]
            if program is None:
                blockers.append(str(row.get('alias'))+':signal_program_missing')
                continue
            incoming={link['from_lane_id'] for link in program.get('controlled_links',[])}
            if len(incoming)!=lanes:
                blockers.append(str(row.get('alias'))+':physical_lane_count_differs_from_model_slots')
            green_count=sum(any(c in phase['state'] for c in 'gG') and
                            not any(c in phase['state'] for c in 'yY') for phase in program['phases'])
            if green_count!=row['num_phases']:
                blockers.append(str(row.get('alias'))+':physical_green_count_differs_from_model_actions')
            if not isinstance(indices,list) or len(indices)!=row['num_phases'] or len(set(indices))!=len(indices):
                blockers.append(str(row.get('alias'))+':explicit_action_phase_indices_required')
                continue
            for index in indices:
                valid=isinstance(index,int) and not isinstance(index,bool) and 0<=index<len(program['phases'])
                state=program['phases'][index]['state'] if valid else ''
                if not valid or not any(c in state for c in 'gG') or any(c in state for c in 'yY'):
                    blockers.append(str(row.get('alias'))+':action_is_not_a_reviewed_green_phase')
    if checkpoint is None or not Path(checkpoint).is_file():
        blockers.append('verified_external_checkpoint_required')
    elif hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()!=model_manifest.get('checkpoint_sha256'):
        blockers.append('checkpoint_hash_mismatch')
    return {'source':'offline_configuration_audit','ready_for_live_policy':not blockers,
            'blockers':blockers,'signal_mapping':pairs,
            'simulation_started':False,'actuation_permitted':False}


def actor_vectors(lane_packets, beliefs, phase_context, action_mapping, schema, capacity=15.0):
    """Assemble the P3 vector only from explicit lane beliefs and phase context.

    Unavailable lanes require a P3 belief and retain their mask/source age.
    The caller must pass the configuration audit before using this in a coordinator.
    """
    if isinstance(capacity,bool) or not isinstance(capacity,(int,float)) or not math.isfinite(capacity) or capacity<=0:
        raise ValueError('Positive queue normalization capacity required.')
    lanes=schema['num_lanes_per_junction']
    junctions=action_mapping['junctions']
    maximum=max(row['num_phases'] for row in junctions)
    vectors={}
    allowed_fields={'lane_id','observed_count','missing','age_s'}
    for position,junction in enumerate(junctions):
        jid=junction['alias']
        order=junction.get('lane_ids')
        if not isinstance(order,list) or len(order)!=lanes:
            raise ValueError('Reviewed lane order is required; image counts cannot fill lane slots.')
        packets=lane_packets[jid]
        if any(set(packet)!=allowed_fields for packet in packets):
            raise ValueError('Unexpected lane field; simulator truth is not accepted.')
        by_id={packet['lane_id']:packet for packet in packets}
        if len(by_id)!=len(packets) or set(by_id)!=set(order):
            raise ValueError('Lane data/order mismatch.')
        normalized=[];missing=[];ages=[]
        for lane_id in order:
            packet=by_id[lane_id]
            if not isinstance(packet['missing'],bool):
                raise ValueError('Missing flag must be boolean.')
            count=packet['observed_count']
            if packet['missing'] and count is not None:
                raise ValueError('Missing lane must have null raw count.')
            if not packet['missing'] and (isinstance(count,bool) or not isinstance(count,int) or count<0):
                raise ValueError('Available lane requires a measured nonnegative integer count.')
            belief=beliefs[jid][lane_id]
            age=packet['age_s']
            if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in (belief,age)):
                raise ValueError('Finite nonnegative lane belief and age required.')
            normalized.append(min(1.0,belief/capacity));missing.append(float(packet['missing']));ages.append(age/30.0)
        context=phase_context[jid]
        index=context['green_action_index']
        elapsed=context['elapsed_green_s']
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<junction['num_phases']:
            raise ValueError('Reviewed active green action index required.')
        if not isinstance(elapsed,(int,float)) or isinstance(elapsed,bool) or not math.isfinite(elapsed) or elapsed<0:
            raise ValueError('Invalid phase age.')
        inflows=context['neighbor_inflow']
        if len(inflows)!=len(junctions) or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0 for v in inflows):
            raise ValueError('Explicit nonnegative observation-derived neighbor inflow required.')
        phase=[float(i==index) for i in range(maximum)]
        identity=[float(i==position) for i in range(len(junctions))]
        vectors[jid]=normalized+missing+ages+phase+[elapsed/junction['max_green_s']]+list(inflows)+identity
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
