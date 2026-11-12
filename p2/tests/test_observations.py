import copy
import unittest
from p2.observations import build_snapshot, validate_snapshot
from p2.replay_compare import deduplicate, restore_box, tile_windows


class ObservationTests(unittest.TestCase):
    def source(self):
        return {'mode':'LIVE','run_id':'test-only-run','published_at_utc':'2026-11-12T06:36:09+00:00',
                'published_sim_time_s':6.0,'camera_config':{'stale_after_sim_s':2},
                'observations':[{'camera_id':'cam_test','frame_id':10,'source_sim_time_s':1.0,
                                 'missing':False,'status':'detected','whole_image_vehicle_count':0}]}

    def test_stale_zero_is_masked_and_source_timestamp_preserved(self):
        snapshot=build_snapshot(self.source())
        self.assertEqual(snapshot['mode'],'REPLAY')
        self.assertFalse(snapshot['ready_for_live_policy'])
        self.assertEqual(snapshot['cameras'][0]['observed_at_sim_s'],1)
        self.assertIsNone(snapshot['cameras'][0]['observed_vehicle_count'])

    def test_caller_cannot_hide_staleness_with_false_flag(self):
        source=self.source()
        source['observations'][0]['stale']=False
        self.assertTrue(build_snapshot(source)['cameras'][0]['stale'])

    def test_future_timestamp_does_not_become_fresh(self):
        source=self.source()
        source['observations'][0]['source_sim_time_s']=7
        row=build_snapshot(source)['cameras'][0]
        self.assertEqual(row['status'],'clock_unknown')
        self.assertIsNone(row['observed_vehicle_count'])

    def test_unknown_fields_rejected_at_policy_boundary(self):
        snapshot=build_snapshot(self.source())
        snapshot['cameras'][0]['true_vehicle_positions']=[[1,2]]
        with self.assertRaises(ValueError):
            validate_snapshot(snapshot)

    def test_root_control_fields_rejected(self):
        snapshot=build_snapshot(self.source())
        snapshot['proposals']=[]
        with self.assertRaises(ValueError):
            validate_snapshot(snapshot)

    def test_boundary_rejects_forged_freshness_and_integer_flags(self):
        for flag in (False,0):
            snapshot=build_snapshot(self.source())
            snapshot['cameras'][0]['stale']=flag
            with self.assertRaises(ValueError):
                validate_snapshot(snapshot)

    def test_nonfinite_time_rejected(self):
        source=self.source()
        source['observations'][0]['source_sim_time_s']=float('nan')
        with self.assertRaises(ValueError):
            build_snapshot(source)

    def test_original_measurements_are_not_mutated(self):
        source=self.source()
        before=copy.deepcopy(source)
        build_snapshot(source)
        self.assertEqual(source,before)


class ReplayGeometryTests(unittest.TestCase):
    def test_tile_edges_cover_full_frame(self):
        boxes=tile_windows(960,540)
        self.assertEqual(len(boxes),4)
        for x,y in [(0,0),(959,0),(0,539),(959,539),(480,270)]:
            self.assertTrue(any(x1<=x<x2 and y1<=y<y2 for x1,y1,x2,y2 in boxes))

    def test_rotated_coordinates_restore_to_original(self):
        self.assertEqual(restore_box([10,20,50,60],960,540,'rot180'),[910,480,950,520])
        self.assertEqual(restore_box([1,2,3,4],960,540,'tiles',(320,180)),[321,182,323,184])

    def test_overlap_is_not_double_counted_but_different_classes_survive(self):
        rows=[{'class_id':2,'confidence':0.8,'xyxy_pixels':[0,0,50,30]},
              {'class_id':2,'confidence':0.7,'xyxy_pixels':[1,1,51,31]},
              {'class_id':0,'confidence':0.9,'xyxy_pixels':[0,0,50,30]}]
        self.assertEqual(len(deduplicate(rows)),2)


if __name__=='__main__':
    unittest.main()
