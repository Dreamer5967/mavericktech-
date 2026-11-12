"""Pure v2 lane-slot and green-action contract helpers; no simulator access."""
import numpy as np


def dimensions(schema):
    meta=schema.get('_metadata',{})
    return (schema.get('max_model_lane_slots',schema.get('num_lanes_per_junction',meta.get('num_lanes_per_junction',4))),
            schema.get('max_model_action_slots',4))


def lane_groups(junction,slots=4):
    aggregation=junction.get('lane_slot_aggregation')
    if aggregation is None:
        ids=junction.get('lane_ids')
        if not isinstance(ids,list) or len(ids)!=slots:raise ValueError('Reviewed lane order is required.')
        return [[lane] for lane in ids]
    groups=[]
    for index in range(slots):
        value=aggregation.get('slot_'+str(index))
        if value is not None and (not isinstance(value,list) or not value or any(not isinstance(v,str) for v in value)):
            raise ValueError('Lane slots must contain nonempty lane ID lists or null.')
        groups.append(list(value or []))
    lanes=[lane for group in groups for lane in group]
    if len(set(lanes))!=len(lanes) or set(lanes)!=set(junction['incoming_lane_ids']):
        raise ValueError('Lane aggregation must cover every physical lane exactly once.')
    return groups


def phase_mapping(junction):
    raw=junction.get('policy_action_phase_mapping')
    if raw is None:
        indices=junction.get('sumo_green_phase_indices')
        if indices is None:raise ValueError('Explicit policy-to-SUMO phase mapping is required.')
        return dict(enumerate(indices))
    result={}
    for key,value in raw.items():
        index=int(key)
        phase=value['sumo_phase_index'] if value is not None else None
        if phase is not None and (isinstance(phase,bool) or not isinstance(phase,int) or phase<0):
            raise ValueError('SUMO phase indices must be nonnegative integers.')
        result[index]=phase
    active=[phase for phase in result.values() if phase is not None]
    if len(active)!=len(set(active)):raise ValueError('Active action slots must map to distinct green phases.')
    return result


def permanent_mask(junction,slots=4):
    mapping=phase_mapping(junction)
    if set(mapping)!=set(range(slots)):raise ValueError('Every model action slot must be declared.')
    mask=np.array([mapping[i] is not None for i in range(slots)],dtype=bool)
    for index in junction.get('action_mask_always_false',[]):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<slots:raise ValueError('Invalid masked action slot.')
        mask[index]=False
    return mask


def require_action_mask(mask,structural):
    values=np.asarray(mask)
    if values.shape!=structural.shape or values.dtype!=np.bool_:
        raise ValueError('Action mask must be a boolean vector matching model slots.')
    result=np.logical_and(values,structural)
    if not result.any():raise ValueError('No valid action remains; no phase proposal is permitted.')
    return result
