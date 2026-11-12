"""Local-only contract demo. All traffic values are fixtures, not measurements.
Run: python -m aegis_helpers.mock_server --port 8000
"""
import argparse,json,os,threading,time,math
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse
class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.failed = set()
        self.revision = 0
        self.processed_requests = {}
    def snapshot(self):
        with self.lock:
            junctions=[]
            for i in range(1,5):
                j=f'J{i}';bad=j in self.failed
                junctions.append({'junction_id':j,'phase':'NS_GREEN',
                    'camera_status':'MISSING' if bad else 'AVAILABLE',
                    'observed_count':None if bad else 3+i,
                    'estimated_queue':float(3+i),'queue_interval':[2+i,7+i] if bad else [3+i,3+i],
                    'source':'mock','data_quality':'fixture'})
            return {'schema_version':'1.0','mode':'MOCK','run_id':'local-fixture',
                'state_revision':self.revision,'sim_time_s':100.0,
                'notice':'DEVELOPMENT FIXTURES. NO CARLA, YOLO, MARL OR REAL METRICS.',
                'junctions':junctions,'plans':[], 'metrics':None}
    def fault(self,j,enabled,request_id=None):
        with self.lock:
            if request_id is not None and request_id in self.processed_requests:
                return False
            if enabled:self.failed.add(j)
            else:self.failed.discard(j)
            self.revision+=1
            if request_id is not None:
                self.processed_requests[request_id]=True
            return True
    def reset(self,request_id=None):
        with self.lock:
            if request_id is not None and request_id in self.processed_requests:
                return False
            self.failed.clear()
            self.revision+=1
            if request_id is not None:
                self.processed_requests[request_id]=True
            return True

def make_handler(store:Store,token:str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def send_json(self,obj,status=200):
            raw=json.dumps(obj).encode();self.send_response(status)
            self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            path=urlparse(self.path).path
            if path=='/health':return self.send_json({'ok':True,'mode':'MOCK'})
            if path=='/api/v1/snapshot':return self.send_json(store.snapshot())
            if path=='/':
                body=(Path(__file__).resolve().parent.parent/'web'/'index.html').read_bytes()
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
                self.send_header('Content-Length',str(len(body)));self.end_headers();return self.wfile.write(body)
            self.send_json({'error':'not_found'},404)
        def do_POST(self):
            if self.headers.get('Authorization')!='Bearer '+token:
                return self.send_json({'error':'unauthorized'},401)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0 <= size <= 4096:return self.send_json({'error':'body_too_large'},413)
                obj=json.loads(self.rfile.read(size) or b'{}')
                if not isinstance(obj,dict):raise ValueError('Expected JSON object')
                req_id=obj.get('request_id')
                if req_id is not None and (not isinstance(req_id,str) or not req_id.strip() or len(req_id)>128):
                    raise ValueError('Bad request_id')
                if self.path=='/api/v1/reset':
                    store.reset(req_id)
                    return self.send_json(store.snapshot())
                if self.path!='/api/v1/faults':return self.send_json({'error':'not_found'},404)
                j=obj.get('junction_id');enabled=obj.get('enabled')
                if j not in {'J1','J2','J3','J4'} or not isinstance(enabled,bool):raise ValueError('Bad fault fields')
                store.fault(j,enabled,req_id)
                self.send_json(store.snapshot())
            except (ValueError,TypeError):self.send_json({'error':'invalid_request'},400)
    return Handler

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8000);p.add_argument('--host',default='127.0.0.1');a=p.parse_args()
    token=os.environ.get('AEGIS_OPERATOR_TOKEN','local-demo-only')
    srv=ThreadingHTTPServer((a.host,a.port),make_handler(Store(),token))
    print(f'MOCK ONLY: http://127.0.0.1:{a.port} ; operator token from AEGIS_OPERATOR_TOKEN or local-demo-only',flush=True)
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()
if __name__=='__main__':main()
