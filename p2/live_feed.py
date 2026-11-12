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
import os
from pathlib import Path
import re
import signal
import threading
import time
from urllib.parse import urlparse
import uuid

from p2.capture_four import load_warmed_model, infer_frame, require_async, validate_config, utc_now
from p2.lane_counts import measure, validate_regions


def check_clock_mode(world, mode):
    if mode not in ('standalone','observer'):
        raise ValueError('Unknown clock mode.')
    if mode=='standalone':
        require_async(world)
    # An observer accepts frames from an external coordinator and never ticks.


def _light_state_name(state):
    """Return a stable, JSON-safe CARLA light-state name."""
    value=getattr(state,'name',str(state))
    return value.rsplit('.',1)[-1].upper()


def read_signal_states(world, cameras):
    """Read, but never control, the configured CARLA traffic lights.

    CARLA exposes the OpenDRIVE identifier through different accessors across
    builds, so support both forms.  Unknown IDs remain ``UNAVAILABLE`` rather
    than being guessed from the SUMO schedule.
    """
    wanted={str(signal) for camera in cameras for signal in camera.get('opendrive_signal_ids',[])}
    states={}
    for actor in world.get_actors().filter('traffic.traffic_light'):
        try:
            getter=getattr(actor,'get_opendrive_id',None)
            signal_id=getter() if callable(getter) else actor.attributes.get('opendrive_id')
            signal_id=str(signal_id) if signal_id is not None else None
            if signal_id in wanted:
                states[signal_id]=_light_state_name(actor.get_state())
        except Exception:
            # A disappearing actor must not take down perception publishing.
            continue
    return {camera['camera_id']:{str(signal):states.get(str(signal),'UNAVAILABLE')
                                 for signal in camera.get('opendrive_signal_ids',[])}
            for camera in cameras}


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>AEGIS camera feed</title><style>
body{font:15px system-ui;background:#101826;color:#e8edf4;margin:24px}h1{font-size:24px}#status{color:#7dd3fc}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px}
article{background:#1b283c;border:1px solid #334155;border-radius:12px;padding:14px}
img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#080f1a}.meta{color:#b8c7d9;line-height:1.7}
.warn{color:#fbbf24}button{padding:8px}small{color:#b8c7d9}</style></head><body>
<h1>AEGIS · camera feed</h1><p id="status">Connecting…</p>
<p class="warn">Counts cover reviewed lane regions. Occluded or stale counts are unavailable. Vehicle occupancy is not queue length.</p>
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
card.lastChild.textContent=c.status+' · whole-frame vehicles: '+(c.observed_vehicle_count??'unavailable')+' · lane occupancy: '+JSON.stringify(c.lane_counts??{})+' · count frame '+(c.frame_id??'—')+
' · sim age '+(c.age_sim_s==null?'unknown':c.age_sim_s.toFixed(2)+'s')+' · wall age '+(c.wall_age_s==null?'unknown':c.wall_age_s.toFixed(2)+'s')+
' · preview age '+(c.preview_age_sim_s==null?'unknown':c.preview_age_sim_s.toFixed(2)+'s')+' · captured '+(c.received_at_utc??'waiting');card.className=c.status==='fresh'?'':'warn'}
}catch(e){document.getElementById('status').textContent='OFFLINE · feed unavailable';for(const card of cards.values())card.lastChild.textContent='OFFLINE · last image is historical'}
if(active)setTimeout(poll,500)}poll();</script></body></html>'''


class FeedStore:
    """Bounded JPEG cache permits slow transfers without a disk frame dump."""
    def __init__(self, camera_ids, run_id, threshold=2.0, max_frames_per_camera=32, lane_templates=None, signal_templates=None):
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
        self.lane_templates=lane_templates or {}
        self.signal_templates=signal_templates or {}
        self.signal_states={camera_id:{signal:'UNAVAILABLE' for signal in signals}
                            for camera_id,signals in self.signal_templates.items()}
        self.active_faults=[]
        self.previews={}
        self.fault_override=None

    def request_fault(self,camera_id,duration_s):
        if camera_id not in self.camera_ids: raise ValueError('Unknown camera.')
        if not 0 < duration_s <= 15: raise ValueError('Fault duration must be 1-15 seconds.')
        with self.lock:
            self.fault_override={'camera_id':camera_id,'expires_monotonic':time.monotonic()+duration_s}
            self.active_faults=[camera_id]
            return {'camera_id':camera_id,'duration_s':duration_s}

    def cache_frame(self,camera_id,token,jpeg):
        self.frames[token]=(camera_id,jpeg)
        tokens=[key for key,value in self.frames.items() if value[0]==camera_id]
        for expired in tokens[:-self.max_frames_per_camera]:self.frames.pop(expired)

    def publish_preview(self,camera_id,row,jpeg,sim_time):
        with self.lock:
            token=self.run_id+'_'+camera_id+'_preview_'+str(row['frame_id'])
            self.cache_frame(camera_id,token,jpeg)
            self.previews[camera_id]={**row,'preview_frame_id':token,'frame_url':'/api/v1/frames/'+token}
            self.sim_time=max(sim_time,self.sim_time) if self.sim_time is not None else sim_time

    def publish(self, rows, sim_time):
        with self.lock:
            for camera_id,row,jpeg in rows:
                token=self.run_id+'_'+camera_id+'_'+str(row['frame_id'])
                row=copy.deepcopy(row)
                row.update(preview_frame_id=token,frame_url='/api/v1/frames/'+token)
                self.cache_frame(camera_id,token,jpeg)
                self.rows[camera_id]=row
            self.sim_time=max(sim_time,self.sim_time) if self.sim_time is not None else sim_time
            self.revision+=1
            self.phase='RUNNING'
            self.events.append({'state_revision':self.revision,'published_at_utc':utc_now()})

    def set_phase(self, phase, error=None):
        with self.lock:
            self.phase=phase
            self.error=error

    def publish_signal_states(self, states):
        """Publish a read-only snapshot of CARLA's current signal states."""
        with self.lock:
            self.signal_states=copy.deepcopy(states)

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
                preview=self.previews.get(camera_id,row)
                preview_wall=now-datetime.fromisoformat(preview['received_at_utc']).timestamp() if preview.get('received_at_utc') else None
                preview_time=preview.get('source_sim_time_s')
                preview_age=self.sim_time-preview_time if self.sim_time is not None and preview_time is not None and self.sim_time>=preview_time else None
                cameras.append({'camera_id':camera_id,'frame_id':row.get('frame_id'),
                    'source_sim_time_s':captured,'received_at_utc':row.get('received_at_utc'),
                    'age_sim_s':age,'wall_age_s':max(0,wall) if wall is not None else None,
                    'status':status,'missing':missing,'stale':stale,
                    'observed_vehicle_count':row.get('vehicle_count') if status=='fresh' else None,
                    'counts_by_class':row.get('counts_by_class') if status=='fresh' else None,
                    'lane_counts':(row.get('lane_counts') if status=='fresh' else
                        {lane:None for lane in self.lane_templates[camera_id]}) if camera_id in self.lane_templates else None,
                    'lane_count_semantics':'detected_vehicle_roi_occupancy' if camera_id in self.lane_templates else None,
                    'queue_estimate':None,
                    'traffic_lights':copy.deepcopy(self.signal_states.get(camera_id,{})),
                    'preview_frame_id':preview.get('preview_frame_id'),'frame_url':preview.get('frame_url'),
                    'preview_source_frame_id':preview.get('frame_id'),
                    'preview_source_sim_time_s':preview.get('source_sim_time_s'),
                    'preview_received_at_utc':preview.get('received_at_utc'),
                    'preview_width':preview.get('width'),'preview_height':preview.get('height'),
                    'preview_annotated':camera_id not in self.previews,
                    'preview_wall_age_s':preview_wall,
                    'preview_age_sim_s':preview_age,
                    'preview_stale':preview_wall is None or preview_wall<0 or preview_wall>self.threshold or preview_age is None or preview_age>self.threshold or self.phase not in ('STARTING','RUNNING'),
                    'inference_call_wall_ms':row.get('inference_call_wall_ms'),'error':row.get('error')})
            return {'schema_version':'aegis.p2.live-feed.v1-draft','mode':'LIVE' if self.phase=='RUNNING' else self.phase,
                    'run_id':self.run_id,'state_revision':self.revision,'phase':self.phase,
                    'as_of_sim_time_s':self.sim_time,'generated_at_utc':utc_now(),
                    'ready_for_live_policy':False,'lane_attribution_status':'partial_reviewed_regions' if self.lane_templates else 'uncalibrated',
                    'active_faults':list(self.active_faults),
                    'error':self.error,'cameras':cameras}

    def frame(self, token):
        with self.lock:
            entry=self.frames.get(token)
            return entry[1] if entry else None


def make_handler(store, allowed_origin=None, fault_token=None):
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
            # Drain ordinary small requests before closing so clients receive
            # the explicit refusal rather than a reset from an unread body.
            try:
                length=int(self.headers.get('Content-Length','0'))
            except ValueError:
                length=0
            body=b''
            if 0<length<=4096:
                self.connection.settimeout(2)
                body=self.rfile.read(length)
            path=urlparse(self.path).path
            if path!='/api/v1/faults':
                self.reply({'error':'read_only_feed'},status=405); return
            auth=self.headers.get('Authorization','')
            if not fault_token or auth!='Bearer '+fault_token:
                self.reply({'error':'unauthorized'},status=401); return
            try:
                payload=json.loads(body or b'{}')
                result=store.request_fault(str(payload.get('camera_id','')),float(payload.get('duration_s',0)))
                self.reply({'ok':True,'active_fault':result})
            except (ValueError,TypeError) as exc:
                self.reply({'error':'invalid_request','detail':str(exc)},status=400)

    return Handler


def run(config, duration, port, output_root, allowed_origin, clock_mode='standalone',lane_regions=None,fault=None):
    import carla
    import cv2
    import numpy as np
    client=carla.Client('127.0.0.1',2000)
    client.set_timeout(8)
    if (client.get_client_version(),client.get_server_version())!=('0.9.15','0.9.15'):
        raise RuntimeError('CARLA version mismatch.')
    world=client.get_world()
    check_clock_mode(world,clock_mode)
    if world.get_map().name!=config['map'] or list(world.get_actors().filter('sensor.camera.rgb')):
        raise RuntimeError('Map mismatch or existing cameras; inspect ownership before continuing.')
    run_id=datetime.now(timezone.utc).strftime('p2-feed-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    output=output_root/run_id
    output.mkdir(parents=True,exist_ok=False)
    if lane_regions is not None:
        validate_regions(lane_regions,config)
        if hashlib.sha256(world.get_map().to_opendrive().encode()).hexdigest()!=lane_regions['xodr_sha256']:
            raise RuntimeError('Live map geometry differs from the calibrated map.')
    camera_regions={c['camera_id']:c for c in lane_regions['cameras']} if lane_regions else {}
    templates={key:[r['lane_id'] for r in c['regions']] for key,c in camera_regions.items()}
    signals={camera['camera_id']:[str(signal) for signal in camera.get('opendrive_signal_ids',[])]
             for camera in config['cameras']}
    store=FeedStore([c['camera_id'] for c in config['cameras']],run_id,config['stale_after_sim_s'],
                    lane_templates=templates,signal_templates=signals)
    server=ThreadingHTTPServer(('127.0.0.1',port),make_handler(store,allowed_origin,os.environ.get('AEGIS_FAULT_TOKEN')))
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
    preview_thread=None
    preview_errors=[]
    def callback(camera_id):
        def receive(image):
            with buffer_lock:
                latest[camera_id]=(image,utc_now())
        return receive
    print('LIVE_FEED_OUTPUT',output,flush=True)
    print('LIVE_FEED_URL http://127.0.0.1:'+str(port),flush=True)
    def publish_previews():
        processed_preview={}
        try:
            while not stop.is_set():
                started=time.monotonic()
                with buffer_lock:samples=dict(latest)
                with store.lock:dropped=set(store.active_faults)
                for camera_id,(image,received) in samples.items():
                    if camera_id in dropped or processed_preview.get(camera_id)==image.frame:continue
                    bgr=np.frombuffer(image.raw_data,dtype=np.uint8).reshape(image.height,image.width,4)[:,:,:3]
                    width=config.get('preview_width',640);height=round(image.height*width/image.width)
                    small=cv2.resize(bgr,(width,height),interpolation=cv2.INTER_AREA)
                    ok,encoded=cv2.imencode('.jpg',small,[cv2.IMWRITE_JPEG_QUALITY,70])
                    if not ok:raise RuntimeError('Independent preview JPEG encoding failed.')
                    store.publish_preview(camera_id,{'frame_id':image.frame,'source_sim_time_s':image.timestamp,
                        'received_at_utc':received,'width':width,'height':height},encoded.tobytes(),
                        world.get_snapshot().timestamp.elapsed_seconds)
                    processed_preview[camera_id]=image.frame
                stop.wait(max(0,1/config['independent_preview_hz']-(time.monotonic()-started)))
        except Exception as exc:
            preview_errors.append(type(exc).__name__+': '+str(exc));stop.set()
    try:
        model,timings=load_warmed_model(Path(config['weights_path']),config,output)
        for camera in config['cameras']:
            check_clock_mode(world,clock_mode)
            bp=world.get_blueprint_library().find('sensor.camera.rgb')
            for key,value in [('image_size_x',config['image_width']),('image_size_y',config['image_height']),('fov',config['fov']),
                              ('sensor_tick',config['sensor_tick_s']),('role_name','aegis_p2_feed_'+camera['camera_id'])]:
                bp.set_attribute(key,str(value))
            t=camera['transform']
            sensor=world.spawn_actor(bp,carla.Transform(carla.Location(x=t['x'],y=t['y'],z=t['z']),
                                     carla.Rotation(pitch=t['pitch'],yaw=t['yaw'],roll=t['roll'])))
            owned.append(sensor)
            sensor.listen(callback(camera['camera_id']))
        deadline=time.monotonic()+duration
        if config.get('independent_preview_hz'):
            preview_thread=threading.Thread(target=publish_previews,daemon=True);preview_thread.start()
        with (output/'observations.jsonl').open('x',encoding='utf-8') as log:
            while not stop.is_set() and time.monotonic()<deadline:
                started=time.monotonic()
                check_clock_mode(world,clock_mode)
                batch=[]
                elapsed=duration-(deadline-time.monotonic())
                dropping=[fault['camera_id']] if fault and fault['start_s']<=elapsed<fault['start_s']+fault['duration_s'] else []
                with store.lock:
                    override=store.fault_override
                    if override and time.monotonic() < override['expires_monotonic']:
                        dropping.append(override['camera_id'])
                    elif override:
                        store.fault_override=None
                    store.active_faults=sorted(set(dropping))
                store.publish_signal_states(read_signal_states(world,config['cameras']))
                for camera in config['cameras']:
                    camera_id=camera['camera_id']
                    if camera_id in dropping:continue
                    with buffer_lock:
                        sample=latest.get(camera_id)
                    if sample is None:continue
                    image,received=sample
                    if processed.get(camera_id)==image.frame:
                        continue
                    row={'frame_id':image.frame,'source_sim_time_s':image.timestamp,'received_at_utc':received,'error':None}
                    bgr=np.frombuffer(image.raw_data,dtype=np.uint8).reshape(image.height,image.width,4)[:,:,:3].copy()
                    try:
                        detections,annotated,elapsed=infer_frame(model,bgr,cv2,config)
                        counts=dict(Counter(d['class_name'] for d in detections))
                        row.update(counts_by_class=counts,vehicle_count=sum(counts.get(name,0) for name in config['vehicle_classes']),
                                   inference_call_wall_ms=elapsed)
                        if camera_id in camera_regions:
                            lane_result=measure(detections,camera_regions[camera_id],config['vehicle_classes'],
                                enabled=lane_regions['can_publish_lane_counts'],anchor='center' if config.get('tiled_inference') else 'bottom_center')
                            row['lane_counts']=lane_result['lane_counts']
                    except Exception as exc:
                        annotated=bgr
                        row['error']=type(exc).__name__+': '+str(exc)
                    ok,encoded=cv2.imencode('.jpg',annotated,[cv2.IMWRITE_JPEG_QUALITY,75])
                    if not ok:
                        raise RuntimeError('JPEG encoding failed.')
                    # Publish immediately; a slower camera must not hold back fresh results.
                    store.publish([(camera_id,row,encoded.tobytes())],world.get_snapshot().timestamp.elapsed_seconds)
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
        if preview_thread:
            preview_thread.join(timeout=10)
            if preview_thread.is_alive():preview_errors.append('Preview thread did not stop within its deadline.')
        if preview_errors and failure is None:failure='; '.join(preview_errors)
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
                 'cleanup_errors':cleanup,'error':failure,'final_snapshot':store.snapshot(),'clock_mode':clock_mode}
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
    parser.add_argument('--clock-mode',choices=('standalone','observer'),default='standalone')
    parser.add_argument('--lane-regions',type=Path)
    parser.add_argument('--drop-camera')
    parser.add_argument('--drop-after',type=float,default=10)
    parser.add_argument('--drop-for',type=float,default=8)
    args=parser.parse_args()
    config_text=args.config.read_text(encoding='utf-8') if args.config else base64.b64decode(args.config_base64,validate=True).decode()
    config=validate_config(json.loads(config_text))
    regions=validate_regions(json.loads(args.lane_regions.read_text(encoding='utf-8')),config) if args.lane_regions else None
    if args.drop_camera and (args.drop_camera not in {c['camera_id'] for c in config['cameras']} or
        not 0<=args.drop_after<=args.duration or not 0<args.drop_for<=args.duration-args.drop_after):
        parser.error('Fault camera and bounded timing must fit this run.')
    fault={'camera_id':args.drop_camera,'start_s':args.drop_after,'duration_s':args.drop_for} if args.drop_camera else None
    if not 10<=args.duration<=3600 or not 1024<=args.port<=65535:
        parser.error('Use a 10–3600 second duration and a nonprivileged port.')
    if not args.execute:
        print('Description only; no cameras, API, or simulator connection created.')
        return 0
    return run(config,args.duration,args.port,args.output_root,args.allowed_origin,args.clock_mode,regions,fault)


if __name__=='__main__':
    raise SystemExit(main())
