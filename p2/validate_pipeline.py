"""Prepared camera + fixed-time bridge validation; explicit clock approval required."""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import urlopen
import uuid


def stop_owned(process, sig):
    if process is not None and process.poll() is None:
        process.send_signal(sig)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def run(args):
    if os.environ.get('AEGIS_APPROVE_LIVE_COSIM')!='yes':
        raise RuntimeError('Explicit live-clock approval is required; no child was started.')
    import carla
    client=carla.Client('127.0.0.1',2000);client.set_timeout(8)
    world=client.get_world()
    config=json.loads(args.config.read_text(encoding='utf-8'))
    if world.get_map().name!=config['map'] or world.get_settings().synchronous_mode:
        raise RuntimeError('Unexpected map or an existing synchronous clock owner.')
    if list(world.get_actors().filter('sensor.camera.rgb')):
        raise RuntimeError('Existing RGB sensors require ownership review before validation.')
    if (client.get_client_version(),client.get_server_version())!=('0.9.15','0.9.15'):
        raise RuntimeError('CARLA client/server version mismatch.')
    if not args.scenario.is_file():
        raise RuntimeError('Reviewed scenario is missing; no camera or bridge was started.')
    output=args.output_root/(datetime.now(timezone.utc).strftime('pipeline-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    environment=os.environ.copy()
    environment['SUMO_HOME']='/workspace/aegis/venv-sim/lib/python3.10/site-packages/sumo'
    environment['PATH']='/workspace/aegis/venv-sim/bin:'+environment.get('PATH','')
    environment['PYTHONPATH']=str(Path(__file__).resolve().parent.parent)
    feed=bridge=None
    samples=[]
    synchronous_samples=[]
    previews={}
    error=None
    try:
        with (output/'feed.log').open('x',encoding='utf-8') as feed_log, (output/'bridge.log').open('x',encoding='utf-8') as bridge_log:
            lane_args=['--lane-regions',str(args.lane_regions.resolve())] if getattr(args,'lane_regions',None) else []
            feed=subprocess.Popen([sys.executable,'-B','-u','-m','p2.live_feed','--execute','--config',str(args.config.resolve()),
                 '--duration','120','--port',str(args.port),'--clock-mode','observer','--output-root',str(output/'frames')]+lane_args,
                 stdout=feed_log,stderr=subprocess.STDOUT,env=environment)
            deadline=time.monotonic()+45
            while True:
                if feed.poll() is not None:
                    raise RuntimeError('Camera worker exited; inspect feed.log.')
                try:
                    with urlopen(f'http://127.0.0.1:{args.port}/health',timeout=1) as response:
                        if json.load(response)['ok']:
                            break
                except OSError:
                    pass
                if time.monotonic()>deadline:
                    raise RuntimeError('Camera warm-up/readiness exceeded the bounded startup wait.')
                time.sleep(0.2)
            bridge=subprocess.Popen([sys.executable,'-B','-u','-m','p2.bridge_validation','--execute',
                '--scenario',str(args.scenario.resolve()),'--config',str(args.config.resolve()),
                '--output',str(output/'bridge'),'--seconds',str(args.seconds)]+(
                ['--policy-checkpoint',str(args.policy_checkpoint.resolve()),'--policy-sha256',args.policy_sha256]
                if args.policy_checkpoint else []),
                stdout=bridge_log,stderr=subprocess.STDOUT,env=environment)
            started=time.monotonic()
            while bridge.poll() is None:
                if time.monotonic()-started>args.seconds+30:
                    raise RuntimeError('Bridge process exceeded startup/cleanup deadline.')
                if feed.poll() is not None:
                    raise RuntimeError('Camera worker failed during the synchronized run.')
                with urlopen(f'http://127.0.0.1:{args.port}/api/v1/snapshot',timeout=3) as response:
                    snapshot=json.load(response)
                samples.append(snapshot)
                if world.get_settings().synchronous_mode:
                    synchronous_samples.append(snapshot)
                    import cv2
                    import numpy as np
                    for camera in snapshot['cameras']:
                        if camera['status']!='fresh' or not camera['frame_url']:
                            continue
                        with urlopen(f'http://127.0.0.1:{args.port}'+camera['frame_url'],timeout=3) as response:
                            jpeg=response.read()
                        decoded=cv2.imdecode(np.frombuffer(jpeg,dtype=np.uint8),cv2.IMREAD_COLOR)
                        width=config.get('preview_width',config['image_width']);height=round(config['image_height']*width/config['image_width'])
                        if decoded is None or decoded.shape[:2]!=(height,width):
                            raise RuntimeError('Camera API JPEG dimensions differ from the configured profile.')
                        image_path=output/(camera['camera_id']+'.jpg')
                        image_path.write_bytes(jpeg)
                        previews[camera['camera_id']]={'file':image_path.name,'sha256':hashlib.sha256(jpeg).hexdigest(),
                            'frame_id':camera.get('preview_source_frame_id',camera['frame_id']),
                            'source_sim_time_s':camera.get('preview_source_sim_time_s',camera['source_sim_time_s']),
                            'received_at_utc':camera.get('preview_received_at_utc',camera['received_at_utc']),
                            'count_source_frame_id':camera['frame_id']}
                time.sleep(0.5)
            if bridge.returncode!=0:
                raise RuntimeError('Bridge verification failed; inspect bridge/summary.json and bridge.log.')
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc)
    finally:
        stop_owned(bridge,signal.SIGINT)
        stop_owned(feed,signal.SIGTERM)
    (output/'observations.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples),encoding='utf-8')
    remaining=[actor.id for actor in world.get_actors().filter('sensor.camera.rgb')]
    cameras={}
    for camera in config['cameras']:
        camera_id=camera['camera_id']
        rows=[c for s in synchronous_samples for c in s['cameras'] if c['camera_id']==camera_id]
        fresh=[c for c in rows if c['status']=='fresh']
        times=[c['source_sim_time_s'] for c in fresh]
        cameras[camera_id]={'synchronous_samples':len(rows),'fresh_samples':len(fresh),
            'distinct_fresh_frames':len({c['frame_id'] for c in fresh}),
            'source_time_span_s':max(times)-min(times) if times else 0,
            'preview':previews.get(camera_id)}
    passed=error is None and not remaining and world.get_map().name==config['map'] and not world.get_settings().synchronous_mode
    passed=passed and all(c['distinct_fresh_frames']>=3 and c['source_time_span_s']>0 and c['preview'] for c in cameras.values())
    summary={'status':'PASSED' if passed else 'FAILED',
             'mode':'FIXED_TIME_COSIM_WITH_CAMERA_OBSERVATIONS','learned_policy_enabled':False,
             'error':error,'snapshot_samples':len(samples),'remaining_rgb_actor_ids':remaining,
             'synchronous_snapshot_samples':len(synchronous_samples),'cameras':cameras,
             'post_map':world.get_map().name,'post_synchronous_mode':world.get_settings().synchronous_mode}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('PIPELINE_VALIDATION',output,json.dumps(summary),flush=True)
    return 0 if summary['status']=='PASSED' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--lane-regions',type=Path)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--policy-checkpoint',type=Path,
                        help='Optional verified checkpoint for read-only policy diagnostics.')
    parser.add_argument('--policy-sha256',help='Required with --policy-checkpoint.')
    parser.add_argument('--output-root',type=Path,default=Path('/workspace/aegis/evidence/pipeline-validation'))
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not 1<=args.seconds<=30 or not 1024<=args.port<=65535:
        parser.error('Use at most 30 seconds and a nonprivileged port.')
    if (args.policy_checkpoint is None)!=(args.policy_sha256 is None):
        parser.error('Use --policy-checkpoint and --policy-sha256 together.')
    if not args.execute:
        print('Prepared only: warms observer first, then one bridge clock owner. No process or connection started.')
        return 0
    return run(args)


if __name__=='__main__':
    raise SystemExit(main())
