import copy
import hashlib
import unittest
from p2.runtime_mapping import build, corridor


class RuntimeMappingTests(unittest.TestCase):
    def fixture(self):
        xml = b'''<net><location netOffset="0,0"/>
        <edge id="10"><lane id="10_0" index="0" shape="0,0 50,0">
          <param key="origId" value="9_-1 10_-1"/></lane></edge>
        <edge id="out"><lane id="out_0" index="0" shape="50,0 60,0"/></edge>
        <connection from="10" fromLane="0" to="out" toLane="0" tl="719" linkIndex="0"/>
        <tlLogic id="719" programID="0"><phase duration="10" state="G"/>
          <phase duration="3" state="y"/><phase duration="2" state="r"/>
          <param key="linkSignalID:0" value="960"/></tlLogic></net>'''
        manifest = {'network_sha256': hashlib.sha256(xml).hexdigest(), 'xodr_sha256': 'fixture', 'map': 'fixture'}
        stop = {'x': 40, 'y': 0, 'z': 0, 'width_m': 3.5}
        geometry = {'map': 'fixture', 'live_xodr_sha256': 'fixture', 'cameras': [
            {'camera_id': 'cam_g1', 'lanes': [{'matched': True, 'road_id': 10,
              'lane_id': -1, 'samples': [stop]}]}]}
        cameras = {'map': 'fixture', 'image_width': 960, 'image_height': 540, 'fov': 90,
            'cameras': [{'camera_id': 'cam_g1', 'transform':
                {'x': 40, 'y': 0, 'z': 30, 'pitch': -90, 'yaw': 0, 'roll': 0}}]}
        policy = {'junctions': [{'alias': 'J1', 'camera_id': 'cam_g1', 'sumo_tls_id': '719', 'num_phases': 4}]}
        return xml, manifest, geometry, cameras, policy

    def test_orig_id_mapping_green_inventory_and_disabled_coverage(self):
        calibration, runtime = build(*self.fixture())
        lane = calibration['cameras'][0]['regions'][0]
        self.assertEqual(lane['lane_id'], '10_0')
        self.assertEqual(lane['upstream_region_m'], 25)
        self.assertTrue(lane['mapping_verified'])
        self.assertFalse(lane['usable_for_counts'])
        self.assertFalse(calibration['can_publish_lane_counts'])
        self.assertEqual([p['sumo_phase_index'] for p in runtime['junctions'][0]['green_phases']], [0])
        self.assertIsNone(runtime['junctions'][0]['policy_action_phase_mapping'])

    def test_wrong_network_hash_blocks_projection(self):
        args = list(self.fixture())
        args[1] = copy.deepcopy(args[1]); args[1]['network_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            build(*args)

    def test_stop_lane_far_from_centerline_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'more than 1m'):
            corridor([[0, 0], [50, 0]], {'x': 40, 'y': 5, 'z': 0}, 3.5)


if __name__ == '__main__':
    unittest.main()
