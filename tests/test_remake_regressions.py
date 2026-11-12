import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import numpy as np
from services.control.inference_entrypoint import AEGISInferenceEngine
from p2.controller_gate import audit_controller, actor_vectors

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding='utf-8-sig'))


class InferenceRegressionTests(unittest.TestCase):
    def inputs(self):
        return ({f'J{i}':np.zeros(25,dtype=np.float32) for i in range(1,5)},
                {f'J{i}':np.zeros(4,dtype=bool) for i in range(1,5)})

    def test_all_false_masks_stop_actor_and_planner(self):
        for planner in (False,True):
            engine=AEGISInferenceEngine(use_planner=planner,fail_closed=False)
            engine.actor.get_action=Mock(side_effect=AssertionError('actor must not run'))
            if engine.planner:engine.planner.plan=Mock(side_effect=AssertionError('planner must not run'))
            with self.assertRaisesRegex(ValueError,'No valid action'):
                engine.step(*self.inputs(),'fixture',1,0)

    def test_forced_switch_is_only_a_proposal_and_never_executable(self):
        engine=AEGISInferenceEngine(use_planner=False,fail_closed=False)
        engine.actor.get_action=lambda *args,**kwargs:(1,0)
        obs,_=self.inputs();masks={j:np.ones(4,dtype=bool) for j in obs}
        result=engine.step(obs,masks,'fixture',1,0)
        self.assertEqual(set(result['proposed_sumo_phases'].values()),{3})
        self.assertEqual(result['actions'],{})
        self.assertEqual(result['active_signals'],{})
        self.assertFalse(result['actuation_permitted'])
        self.assertTrue(result['requires_transition_validation'])

    def test_unverified_artifact_rejected_before_load_even_in_diagnostic_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'unverified.pt';path.write_bytes(b'unverified')
            with patch('services.control.inference_entrypoint.torch.load') as load:
                with self.assertRaisesRegex(ValueError,'blocked'):
                    AEGISInferenceEngine(checkpoint_path=str(path),fail_closed=False)
                load.assert_not_called()

    def test_v2_gate_reports_blockers_without_schema_crash(self):
        result=audit_controller(read('configs/action_mapping.json'),read('configs/observation_schema.json'),
            read('manifests/model_manifest.json'),runtime_map=read('configs/runtime_mapping.json'))
        self.assertFalse(result['ready_for_live_policy'])
        self.assertIn('camera_domain_policy_validation_required',result['blockers'])
        self.assertNotIn('runtime_network_hash_mismatch',result['blockers'])
        self.assertFalse(any('inventory_mismatch' in b for b in result['blockers']))

    def test_physical_missing_lane_masks_aggregate_and_unused_slots_stay_missing(self):
        config=read('configs/action_mapping.json');schema=read('configs/observation_schema.json')
        packets={};beliefs={};context={}
        for j in config['junctions']:
            jid=j['alias'];ids=j['incoming_lane_ids']
            packets[jid]=[{'lane_id':lane,'observed_count':None if lane=='20_3' else 2,
                'missing':lane=='20_3','age_s':1} for lane in ids]
            beliefs[jid]={lane:6 for lane in ids}
            context[jid]={'green_action_index':0,'elapsed_green_s':10,'neighbor_inflow':[0]*4}
        result=actor_vectors(packets,beliefs,context,config,schema)
        self.assertTrue(all(len(v)==25 for v in result.values()))
        self.assertEqual(result['J3'][4],1)
        self.assertAlmostEqual(result['J3'][0],.4)
        self.assertEqual(result['J4'][2:4],[0,0])
        self.assertEqual(result['J4'][6:8],[1,1])


class TrainingAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traci=types.ModuleType('traci')
        cls.traci.TraCIException=RuntimeError;cls.traci.FatalTraCIError=RuntimeError
        cls.traci.trafficlight=types.SimpleNamespace(setPhase=Mock(),setPhaseDuration=Mock())
        cls.traci.lane=types.SimpleNamespace(getLastStepHaltingNumber=lambda lane:2)
        spec=importlib.util.spec_from_file_location('aegis_test_sumo_environment',ROOT/'training/sumo_env.py')
        cls.module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'traci':cls.traci,'sumolib':types.ModuleType('sumolib'),
                                    'gymnasium':types.ModuleType('gymnasium')}):
            spec.loader.exec_module(cls.module)

    def setUp(self):
        self.env=self.module.AEGISTrafficEnv('not-opened.net.xml','not-opened.rou.xml')
        self.traci.trafficlight.setPhase.reset_mock();self.traci.trafficlight.setPhaseDuration.reset_mock()

    def tearDown(self):self.env.close()

    def test_constructor_and_observations_accept_real_v2_schema(self):
        self.assertEqual(self.env.obs_dim,25)
        self.assertEqual([len(self.env._get_lane_ids_for_junction(i)) for i in range(4)],[6,6,8,4])
        self.assertEqual(self.env._get_observation(0).shape,(25,))
        self.assertEqual(self.env._get_observation(3)[6:8].tolist(),[1,1])

    def test_unreviewed_reset_does_not_launch_sumo(self):
        with patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(RuntimeError,'unreviewed'):self.env.reset()
            launch.assert_not_called()

    def test_policy_index_translates_to_actual_phase(self):
        self.env._set_sumo_phase(0,1)
        self.traci.trafficlight.setPhase.assert_called_once_with('719',3)
        with self.assertRaises(ValueError):self.env._set_sumo_phase(3,3)

    def test_reviewed_clearance_executes_yellow_red_then_target_with_fake_traci(self):
        cfg=self.env.junction_configs[0];cfg['transition_paths_reviewed']=True
        cfg['reviewed_transition_paths']={'0->3':[1,2,3]}
        self.env._phase_elapsed[0]=20
        self.env._apply_action(0,1)
        self.env._advance_transitions(3)
        self.env._advance_transitions(2)
        self.assertEqual([call.args for call in self.traci.trafficlight.setPhase.call_args_list],[('719',1),('719',2)])
        self.env._advance_transitions(1)  # Runtime program requires three seconds of all-red.
        calls=[call.args for call in self.traci.trafficlight.setPhase.call_args_list]
        self.assertEqual(calls,[('719',1),('719',2),('719',3)])
        self.assertFalse(self.env._in_transition[0])
        self.assertEqual(self.env._current_phases[0],1)


if __name__=='__main__':unittest.main()
