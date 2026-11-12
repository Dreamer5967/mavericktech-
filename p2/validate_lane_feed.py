"""Bounded asynchronous lane-feed/dropout validation; never owns a simulation clock."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import urlopen
import uuid
from p2.validate_pipeline import stop_owned


def run(config_path,regions_path,output_root):
    import carla
    import cv2
    import numpy as np
    config=json.loads(config_path.read_text());regions=json.loads(regions_path.read_text())
    client=carla.Client('127.0.0.1',2000);client.set_timeout(10);world=client.get_world()
    if world.get_settings().synchronous_mode or world.get_map().name!=config['map']:
        raise RuntimeError('Unexpected map or existing synchronous owner; no worker started.')
    if list(world.get_actors().filter('sensor.camera.rgb')):
        raise RuntimeError('Existing RGB sensors require ownership review.')
    output=output_root/('lane-feed-'+uuid.uuid4().hex[:10]);output.mkdir(parents=True,exist_ok=False)
    process=None;samples=[];error=None
    try:
        with (output/'feed.log').open('x') as log:
            process=subprocess.Popen([sys.executable,'-B','-u','-m','p2.live_feed','--execute',
                '--config',str(config_path),'--lane-regions',str(regions_path),'--duration','90',
                '--output-root',str(output/'worker'),'--drop-camera','cam_g3','--drop-after','10','--drop-for','8'],
                stdout=log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+45
            while True:
                if process.poll() is not None:raise RuntimeError('Worker exited before readiness.')
                try:
                    with urlopen('http://127.0.0.1:8765/health',timeout=1) as response:
                        if json.load(response)['ok']:break
                except OSError:pass
                if time.monotonic()>deadline:raise RuntimeError('Readiness deadline exceeded.')
                time.sleep(.2)
            started=time.monotonic();next_preview=0
            while time.monotonic()-started<40:
                if process.poll() is not None:raise RuntimeError('Worker failed during the test.')
                with urlopen('http://127.0.0.1:8765/api/v1/snapshot',timeout=3) as response:snapshot=json.load(response)
                samples.append(snapshot)
                if time.monotonic()-started>=next_preview:
                    for camera in snapshot['cameras']:
                        if camera['status']!='fresh':continue
                        with urlopen('http://127.0.0.1:8765'+camera['frame_url'],timeout=3) as response:jpeg=response.read()
                        image=cv2.imdecode(np.frombuffer(jpeg,dtype=np.uint8),cv2.IMREAD_COLOR)
                        if image is None or image.shape[:2]!=(1280,1280):raise RuntimeError('Invalid square JPEG.')
                        (output/(camera['camera_id']+'.jpg')).write_bytes(jpeg)
                    next_preview=time.monotonic()-started+5
                time.sleep(.25)
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    finally:stop_owned(process,signal.SIGTERM)
    (output/'observations.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
    fault=[s for s in samples if 'cam_g3' in s.get('active_faults',[])]
    stale_fault=[s for s in fault if next(c for c in s['cameras'] if c['camera_id']=='cam_g3')['status']=='stale']
    seen=False;recovered=False
    for s in samples:
        if s.get('active_faults'):seen=True
        elif seen and next(c for c in s['cameras'] if c['camera_id']=='cam_g3')['status']=='fresh':recovered=True
    lane_ids={r['lane_id'] for c in regions['cameras'] for r in c['regions'] if r['usable_for_counts']}
    valid_lanes={lane for s in samples for c in s['cameras'] if c['status']=='fresh'
                 for lane,count in (c['lane_counts'] or {}).items() if count is not None}
    occluded={r['lane_id'] for c in regions['cameras'] for r in c['regions'] if not r['usable_for_counts']}
    occluded_masked=all(count is None for s in samples for c in s['cameras'] for lane,count in (c['lane_counts'] or {}).items() if lane in occluded)
    faults_masked=bool(stale_fault) and all(all(v is None for v in next(c for c in s['cameras'] if c['camera_id']=='cam_g3')['lane_counts'].values()) for s in stale_fault)
    other_progress={cid:len({c['frame_id'] for s in fault for c in s['cameras'] if c['camera_id']==cid and c['status']=='fresh'})
                    for cid in ('cam_g1','cam_g4','cam_g5')}
    remaining=[a.id for a in world.get_actors().filter('sensor.camera.rgb')]
    worker_summaries=list((output/'worker').glob('*/summary.json'))
    worker=json.loads(worker_summaries[0].read_text()) if worker_summaries else {}
    passed=error is None and valid_lanes==lane_ids and occluded_masked and faults_masked and recovered
    passed=passed and bool(worker_summaries) and all(v>=2 for v in other_progress.values()) and not remaining and not worker.get('cleanup_errors') and worker.get('error') is None
    passed=passed and world.get_map().name==config['map'] and not world.get_settings().synchronous_mode and process.returncode==0
    summary={'passed':bool(passed),'error':error,'snapshot_samples':len(samples),'published_lane_count':len(valid_lanes),
        'occluded_lanes_remained_null':occluded_masked,'dropout_stale_samples':len(stale_fault),
        'dropout_counts_masked':faults_masked,'camera_recovered':recovered,'other_camera_fresh_frames_during_fault':other_progress,
        'remaining_rgb_actor_ids':remaining,'worker_cleanup_errors':worker.get('cleanup_errors'),
        'post_map':world.get_map().name,'post_synchronous_mode':world.get_settings().synchronous_mode,
        'measurement':'detected_vehicle_roi_occupancy','queue_estimate':None,'policy_enabled':False,'manual_ticks':False}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('LANE_FEED_VALIDATION',output,json.dumps(summary),flush=True)
    return 0 if passed else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--lane-regions',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not args.execute:
        print('Description only; no cloud connection, cameras or worker started.');return 0
    return run(args.config.resolve(),args.lane_regions.resolve(),args.output_root)


if __name__=='__main__':raise SystemExit(main())
