import unittest,math,threading,json,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
from aegis_helpers.budget import Budget
from aegis_helpers.contracts import LaneObservation
from aegis_helpers.phase_guard import TransitionRequest,check_request,transition_sequence
from aegis_helpers.mock_server import Store,make_handler
class BudgetTests(unittest.TestCase):
 def test_normal(self):self.assertAlmostEqual(Budget(5,.3,0,.5,1).hours(),3.5/.3)
 def test_storage(self):self.assertAlmostEqual(Budget(5,.3,.05,.5,1).hours(),10)
 def test_insufficient(self):self.assertEqual(Budget(1,.3,0,.5,1).hours(),0)
 def test_negative(self):
  with self.assertRaises(ValueError):Budget(-1,.3).hours()
 def test_zero_rate(self):
  with self.assertRaises(ValueError):Budget(5,0).hours()
 def test_nan(self):
  with self.assertRaises(ValueError):Budget(math.nan,.3).hours()
class ContractTests(unittest.TestCase):
 def obs(self,**kw):
  d=dict(lane_id='a',observed_count=3,estimated_queue=3.,lower_queue=2.,upper_queue=4.,observed_at_sim_s=1.,sim_time_s=2.,source='camera',missing=False);d.update(kw);return LaneObservation(**d)
 def test_camera(self):self.assertEqual(self.obs().validate().observed_count,3)
 def test_missing_null(self):self.obs(missing=True,observed_count=None,source='estimate').validate()
 def test_missing_zero(self):
  with self.assertRaises(ValueError):self.obs(missing=True,observed_count=0,source='estimate').validate()
 def test_bounds(self):
  with self.assertRaises(ValueError):self.obs(lower_queue=4).validate()
 def test_truth(self):
  with self.assertRaises(ValueError):self.obs(source='ground_truth').validate()
 def test_future(self):
  with self.assertRaises(ValueError):self.obs(observed_at_sim_s=3).validate()
 def test_camera_timestamp(self):
  with self.assertRaises(ValueError):self.obs(observed_at_sim_s=None).validate()
 def test_bool_count(self):
  with self.assertRaises(ValueError):self.obs(observed_count=True).validate()
class PhaseTests(unittest.TestCase):
 def req(self,**kw):
  d=dict(current_phase='NS',requested_phase='EW',elapsed_s=12,observation_age_s=1,state_revision=2,expected_revision=2);d.update(kw);return TransitionRequest(**d)
 def test_valid(self):self.assertTrue(check_request(self.req(),{'NS','EW'})[0])
 def test_min_green(self):self.assertEqual(check_request(self.req(elapsed_s=2),{'NS','EW'})[1],'minimum_green')
 def test_unknown(self):self.assertFalse(check_request(self.req(requested_phase='X'),{'NS','EW'})[0])
 def test_stale_revision(self):self.assertFalse(check_request(self.req(expected_revision=3),{'NS','EW'})[0])
 def test_stale_age(self):self.assertFalse(check_request(self.req(observation_age_s=10),{'NS','EW'})[0])
 def test_negative(self):self.assertFalse(check_request(self.req(elapsed_s=-1),{'NS','EW'})[0])
 def test_hold(self):self.assertEqual(check_request(self.req(requested_phase='NS',elapsed_s=1),{'NS','EW'})[1],'hold')
 def test_path(self):self.assertEqual(transition_sequence('NS','EW',{('NS','EW'):['YELLOW','ALL_RED','EW']}),['YELLOW','ALL_RED','EW'])
 def test_no_path(self):
  with self.assertRaises(ValueError):transition_sequence('NS','EW',{})
class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=Store();cls.http=ThreadingHTTPServer(('127.0.0.1',0),make_handler(cls.s,'test-token'))
  cls.t=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.t.start();cls.base='http://127.0.0.1:'+str(cls.http.server_port)
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.t.join()
 def req(self,path,body=None,token=None):
  hdr={'Content-Type':'application/json'}
  if token:hdr['Authorization']='Bearer '+token
  r=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=hdr)
  return urllib.request.urlopen(r,timeout=3)
 def test_health(self):self.assertEqual(json.load(self.req('/health'))['mode'],'MOCK')
 def test_no_fake_metrics(self):self.assertIsNone(json.load(self.req('/api/v1/snapshot'))['metrics'])
 def test_unauthorized(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.req('/api/v1/faults',{'junction_id':'J2','enabled':True})
  self.assertEqual(cm.exception.code,401)
 def test_missing(self):
  s=json.load(self.req('/api/v1/faults',{'junction_id':'J2','enabled':True},'test-token'))
  self.assertIsNone(s['junctions'][1]['observed_count']);self.assertGreater(s['junctions'][1]['estimated_queue'],0)
 def test_bad_junction(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.req('/api/v1/faults',{'junction_id':'X','enabled':True},'test-token')
  self.assertEqual(cm.exception.code,400)
 def test_reset(self):self.assertTrue(all(j['camera_status']=='AVAILABLE' for j in json.load(self.req('/api/v1/reset',{},'test-token'))['junctions']))
if __name__=='__main__':unittest.main()
