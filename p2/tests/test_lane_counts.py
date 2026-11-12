import copy
from datetime import datetime
import hashlib
import json
import unittest
from p2.lane_counts import measure, validate_regions
from p2.tiled_detector import restore_box, suppress_duplicates
from p2.live_feed import FeedStore


class LaneCountTests(unittest.TestCase):
    def camera(self):
        return {'camera_id':'cam_g1','regions':[
            {'lane_id':'a','polygon_pixels':[[0,0],[10,0],[10,20],[0,20]],
             'coverage_reviewed':True,'occlusion_reviewed':True,'detection_validated':True,'usable_for_counts':True},
            {'lane_id':'b','polygon_pixels':[[10,0],[20,0],[20,20],[10,20]],'usable_for_counts':False}]}

    def box(self,points):
        return {'class_name':'car','confidence':.8,'xyxy_pixels':points}

    def test_reviewed_region_counts_and_hidden_region_is_null(self):
        result=measure([self.box([2,2,6,8]),self.box([12,2,16,8])],self.camera(),['car'],enabled=True)
        self.assertEqual(result['lane_counts'],{'a':1,'b':None})
        self.assertIsNone(result['queue_estimate'])

    def test_boundary_ambiguity_does_not_double_count(self):
        result=measure([self.box([8,2,12,8])],self.camera(),['car'],enabled=True)
        self.assertEqual(result['lane_counts'],{'a':None,'b':None})
        self.assertEqual(result['ambiguous_lane_ids'],['a','b'])

    def test_unreviewed_empty_detection_is_not_published_as_zero(self):
        self.assertEqual(measure([],self.camera(),['car'])['lane_counts'],{'a':None,'b':None})

    def test_calibration_pose_hash_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'exact camera'):
            validate_regions({'camera_config_sha256':'bad','map':'test'},{'map':'test','cameras':[]})

    def test_review_without_detection_validation_is_rejected(self):
        config={'map':'test','cameras':[{'camera_id':'cam_g1'}]}
        camera=self.camera();camera['regions'][0]['detection_validated']=False
        cal={'map':'test','camera_config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),'cameras':[camera]}
        with self.assertRaises(ValueError):validate_regions(cal,config)

    def test_stale_lane_counts_are_masked_without_retimestamping(self):
        store=FeedStore(['cam_g1'],'test',lane_templates={'cam_g1':['a','b']})
        row={'frame_id':1,'source_sim_time_s':10,'received_at_utc':'2026-11-12T00:00:00+00:00',
             'error':None,'lane_counts':{'a':1,'b':None}}
        store.publish([('cam_g1',row,b'jpeg')],10.1)
        received=datetime.fromisoformat(row['received_at_utc']).timestamp()
        result=store.snapshot(now=received+3)['cameras'][0]
        self.assertEqual(result['lane_counts'],{'a':None,'b':None})
        self.assertEqual(result['source_sim_time_s'],10)


class TileGeometryTests(unittest.TestCase):
    def test_rotation_inverses(self):
        self.assertEqual(restore_box([10,20,30,40],0,0,1,100,100),[60,10,80,30])
        self.assertEqual(restore_box([10,20,30,40],0,0,2,100,100),[70,60,90,80])
        self.assertEqual(restore_box([10,20,30,40],0,0,3,100,100),[20,70,40,90])

    def test_nested_rotation_duplicates_suppressed_but_adjacent_cars_remain(self):
        boxes=[{'confidence':.9,'xyxy_pixels':[0,0,100,100]},
               {'confidence':.3,'xyxy_pixels':[0,50,30,100]},
               {'confidence':.8,'xyxy_pixels':[110,0,200,100]}]
        self.assertEqual(len(suppress_duplicates(boxes)),2)


if __name__=='__main__':unittest.main()
