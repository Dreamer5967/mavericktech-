"""Bounded four-camera smoke capture; requires explicit --execute approval.

No world ticks, settings changes, map loads, traffic control, or SUMO calls.
Candidate views are not calibrated roadside cameras or lane counters.
Without --execute, this program only describes the local configuration.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import threading
import time
import uuid


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_config(config):
    if config['map'] != 'Carla/Maps/Town10HD_Opt':
        raise ValueError('This candidate configuration is only for Town10HD_Opt.')
    cameras = config['cameras']
    if len(cameras) != 4:
        raise ValueError('Exactly four camera sites are required.')
    ids = [c['camera_id'] for c in cameras]
    if len(set(ids)) != 4 or any(not re.fullmatch(r'cam_[a-z0-9_]+', x) for x in ids):
        raise ValueError('Camera IDs must be distinct safe filenames beginning cam_.')
    if len({c['candidate_group'] for c in cameras}) != 4:
        raise ValueError('Use four distinct candidate signal groups.')
    for camera in cameras:
        for key in ('x', 'y', 'z', 'pitch', 'yaw', 'roll'):
            value = camera['transform'][key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Camera transforms must contain finite numbers.')
    if config['image_width'] != 960 or config['image_height'] != 540:
        raise ValueError('This bounded smoke test uses 960x540 images.')
    for key, low, high in (('fov', 60, 110), ('sensor_tick_s', 0.1, 1.0),
                           ('capture_timeout_s', 1, 45), ('stale_after_sim_s', 0, 60),
                           ('confidence', 0.01, 1.0)):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('Invalid bounded setting: ' + key)
    if not PurePosixPath(config['weights_path']).is_absolute():
        raise ValueError('Provide an absolute path to existing local weights.')
    size = config.get('inference_imgsz', 640)
    if isinstance(size, bool) or not isinstance(size, int) or size not in (640, 960, 1280):
        raise ValueError('inference_imgsz must be 640, 960 or 1280.')
    return config


def require_async(world):
    if world.get_settings().synchronous_mode:
        raise RuntimeError('Synchronous mode detected: stop; do not start another clock owner.')


def capture_frames(world, carla_module, config):
    """Retain at most one image per owned sensor; clean up even on failure."""
    require_async(world)
    condition = threading.Condition()
    latest, errors = {}, {}
    owned, cleanup_errors = [], []
    accepting = True
    deadline = time.monotonic() + config['capture_timeout_s']

    def callback(camera_id):
        def receive(image):
            nonlocal accepting
            with condition:
                if accepting:
                    latest[camera_id] = (image, utc_now(), time.monotonic())
                    condition.notify_all()
        return receive

    try:
        for camera in config['cameras']:
            require_async(world)
            if time.monotonic() >= deadline:
                errors[camera['camera_id']] = 'capture_deadline_before_spawn'
                continue
            bp = world.get_blueprint_library().find('sensor.camera.rgb')
            for key, value in (('image_size_x', config['image_width']),
                               ('image_size_y', config['image_height']),
                               ('sensor_tick', config['sensor_tick_s']),
                               ('fov', config['fov']),
                               ('role_name', 'aegis_p2_smoke_' + camera['camera_id'])):
                bp.set_attribute(key, str(value))
            t = camera['transform']
            transform = carla_module.Transform(
                carla_module.Location(x=t['x'], y=t['y'], z=t['z']),
                carla_module.Rotation(pitch=t['pitch'], yaw=t['yaw'], roll=t['roll']))
            try:
                sensor = world.spawn_actor(bp, transform)
                # Record ownership before listen(), which can fail independently.
                owned.append(sensor)
                print('Owned camera:', camera['camera_id'], 'actor', sensor.id, flush=True)
                sensor.listen(callback(camera['camera_id']))
            except Exception as exc:
                errors[camera['camera_id']] = type(exc).__name__ + ': ' + str(exc)
        while time.monotonic() < deadline:
            require_async(world)
            with condition:
                pending = [c['camera_id'] for c in config['cameras']
                           if c['camera_id'] not in latest and c['camera_id'] not in errors]
                if not pending:
                    break
                condition.wait(timeout=min(0.2, max(0, deadline - time.monotonic())))
    except Exception as exc:
        errors['_capture'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        with condition:
            accepting = False
        for sensor in reversed(owned):
            try:
                sensor.stop()
            except Exception as exc:
                cleanup_errors.append({'actor_id': sensor.id, 'operation': 'stop', 'error': str(exc)})
            try:
                if not sensor.destroy():
                    cleanup_errors.append({'actor_id': sensor.id, 'operation': 'destroy', 'error': 'returned false'})
            except Exception as exc:
                cleanup_errors.append({'actor_id': sensor.id, 'operation': 'destroy', 'error': str(exc)})
        for issue in cleanup_errors:
            print('CLEANUP ISSUE:', json.dumps(issue), flush=True)
    for camera in config['cameras']:
        if camera['camera_id'] not in latest:
            errors.setdefault(camera['camera_id'], 'frame_timeout')
    return latest, errors, cleanup_errors, [sensor.id for sensor in owned]


def empty_observation(camera_id, error=None):
    return {
        'camera_id': camera_id, 'source': 'carla_rgb', 'status': 'missing',
        'missing': True, 'error': error, 'frame_id': None,
        'source_sim_time_s': None, 'received_at_utc': None,
        'frame_age_sim_s': None, 'stale': None,
        'raw_image': None, 'raw_sha256': None, 'annotated_image': None,
        'detections': None, 'counts_by_class': None, 'whole_image_vehicle_count': None,
        'lane_counts': None, 'queue_estimate': None,
        'lane_attribution_status': 'uncalibrated', 'inference_call_wall_ms': None,
    }


def stamp_freshness(row, sim_time, threshold):
    captured = row['source_sim_time_s']
    if captured is None or sim_time is None or sim_time < captured:
        row['frame_age_sim_s'] = None
        row['stale'] = None
    else:
        row['frame_age_sim_s'] = sim_time - captured
        row['stale'] = row['frame_age_sim_s'] > threshold


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def infer_frame(model, bgr, cv2, config, device=0):
    start = time.monotonic()
    result = model.predict(source=bgr, device=device, conf=config['confidence'],
                           imgsz=config.get('inference_imgsz', 640), save=False, verbose=False)[0]
    boxes = result.boxes
    if boxes is None:
        raise RuntimeError('Detector did not return detection boxes.')
    detections = []
    for xyxy, class_id, confidence in zip(boxes.xyxy.detach().cpu().tolist(),
                                         boxes.cls.detach().cpu().tolist(),
                                         boxes.conf.detach().cpu().tolist()):
        numbers = list(xyxy) + [class_id, confidence]
        if not all(math.isfinite(x) for x in numbers):
            raise ValueError('Nonfinite detector output.')
        detections.append({'class_id': int(class_id), 'class_name': result.names[int(class_id)],
                           'confidence': float(confidence), 'xyxy_pixels': xyxy})
    elapsed_ms = (time.monotonic() - start) * 1000
    annotated = bgr.copy()
    for detection in detections:
        x1, y1, x2, y2 = [int(x) for x in detection['xyxy_pixels']]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 220, 0), 2)
        label = f"{detection['class_name']} {detection['confidence']:.2f}"
        cv2.putText(annotated, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 220, 0), 1, cv2.LINE_AA)
    return detections, annotated, elapsed_ms


def load_warmed_model(weights, config, run_dir):
    """Complete detector initialization before any sensor is created."""
    os.environ['YOLO_AUTOINSTALL'] = 'false'
    os.environ['YOLO_OFFLINE'] = 'true'
    config_dir = run_dir / 'ultralytics-config'
    (config_dir / 'Ultralytics').mkdir(parents=True, exist_ok=True)
    os.environ['YOLO_CONFIG_DIR'] = str(config_dir)
    import numpy as np
    import torch
    from ultralytics import YOLO, utils
    if utils.AUTOINSTALL or utils.ONLINE:
        raise RuntimeError('Installed Ultralytics did not honor offline/no-install settings.')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; GPU test will not silently fall back to CPU.')
    started = time.monotonic()
    model = YOLO(str(weights))
    loaded = time.monotonic()
    # Same shape and prediction arguments as the coming camera images.
    sample = np.zeros((config['image_height'], config['image_width'], 3), dtype=np.uint8)
    model.predict(source=sample, device=0, conf=config['confidence'],
                  imgsz=config.get('inference_imgsz', 640), save=False, verbose=False)
    torch.cuda.synchronize()
    return model, {'model_load_wall_ms': (loaded-started)*1000,
                   'detector_warmup_wall_ms': (time.monotonic()-loaded)*1000}


def execute(config, output_root):
    # All external dependencies are imported only after the explicit execute gate.
    import carla
    import cv2
    import numpy as np

    weights = Path(config['weights_path'])
    if not weights.is_file():
        raise RuntimeError('Existing checkpoint not found; no download will be attempted.')
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(8)
    if (client.get_client_version(), client.get_server_version()) != ('0.9.15', '0.9.15'):
        raise RuntimeError('Expected CARLA client and server 0.9.15.')
    world = client.get_world()
    require_async(world)
    if world.get_map().name != config['map']:
        raise RuntimeError('Live map does not match the inspected candidate configuration.')
    if list(world.get_actors().filter('sensor.camera.rgb')):
        raise RuntimeError('RGB cameras already exist. Review their ownership before another test.')

    run_id = datetime.now(timezone.utc).strftime('p2-smoke-%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    print('Evidence directory:', run_dir, flush=True)
    document = {
        'schema_version': 'p2.camera-smoke.v2-draft', 'mode': 'LIVE',
        'run_id': run_id, 'purpose': 'bounded_smoke_capture',
        'ready_for_live_policy': False, 'coverage_reviewed': False,
        'connected_topology_verified': False, 'camera_config': config,
        'started_at_utc': utc_now(), 'published_at_utc': None,
        'published_sim_time_s': None, 'frame_skew_sim_s': None,
        'weights_sha256': sha256_file(weights), 'versions': {},
        'owned_actor_ids': [], 'cleanup_errors': [], 'errors': [],
        'observations': [], 'timings': {},
    }
    for package in ('carla', 'ultralytics', 'torch', 'torchvision', 'numpy', 'opencv-python'):
        try:
            document['versions'][package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            document['versions'][package] = None

    model = None
    try:
        model, document['timings'] = load_warmed_model(weights, config, run_dir)
        print('YOLO loaded and warmed before camera creation.', flush=True)
    except Exception as exc:
        document['errors'].append('Detector initialization failed; no cameras created: ' + str(exc))
    shots, capture_errors = {}, {}
    capture_started = time.monotonic()
    try:
        if model is not None:
            shots, capture_errors, cleanup_errors, owned = capture_frames(world, carla, config)
            document['owned_actor_ids'] = owned
            document['cleanup_errors'] = cleanup_errors
            if '_capture' in capture_errors:
                document['errors'].append('Capture aborted: ' + capture_errors['_capture'])
        else:
            capture_errors = {c['camera_id']: 'detector_initialization_failed' for c in config['cameras']}
    except Exception as exc:
        document['errors'].append('Capture aborted: ' + type(exc).__name__ + ': ' + str(exc))
    document['timings']['capture_and_cleanup_wall_ms'] = (time.monotonic()-capture_started)*1000

    images = {}
    encoding_started = time.monotonic()
    for camera in config['cameras']:
        camera_id = camera['camera_id']
        row = empty_observation(camera_id, capture_errors.get(camera_id))
        document['observations'].append(row)
        if camera_id not in shots:
            continue
        image, received_utc, _ = shots[camera_id]
        row.update(missing=False, status='captured', frame_id=image.frame,
                   source_sim_time_s=image.timestamp, received_at_utc=received_utc, error=None)
        try:
            bgr = np.frombuffer(image.raw_data, dtype=np.uint8).reshape(image.height, image.width, 4)[:, :, :3].copy()
            raw_path = run_dir / (camera_id + '.png')
            if not cv2.imwrite(str(raw_path), bgr):
                raise RuntimeError('Raw image encoding failed.')
            row.update(raw_image=raw_path.name, raw_sha256=sha256_file(raw_path))
            images[camera_id] = bgr
        except Exception as exc:
            row.update(status='image_error', error=str(exc))

    document['timings']['raw_image_encoding_wall_ms'] = (time.monotonic()-encoding_started)*1000
    # Sensors are now cleaned up and the already-warm model handles the saved batch.
    for row in document['observations']:
        if row['camera_id'] not in images:
            continue
        if model is None:
            row.update(status='inference_error', error='Detector unavailable; see run errors.')
            continue
        try:
            row['inference_started_at_utc'] = utc_now()
            row['receive_to_inference_start_wall_ms'] = (time.monotonic()-shots[row['camera_id']][2])*1000
            detections, annotated, elapsed = infer_frame(model, images[row['camera_id']], cv2, config)
            row['inference_completed_at_utc'] = utc_now()
            annotated_path = run_dir / (row['camera_id'] + '_yolo.jpg')
            if not cv2.imwrite(str(annotated_path), annotated):
                raise RuntimeError('Annotated image encoding failed.')
            counts = dict(Counter(d['class_name'] for d in detections))
            row.update(status='detected', detections=detections, counts_by_class=counts,
                       whole_image_vehicle_count=sum(counts.get(name, 0) for name in config['vehicle_classes']),
                       annotated_image=annotated_path.name, inference_call_wall_ms=elapsed)
        except Exception as exc:
            row.update(status='inference_error', error=type(exc).__name__ + ': ' + str(exc))
    try:
        document['published_sim_time_s'] = world.get_snapshot().timestamp.elapsed_seconds
    except Exception as exc:
        document['errors'].append('Publication clock unavailable: ' + str(exc))
    for row in document['observations']:
        stamp_freshness(row, document['published_sim_time_s'], config['stale_after_sim_s'])
    times = [row['source_sim_time_s'] for row in document['observations'] if row['source_sim_time_s'] is not None]
    if times and document['published_sim_time_s'] is not None and document['published_sim_time_s'] < max(times):
        document['errors'].append('Publication time predates a captured frame; possible scenario reset.')
    if len(times) >= 2:
        document['frame_skew_sim_s'] = max(times) - min(times)
    document['published_at_utc'] = utc_now()
    document['smoke_success'] = (all(row['status'] == 'detected' for row in document['observations'])
                                 and not document['cleanup_errors'] and not document['errors'])
    # A single writer creates a new run's file; existing evidence is never replaced.
    with (run_dir / 'observations.json').open('x', encoding='utf-8') as stream:
        json.dump(document, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('Observations:', run_dir / 'observations.json', flush=True)
    for row in document['observations']:
        print(row['camera_id'], row['status'], 'frame=', row['frame_id'],
              'counts=', row['counts_by_class'], 'stale=', row['stale'], flush=True)
    print('Smoke success:', document['smoke_success'], '; coverage and lane counts remain unverified.', flush=True)
    return 0 if document['smoke_success'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config', type=Path)
    source.add_argument('--config-base64')
    parser.add_argument('--execute', action='store_true', help='Explicit approval to spawn temporary cameras and run YOLO.')
    parser.add_argument('--output-root', type=Path, default=Path('/workspace/aegis/evidence/multicam'))
    args = parser.parse_args()
    text = args.config.read_text(encoding='utf-8') if args.config else base64.b64decode(args.config_base64, validate=True).decode('utf-8')
    config = validate_config(json.loads(text))
    if not args.execute:
        print(json.dumps({'action': 'describe_only', 'cloud_contacted': False, 'config': config}, indent=2))
        return 0
    return execute(config, args.output_root)


if __name__ == '__main__':
    raise SystemExit(main())
