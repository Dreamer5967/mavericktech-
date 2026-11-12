"""Compare saved RGB images locally. Never imports or connects to CARLA/SUMO."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import time
import uuid

from p2.capture_four import infer_frame, sha256_file


PROFILES = [
    {'name': 'full_640', 'imgsz': 640, 'transform': 'full'},
    {'name': 'full_960', 'imgsz': 960, 'transform': 'full'},
    {'name': 'full_1280', 'imgsz': 1280, 'transform': 'full'},
    {'name': 'rot180_960', 'imgsz': 960, 'transform': 'rot180'},
    {'name': 'tiles_640', 'imgsz': 640, 'transform': 'tiles'},
]


def tile_windows(width, height):
    if width <= 0 or height <= 0:
        raise ValueError('Image dimensions must be positive.')
    tw, th = max(1, (2*width)//3), max(1, (2*height)//3)
    return sorted(set((x, y, x+tw, y+th)
                      for x in (0, width-tw) for y in (0, height-th)))


def restore_box(box, width, height, transform, offset=(0, 0)):
    x1, y1, x2, y2 = box
    if transform == 'rot180':
        return [width-x2, height-y2, width-x1, height-y1]
    dx, dy = offset
    return [x1+dx, y1+dy, x2+dx, y2+dy]


def iou(a, b):
    intersection = max(0, min(a[2],b[2])-max(a[0],b[0])) * max(0,min(a[3],b[3])-max(a[1],b[1]))
    area = max(0,a[2]-a[0])*max(0,a[3]-a[1]) + max(0,b[2]-b[0])*max(0,b[3]-b[1]) - intersection
    return intersection/area if area else 0


def deduplicate(detections):
    # Cross-tile suppression only; do not change the model's own prediction head.
    kept = []
    for candidate in sorted(detections, key=lambda d:d['confidence'], reverse=True):
        if not any(candidate['class_id'] == other['class_id'] and
                   iou(candidate['xyxy_pixels'],other['xyxy_pixels']) > 0.5 for other in kept):
            kept.append(candidate)
    return kept


def compare(args):
    source_path = args.run_dir/'observations.json'
    document = json.loads(source_path.read_text(encoding='utf-8'))
    if not args.weights.is_file() or sha256_file(args.weights) != document['weights_sha256']:
        raise ValueError('Checkpoint must exactly match the source run SHA256; no download is attempted.')
    frames = []
    root = args.run_dir.resolve()
    for observation in document['observations']:
        if observation['missing']:
            continue
        path = (root/observation['raw_image']).resolve()
        if not path.is_relative_to(root) or sha256_file(path) != observation['raw_sha256']:
            raise ValueError('Frame path/hash validation failed.')
        frames.append((observation,path))
    if not frames:
        raise ValueError('No verified source frames.')
    identifier = datetime.now(timezone.utc).strftime('replay-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    output = args.output_root/identifier
    output.mkdir(parents=True,exist_ok=False)
    os.environ['YOLO_OFFLINE']='true'
    os.environ['YOLO_AUTOINSTALL']='false'
    config_dir=output/'ultralytics-config'
    (config_dir/'Ultralytics').mkdir(parents=True,exist_ok=True)
    os.environ['YOLO_CONFIG_DIR']=str(config_dir)
    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO, utils
    if utils.ONLINE or utils.AUTOINSTALL:
        raise RuntimeError('Offline/no-install settings were not honored.')
    torch.set_num_threads(min(4,os.cpu_count() or 1))
    model = YOLO(str(args.weights))
    report = {
        'mode':'REPLAY','source_run_id':document['run_id'],
        'source_manifest_sha256':sha256_file(source_path),
        'weights_sha256':document['weights_sha256'], 'checkpoint_matches_source':True,
        'device':'cpu','versions':{name:metadata.version(name) for name in ('ultralytics','torch','numpy')},
        'original_runtime_versions':document['versions'],
        'scope':'Diagnostic replay of four saved images; not a traffic benchmark or cloud throughput measurement.',
        'confidence_threshold':0.25, 'ready_for_live_policy':False, 'rows':[]}
    images = [(observation,cv2.imread(str(path))) for observation,path in frames]
    if any(image is None for _,image in images):
        raise ValueError('Image decode failed.')
    for profile in PROFILES:
        example = images[0][1]
        if profile['transform']=='tiles':
            x1,y1,x2,y2=tile_windows(example.shape[1],example.shape[0])[0]
            example=example[y1:y2,x1:x2]
        warmed=time.monotonic()
        model.predict(source=np.zeros_like(example),device='cpu',imgsz=profile['imgsz'],
                      conf=0.25,save=False,verbose=False)
        print('PROFILE',profile['name'],'warmup_ms',round((time.monotonic()-warmed)*1000,1),flush=True)
        for observation,image in images:
            height,width=image.shape[:2]
            windows = tile_windows(width,height) if profile['transform']=='tiles' else [(0,0,width,height)]
            detections=[]
            total_prediction_ms=0
            started=time.monotonic()
            for x1,y1,x2,y2 in windows:
                view=image[y1:y2,x1:x2]
                if profile['transform']=='rot180':
                    view=np.ascontiguousarray(np.rot90(view,2))
                found,_,elapsed=infer_frame(model,view,cv2,
                                           {'confidence':0.25,'inference_imgsz':profile['imgsz']},device='cpu')
                total_prediction_ms+=elapsed
                for detection in found:
                    detection['xyxy_pixels']=restore_box(detection['xyxy_pixels'],width,height,
                                                         profile['transform'],(x1,y1))
                    detections.append(detection)
            detections=deduplicate(detections)
            counts=dict(Counter(item['class_name'] for item in detections))
            annotated=image.copy()
            for detection in detections:
                x1,y1,x2,y2=[round(v) for v in detection['xyxy_pixels']]
                color=(0,210,0) if detection['class_name'] in document['camera_config']['vehicle_classes'] else (0,190,255)
                cv2.rectangle(annotated,(x1,y1),(x2,y2),color,2)
                cv2.putText(annotated,f"{detection['class_name']} {detection['confidence']:.2f}",
                            (x1,max(y1-5,15)),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,1,cv2.LINE_AA)
            image_name=observation['camera_id']+'__'+profile['name']+'.jpg'
            if not cv2.imwrite(str(output/image_name),annotated):
                raise RuntimeError('Image encoding failed.')
            row={'camera_id':observation['camera_id'],'profile':profile['name'],
                 'source_frame_id':observation['frame_id'],
                 'source_sim_time_s':observation['source_sim_time_s'],
                 'source_received_at_utc':observation['received_at_utc'],
                 'counts_by_class':counts,'detections':detections,
                 'prediction_calls':len(windows),'prediction_call_wall_ms':total_prediction_ms,
                 'total_processing_wall_ms':(time.monotonic()-started)*1000,'annotated_image':image_name}
            report['rows'].append(row)
            print(observation['camera_id'],profile['name'],counts,flush=True)
    report['replayed_at_utc']=datetime.now(timezone.utc).isoformat()
    with (output/'comparison.json').open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print('REPLAY_REPORT',output/'comparison.json',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--weights',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    compare(parser.parse_args())


if __name__=='__main__':
    main()
