import json
import threading
import unittest
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from p2.live_feed import FeedStore, make_handler, read_signal_states


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.store=FeedStore(['cam_g1'],'test-run',2,max_frames_per_camera=3)

    def row(self,frame=1):
        return {'frame_id':frame,'source_sim_time_s':10.0,
                'received_at_utc':'2026-11-12T00:00:00+00:00','error':None,
                'vehicle_count':3,'counts_by_class':{'car':3}}

    def test_expired_wall_time_masks_counts_without_retimestamp(self):
        self.store.publish([('cam_g1',self.row(),b'jpeg')],10.1)
        received=datetime.fromisoformat(self.row()['received_at_utc']).timestamp()
        result=self.store.snapshot(now=received+3)['cameras'][0]
        self.assertIsNone(result['observed_vehicle_count'])
        self.assertEqual(result['source_sim_time_s'],10)
        self.assertEqual(result['received_at_utc'],'2026-11-12T00:00:00+00:00')

    def test_cache_is_bounded_and_old_frame_expires(self):
        for frame in range(10):
            self.store.publish([('cam_g1',self.row(frame),b'jpeg')],10.1)
        self.assertEqual(len(self.store.frames),3)
        self.assertIsNone(self.store.frame('test-run_cam_g1_0'))
        self.assertEqual(self.store.frame('test-run_cam_g1_9'),b'jpeg')

    def test_failed_detector_never_becomes_zero(self):
        row=self.row()
        row['error']='inference failed'
        self.store.publish([('cam_g1',row,b'jpeg')],10.1)
        camera=self.store.snapshot()['cameras'][0]
        self.assertEqual(camera['status'],'detector_error')
        self.assertIsNone(camera['observed_vehicle_count'])

    def test_truth_fields_are_not_forwarded(self):
        row=self.row()
        row['true_vehicle_positions']=[[1,2]]
        self.store.publish([('cam_g1',row,b'jpeg')],10.1)
        self.assertNotIn('true_vehicle_positions',json.dumps(self.store.snapshot()))

    def test_missing_camera_has_null_count_and_no_frame(self):
        row=self.store.snapshot()['cameras'][0]
        self.assertTrue(row['missing'])
        self.assertIsNone(row['observed_vehicle_count'])
        self.assertIsNone(row['frame_url'])

    def test_signal_states_are_read_only_and_exposed_per_camera(self):
        class Light:
            attributes={}
            def get_opendrive_id(self): return '960'
            def get_state(self): return 'TrafficLightState.Green'
        class Actors(list):
            def filter(self, pattern):
                self.pattern=pattern
                return self
        class World:
            def get_actors(self): return Actors([Light()])
        states=read_signal_states(World(),[{'camera_id':'cam_g1','opendrive_signal_ids':['960','961']}])
        self.assertEqual(states,{'cam_g1':{'960':'GREEN','961':'UNAVAILABLE'}})
        self.store.publish_signal_states(states)
        self.assertEqual(self.store.snapshot()['cameras'][0]['traffic_lights']['960'],'GREEN')

    def test_http_frame_access_is_allowlisted_and_controls_refused(self):
        self.store.publish([('cam_g1',self.row(),b'jpeg')],10.1)
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.store))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/api/v1/frames/test-run_cam_g1_1',timeout=3) as response:
                self.assertEqual(response.read(),b'jpeg')
                self.assertEqual(response.headers['Content-Type'],'image/jpeg')
            for path in ('/api/v1/frames/../../key','/api/v1/frames/unknown'):
                with self.assertRaises(HTTPError) as result:
                    urlopen(base+path,timeout=3)
                self.assertEqual(result.exception.code,404)
                result.exception.close()
            with self.assertRaises(HTTPError) as result:
                urlopen(Request(base+'/api/v1/reset',data=b'{}'),timeout=3)
            self.assertEqual(result.exception.code,405)
            result.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__=='__main__':
    unittest.main()
