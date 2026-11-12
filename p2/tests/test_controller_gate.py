import copy
import unittest
from p2.controller_gate import audit_controller, actor_vectors
from p2.lane_calibration import camera_coordinates, project_polygon


class ControllerGateTests(unittest.TestCase):
    def config(self):
        return {'junctions':[{'alias':'J1','camera_id':'cam_g1','sumo_tls_id':'719','num_phases':4,
                              'max_green_s':60,'lane_ids':['a','b','c','d']}]}

    def inputs(self):
        packets={'J1':[{'lane_id':lane,'observed_count':None if lane=='b' else 2,
                        'missing':lane=='b','age_s':3 if lane=='b' else 0.2} for lane in ('a','b','c','d')]}
        beliefs={'J1':{lane:6.0 for lane in ('a','b','c','d')}}
        phase={'J1':{'green_action_index':0,'elapsed_green_s':15,'neighbor_inflow':[0.0]}}
        return packets,beliefs,phase

    def test_missing_lane_uses_explicit_belief_and_mask_not_fake_zero(self):
        packets,beliefs,phase=self.inputs()
        vector=actor_vectors(packets,beliefs,phase,self.config(),{'num_lanes_per_junction':4})['J1']
        self.assertAlmostEqual(vector[1],0.4)
        self.assertEqual(vector[5],1.0)
        self.assertAlmostEqual(vector[9],0.1)

    def test_truth_fields_are_rejected(self):
        packets,beliefs,phase=self.inputs()
        packets['J1'][0]['true_vehicle_positions']=[]
        with self.assertRaises(ValueError):
            actor_vectors(packets,beliefs,phase,self.config(),{'num_lanes_per_junction':4})

    def test_image_count_cannot_substitute_for_lane_order(self):
        config=self.config();del config['junctions'][0]['lane_ids']
        with self.assertRaises(ValueError):
            actor_vectors(*self.inputs(),config,{'num_lanes_per_junction':4})

    def test_configuration_without_artifacts_and_reviews_is_blocked(self):
        audit=audit_controller(self.config(),{'num_lanes_per_junction':4},{})
        self.assertFalse(audit['ready_for_live_policy'])
        self.assertIn('verified_external_checkpoint_required',audit['blockers'])
        self.assertIn('J1:phase_mapping_review_required',audit['blockers'])


class ProjectionTests(unittest.TestCase):
    def test_forward_center_and_right_axis(self):
        t={'x':0,'y':0,'z':0,'pitch':0,'yaw':0,'roll':0}
        self.assertEqual(camera_coordinates((10,2,3),t),[10,2,3])

    def test_behind_camera_polygon_is_not_visible(self):
        t={'x':0,'y':0,'z':0,'pitch':0,'yaw':0,'roll':0}
        self.assertEqual(project_polygon([[-1,-1,-1],[-1,1,-1],[-1,1,1],[-1,-1,1]],t,960,540,90),[])

    def test_ground_rectangle_projects_inside_image(self):
        t={'x':0,'y':0,'z':10,'pitch':-90,'yaw':0,'roll':0}
        points=project_polygon([[-2,-2,0],[-2,2,0],[2,2,0],[2,-2,0]],t,960,540,90)
        self.assertEqual(len(points),4)
        self.assertTrue(all(0<=x<=959 and 0<=y<=539 for x,y in points))


if __name__=='__main__':
    unittest.main()
