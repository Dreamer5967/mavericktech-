"""Local-only contract demo and Emergency Green Corridor integration.
All traffic values are fixtures, not measurements.
Run: python -m aegis_helpers.mock_server --port 8000
"""
import argparse, json, os, threading, time, math
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

try:
    from aegis_helpers.corridor_service import EmergencyCorridorService, CorridorStage
except ImportError:
    from starter.aegis_helpers.corridor_service import EmergencyCorridorService, CorridorStage

class Store:
    def __init__(self, operator_secret: str = "local-demo-only"):
        self.lock = threading.Lock()
        self.failed = set()
        self.revision = 0
        self.corridor = EmergencyCorridorService()
        self.operator_secret = operator_secret
        self.last_tick = time.time()

    def snapshot(self):
        with self.lock:
            # Advance corridor automatically if active
            now = time.time()
            dt = min(now - self.last_tick, 2.0)
            self.last_tick = now
            if self.corridor.stage != CorridorStage.STANDBY:
                self.corridor.tick(delta_s=dt)
                self.revision += 1

            corridor_telem = self.corridor.get_telemetry()
            junctions = []
            for i in range(1, 5):
                j = f'J{i}'
                bad = j in self.failed
                j_evc = corridor_telem["junctions"].get(j, {})
                phase = j_evc.get("phase", "NS_GREEN") if self.corridor.stage != CorridorStage.STANDBY else "NS_GREEN"
                q = float(j_evc.get("queue_count", 3 + i)) if self.corridor.stage != CorridorStage.STANDBY else float(3 + i)

                junctions.append({
                    'junction_id': j,
                    'phase': phase,
                    'camera_status': 'MISSING' if bad else 'AVAILABLE',
                    'observed_count': None if bad else int(q),
                    'estimated_queue': q,
                    'queue_interval': [q * 0.7, q * 1.5] if bad else [q, q],
                    'source': 'mock',
                    'data_quality': 'fixture'
                })
            return {
                'schema_version': '1.0',
                'mode': 'MOCK',
                'run_id': 'local-fixture',
                'state_revision': self.revision,
                'sim_time_s': 100.0,
                'notice': 'DEVELOPMENT FIXTURES. NO CARLA, YOLO, MARL OR REAL METRICS.',
                'junctions': junctions,
                'plans': [],
                'metrics': None,
                'emergency_corridor': corridor_telem
            }

    def fault(self, j, enabled):
        with self.lock:
            if enabled: self.failed.add(j)
            else: self.failed.discard(j)
            self.revision += 1

    def reset(self):
        with self.lock:
            self.failed.clear()
            self.corridor.cancel_corridor(self.operator_secret)
            self.revision += 1

def make_handler(store: Store, token: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def send_json(self, obj, status=200):
            raw = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/health': return self.send_json({'ok': True, 'mode': 'MOCK'})
            if path == '/api/v1/snapshot': return self.send_json(store.snapshot())
            if path == '/api/v1/emergency/status':
                with store.lock:
                    return self.send_json(store.corridor.get_telemetry())
            if path == '/' or path == '/index.html':
                web_dir = Path(__file__).resolve().parent.parent / 'web'
                idx = web_dir / 'index.html'
                if not idx.exists():
                    web_dir = Path(__file__).resolve().parent / 'web'
                    idx = web_dir / 'index.html'
                body = idx.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                return self.wfile.write(body)
            self.send_json({'error': 'not_found'}, 404)

        def do_POST(self):
            auth = self.headers.get('Authorization', '')
            if auth != 'Bearer ' + token:
                return self.send_json({'error': 'unauthorized'}, 401)
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 8192: return self.send_json({'error': 'body_too_large'}, 413)
                raw_body = self.rfile.read(size) or b'{}'
                obj = json.loads(raw_body)
                if not isinstance(obj, dict): raise ValueError('Expected JSON object')

                if self.path == '/api/v1/reset':
                    store.reset()
                    return self.send_json(store.snapshot())

                if self.path == '/api/v1/faults':
                    j = obj.get('junction_id')
                    enabled = obj.get('enabled')
                    if j not in {'J1', 'J2', 'J3', 'J4'} or not isinstance(enabled, bool):
                        raise ValueError('Bad fault fields')
                    store.fault(j, enabled)
                    return self.send_json(store.snapshot())

                # Emergency Corridor endpoints
                if self.path == '/api/v1/emergency/dispatch':
                    vid = obj.get('vehicle_id', 'AMB-101')
                    vtype = obj.get('vehicle_type', 'ambulance')
                    prio = int(obj.get('priority_level', 1))
                    with store.lock:
                        ok, msg, telem = store.corridor.dispatch_vehicle(
                            token=token, vehicle_id=vid, vehicle_type=vtype, priority_level=prio
                        )
                    if not ok:
                        return self.send_json({'error': msg}, 400)
                    store.revision += 1
                    return self.send_json({'ok': True, 'status': msg, 'telemetry': telem})

                if self.path == '/api/v1/emergency/cancel':
                    with store.lock:
                        ok, msg = store.corridor.cancel_corridor(token)
                    store.revision += 1
                    return self.send_json({'ok': ok, 'status': msg})

                if self.path == '/api/v1/emergency/tick':
                    dt = float(obj.get('delta_s', 1.0))
                    with store.lock:
                        telem = store.corridor.tick(delta_s=dt)
                    store.revision += 1
                    return self.send_json(telem)

                self.send_json({'error': 'not_found'}, 404)
            except (ValueError, TypeError) as e:
                self.send_json({'error': 'invalid_request', 'detail': str(e)}, 400)
    return Handler

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8000)
    p.add_argument('--host', default='127.0.0.1')
    a = p.parse_args()
    token = os.environ.get('AEGIS_OPERATOR_TOKEN', 'local-demo-only')
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(Store(token), token))
    print(f'AEGIS Mission Control Server running at http://{a.host}:{a.port}', flush=True)
    print(f'Operator Token: {token}', flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: srv.server_close()

if __name__ == '__main__':
    main()
