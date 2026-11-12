"""Continuous camera/YOLO producer with a loopback-only read-only frame adapter.

P4 can consume the existing /health, /api/v1/snapshot and /api/v1/frames routes.
This module never steps CARLA/SUMO, changes maps/settings, or controls signals.
"""
import argparse
import base64
from collections import Counter, OrderedDict, deque
import copy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import signal
import threading
import time
from urllib.parse import urlparse
import uuid

from p2.capture_four import load_warmed_model, infer_frame, require_async, validate_config, utc_now


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>AEGIS camera feed</title><style>
body{font:15px system-ui;background:#101826;color:#e8edf4;margin:24px}h1{font-size:24px}#status{color:#7dd3fc}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px}
article{background:#1b283c;border:1px solid #334155;border-radius:12px;padding:14px}
img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#080f1a}.meta{color:#b8c7d9;line-height:1.7}
.warn{color:#fbbf24}button{padding:8px}small{color:#b8c7d9}</style></head><body>
<h1>AEGIS · camera feed</h1><p id="status">Connecting…</p>
<p class="warn">Whole-image detections · lane counts and queues are uncalibrated. Parked cars may be counted.</p>
<div class="grid" id="grid"></div><p><small>Read-only P2 integration preview. P4 owns the application frontend.</small></p>
<script>
const cards=new Map();let active=true;
async function poll(){try{const r=await fetch('/api/v1/snapshot',{cache:'no-store'});if(!r.ok)throw Error(r.status);
const s=await r.json();document.getElementById('status').textContent=s.mode+' · revision '+s.state_revision+' · '+s.phase;
for(const c of s.cameras){let card=cards.get(c.camera_id);if(!card){card=document.createElement('article');
const title=document.createElement('h2');title.textContent=c.camera_id;card.append(title,document.createElement('img'),document.createElement('div'));
card.lastChild.className='meta';document.getElementById('grid').append(card);cards.set(c.camera_id,card)}
const img=card.querySelector('img');if(c.frame_url&&img.dataset.frame!==c.preview_frame_id&&img.dataset.loading!=='yes'){
const token=c.preview_frame_id;img.dataset.loading='yes';img.onload=()=>{img.dataset.frame=token;img.dataset.loading='no'};
img.onerror=()=>{img.dataset.loading='no'};img.src=c.frame_url}
card.lastChild.textContent=c.status+' · vehicles: '+(c.observed_vehicle_count??'unavailable')+' · frame '+(c.frame_id??'—')+
' · sim age '+(c.age_sim_s==null?'unknown':c.age_sim_s.toFixed(2)+'s')+' · wall age '+(c.wall_age_s==null?'unknown':c.wall_age_s.toFixed(2)+'s')+
' · captured '+(c.received_at_utc??'waiting');card.className=c.status==='fresh'?'':'warn'}
}catch(e){document.getElementById('status').textContent='OFFLINE · feed unavailable';for(const card of cards.values())card.lastChild.textContent='OFFLINE · last image is historical'}
if(active)setTimeout(poll,500)}poll();</script></body></html>'''


class FeedStore:
    """Bounded JPEG cache permits slow transfers without a disk frame dump."""
    def __init__(self, camera_ids, run_id, threshold=2.0, max_frames_per_camera=32):
        self.lock=threading.Lock()
        self.camera_ids=list(camera_ids)
        self.run_id=run_id
        self.threshold=threshold
        self.max_frames_per_camera=max_frames_per_camera
        self.rows={}
        self.frames=OrderedDict()
        self.events=deque(maxlen=20)
        self.revision=0
        self.sim_time=None
        self.phase='STARTING'
        self.error=None

    def publish(self, rows, sim_time):
        with self.lock:
            for camera_id,row,jpeg in rows:
                token=self.run_id+'_'+camera_id+'_'+str(row['frame_id'])
                row=copy.deepcopy(row)
                row.update(preview_frame_id=token,frame_url='/api/v1/frames/'+token)
                self.frames[token]=(camera_id,jpeg)
                tokens=[key for key,value in self.frames.items() if value[0]==camera_id]
                for expired in tokens[:-self.max_frames_per_camera]:
                    self.frames.pop(expired)
                self.rows[camera_id]=row
            self.sim_time=sim_time
            self.revision+=1
            self.phase='RUNNING'
            self.events.append({'state_revision':self.revision,'published_at_utc':utc_now()})

    def set_phase(self, phase, error=None):
        with self.lock:
            self.phase=phase
            self.error=error

    def snapshot(self, now=None):
        now=time.time() if now is None else now
        with self.lock:
            cameras=[]
            for camera_id in self.camera_ids:
                row=copy.deepcopy(self.rows.get(camera_id,{}))
                captured=row.get('source_sim_time_s')
                age=self.sim_time-captured if self.sim_time is not None and captured is not None and self.sim_time>=captured else None
                wall=now-datetime.fromisoformat(row['received_at_utc']).timestamp() if row.get('received_at_utc') else None
                stale=(age is None or age>self.threshold or wall is None or wall<0 or wall>self.threshold)
                missing=not row
                status=('missing' if missing else 'detector_error' if row.get('error') else
                        'stopped' if self.phase not in ('RUNNING','STARTING') else 'stale' if stale else 'fresh')
                cameras.append({'camera_id':camera_id,'frame_id':row.get('frame_id'),
                    'source_sim_time_s':captured,'received_at_utc':row.get('received_at_utc'),
                    'age_sim_s':age,'wall_age_s':max(0,wall) if wall is not None else None,
                    'status':status,'missing':missing,'stale':stale,
                    'observed_vehicle_count':row.get('vehicle_count') if status=='fresh' else None,
                    'counts_by_class':row.get('counts_by_class') if status=='fresh' else None,
                    'lane_counts':None,'queue_estimate':None,
                    'preview_frame_id':row.get('preview_frame_id'),'frame_url':row.get('frame_url'),
                    'inference_call_wall_ms':row.get('inference_call_wall_ms'),'error':row.get('error')})
            return {'schema_version':'aegis.p2.live-feed.v1-draft','mode':'LIVE' if self.phase=='RUNNING' else self.phase,
                    'run_id':self.run_id,'state_revision':self.revision,'phase':self.phase,
                    'as_of_sim_time_s':self.sim_time,'generated_at_utc':utc_now(),
                    'ready_for_live_policy':False,'lane_attribution_status':'uncalibrated',
                    'error':self.error,'cameras':cameras}

    def frame(self, token):
        with self.lock:
            entry=self.frames.get(token)
            return entry[1] if entry else None


def make_handler(store, allowed_origin=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass

        def reply(self,data,kind='application/json',status=200):
            body=json.dumps(data,allow_nan=False).encode() if kind=='application/json' else data
            self.send_response(status)
            self.send_header('Content-Type',kind)
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(body)))
            if allowed_origin and self.headers.get('Origin')==allowed_origin:
                self.send_header('Access-Control-Allow-Origin',allowed_origin)
                self.send_header('Vary','Origin')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path=urlparse(self.path).path
            if path=='/':
                return self.reply(PAGE.encode(),'text/html; charset=utf-8')
            if path=='/health':
                snapshot=store.snapshot()
                return self.reply({'ok':snapshot['phase']=='RUNNING' and all(c['status']=='fresh' for c in snapshot['cameras']),
                                   'mode':snapshot['mode'],'run_id':snapshot['run_id'],
                                   'ready_for_live_policy':False,'phase':snapshot['phase'],'error':snapshot['error']})
            if path=='/api/v1/snapshot':
                return self.reply(store.snapshot())
            if path=='/api/v1/events':
                with store.lock:
                    events=list(store.events)
                return self.reply({'events':events})
            if path.startswith('/api/v1/frames/'):
                token=path[len('/api/v1/frames/'):]
                if re.fullmatch('[a-zA-Z0-9_-]{1,160}',token):
                    jpeg=store.frame(token)
                    if jpeg is not None:
                        return self.reply(jpeg,'image/jpeg')
            return self.reply({'error':'not_found_or_expired'},status=404)

        def do_POST(self):
            self.reply({'error':'read_only_feed'},status=405)

    return Handler


def run(config, duration, port, output_root, allowed_origin):
    import carla
    import cv2
    import numpy as np
    client=carla.Client('127.0.0.1',2000)
    client.set_timeout(8)
    if (client.get_client_version(),client.get_server_version())!=('0.9.15','0.9.15'):
        raise RuntimeError('CARLA version mismatch.')
    world=client.get_world()
    require_async(world)
    if world.get_map().name!=config['map'] or list(world.get_actors().filter('sensor.camera.rgb')):
        raise RuntimeError('Map mismatch or existing cameras; inspect ownership before continuing.')
    run_id=datetime.now(timezone.utc).strftime('p2-feed-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    output=output_root/run_id
    output.mkdir(parents=True,exist_ok=False)
    store=FeedStore([c['camera_id'] for c in config['cameras']],run_id,config['stale_after_sim_s'])
    server=ThreadingHTTPServer(('127.0.0.1',port),make_handler(store,allowed_origin))
    server.daemon_threads=True
    http_thread=threading.Thread(target=server.serve_forever,daemon=True)
    http_thread.start()
    stop=threading.Event()
    for name in ('SIGINT','SIGTERM','SIGHUP'):
        if hasattr(signal,name):
            signal.signal(getattr(signal,name),lambda *_:stop.set())
    latest={}
    processed={}
    buffer_lock=threading.Lock()
    owned=[]
    cleanup=[]
    failure=None
    def callback(camera_id):
        def receive(image):
            with buffer_lock:
                latest[camera_id]=(image,utc_now())
        return receive
    print('LIVE_FEED_OUTPUT',output,flush=True)
    print('LIVE_FEED_URL http://127.0.0.1:'+str(port),flush=True)
    try:
        model,timings=load_warmed_model(Path(config['weights_path']),config,output)
        for camera in config['cameras']:
            require_async(world)
            bp=world.get_blueprint_library().find('sensor.camera.rgb')
            for key,value in [('image_size_x',960),('image_size_y',540),('fov',config['fov']),
                              ('sensor_tick',0.2),('role_name','aegis_p2_feed_'+camera['camera_id'])]:
                bp.set_attribute(key,str(value))
            t=camera['transform']
            sensor=world.spawn_actor(bp,carla.Transform(carla.Location(x=t['x'],y=t['y'],z=t['z']),
                                     carla.Rotation(pitch=t['pitch'],yaw=t['yaw'],roll=t['roll'])))
            owned.append(sensor)
            sensor.listen(callback(camera['camera_id']))
        deadline=time.monotonic()+duration
        with (output/'observations.jsonl').open('x',encoding='utf-8') as log:
            while not stop.is_set() and time.monotonic()<deadline:
                started=time.monotonic()
                require_async(world)
                batch=[]
                with buffer_lock:
                    samples=dict(latest)
                for camera_id,(image,received) in samples.items():
                    if processed.get(camera_id)==image.frame:
                        continue
                    row={'frame_id':image.frame,'source_sim_time_s':image.timestamp,'received_at_utc':received,'error':None}
                    bgr=np.frombuffer(image.raw_data,dtype=np.uint8).reshape(image.height,image.width,4)[:,:,:3].copy()
                    try:
                        detections,annotated,elapsed=infer_frame(model,bgr,cv2,config)
                        counts=dict(Counter(d['class_name'] for d in detections))
                        row.update(counts_by_class=counts,vehicle_count=sum(counts.get(name,0) for name in config['vehicle_classes']),
                                   inference_call_wall_ms=elapsed)
                    except Exception as exc:
                        annotated=bgr
                        row['error']=type(exc).__name__+': '+str(exc)
                    ok,encoded=cv2.imencode('.jpg',annotated,[cv2.IMWRITE_JPEG_QUALITY,75])
                    if not ok:
                        raise RuntimeError('JPEG encoding failed.')
                    batch.append((camera_id,row,encoded.tobytes()))
                    processed[camera_id]=image.frame
                store.publish(batch,world.get_snapshot().timestamp.elapsed_seconds)
                snapshot=store.snapshot()
                log.write(json.dumps(snapshot,allow_nan=False)+'\n')
                log.flush()
                if store.revision%10==0:
                    print('FEED_REVISION',store.revision,[(c['camera_id'],c['status'],c['observed_vehicle_count']) for c in snapshot['cameras']],flush=True)
                stop.wait(max(0,0.5-(time.monotonic()-started)))
    except Exception as exc:
        failure=type(exc).__name__+': '+str(exc)
        print('LIVE_FEED_ERROR',failure,flush=True)
    finally:
        stop.set()
        store.set_phase('FAILED' if failure else 'STOPPED',failure)
        for sensor in reversed(owned):
            try:
                sensor.stop()
            except Exception as exc:
                cleanup.append({'actor_id':sensor.id,'operation':'stop','error':str(exc)})
            try:
                if not sensor.destroy():
                    cleanup.append({'actor_id':sensor.id,'operation':'destroy','error':'returned false'})
            except Exception as exc:
                cleanup.append({'actor_id':sensor.id,'operation':'destroy','error':str(exc)})
        summary={'run_id':run_id,'revisions':store.revision,'duration_limit_s':duration,
                 'cleanup_errors':cleanup,'error':failure,'final_snapshot':store.snapshot()}
        (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        server.shutdown()
        server.server_close()
        http_thread.join(timeout=5)
        print('LIVE_FEED_FINISHED',json.dumps({'revisions':store.revision,'cleanup_errors':cleanup,'error':failure}),flush=True)
    return 1 if failure or cleanup else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config-base64')
    source.add_argument('--config',type=Path)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--duration',type=int,default=600)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--output-root',type=Path,default=Path('/workspace/aegis/evidence/live-feed'))
    parser.add_argument('--allowed-origin')
    args=parser.parse_args()
    config_text=args.config.read_text(encoding='utf-8') if args.config else base64.b64decode(args.config_base64,validate=True).decode()
    config=validate_config(json.loads(config_text))
    if not 10<=args.duration<=3600 or not 1024<=args.port<=65535:
        parser.error('Use a 10–3600 second duration and a nonprivileged port.')
    if not args.execute:
        print('Description only; no cameras, API, or simulator connection created.')
        return 0
    return run(config,args.duration,args.port,args.output_root,args.allowed_origin)


if __name__=='__main__':
    raise SystemExit(main())
