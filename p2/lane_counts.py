"""Camera-only ROI vehicle occupancy; never estimates stopped queues or uses truth."""
import hashlib
import json
import math


def validate_regions(calibration,config):
    expected=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    if calibration.get('camera_config_sha256')!=expected or calibration.get('map')!=config['map']:
        raise ValueError('Lane regions do not match the exact camera configuration.')
    if {c['camera_id'] for c in calibration['cameras']}!={c['camera_id'] for c in config['cameras']}:
        raise ValueError('Lane-region camera set mismatch.')
    for camera in calibration['cameras']:
        ids=[r['lane_id'] for r in camera['regions']]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate lane IDs.')
        for region in camera['regions']:
            polygon=region['polygon_pixels']
            if any(len(p)!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in p) for p in polygon):
                raise ValueError('Invalid lane polygon.')
            if region.get('usable_for_counts') and (len(polygon)<3 or
                 not region.get('coverage_reviewed') or not region.get('occlusion_reviewed') or
                 not region.get('detection_validated')):
                raise ValueError('Usable lanes require reviewed visible polygons.')
    return calibration


def contains(point,polygon):
    x,y=point;inside=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        cross=(x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross)<1e-7 and min(a[0],b[0])<=x<=max(a[0],b[0]) and min(a[1],b[1])<=y<=max(a[1],b[1]):return True
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def measure(detections,camera,vehicle_classes,enabled=False,anchor='center'):
    if anchor not in ('center','bottom_center'):raise ValueError('Unsupported vehicle anchor.')
    regions=camera['regions'];counts={r['lane_id']:0 for r in regions}
    ambiguous=set();unassigned=0
    for detection in detections:
        if detection['class_name'] not in vehicle_classes:continue
        box=detection['xyxy_pixels']
        if len(box)!=4 or not all(math.isfinite(v) for v in box) or box[2]<=box[0] or box[3]<=box[1]:
            raise ValueError('Invalid vehicle bounding box.')
        point=((box[0]+box[2])/2,(box[1]+box[3])/2 if anchor=='center' else box[3])
        matches=[r['lane_id'] for r in regions if contains(point,r['polygon_pixels'])]
        if len(matches)==1:counts[matches[0]]+=1
        elif matches:ambiguous.update(matches)
        else:unassigned+=1
    usable={r['lane_id']:bool(enabled and r.get('usable_for_counts') and r.get('coverage_reviewed')
                              and r.get('occlusion_reviewed') and r.get('detection_validated')
                              and r['lane_id'] not in ambiguous) for r in regions}
    return {'lane_counts':{lid:count if usable[lid] else None for lid,count in counts.items()},
            'candidate_counts':counts,'ambiguous_lane_ids':sorted(ambiguous),'unassigned_vehicle_detections':unassigned,
            'measurement':'detected_vehicle_roi_occupancy','queue_estimate':None}
