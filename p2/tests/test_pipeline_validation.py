import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from p2.bridge_validation import check_lights, run as run_bridge
from p2.live_feed import check_clock_mode
from p2.validate_pipeline import run as run_pipeline


class PipelineValidationTests(unittest.TestCase):
    def test_clock_approval_is_required_before_cloud_import_or_connection(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'approval'):
                run_pipeline(SimpleNamespace())
            with self.assertRaisesRegex(RuntimeError, 'approval'):
                run_bridge(None, None, 30, None)

    def test_read_only_policy_arguments_must_be_a_verified_pair(self):
        with patch.dict(os.environ, {'AEGIS_APPROVE_LIVE_COSIM':'yes'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'both checkpoint path and SHA256'):
                run_bridge(None, None, 30, None, policy_checkpoint='external.pt')

    def test_learned_policy_execution_requires_a_verified_checkpoint(self):
        with patch.dict(os.environ, {'AEGIS_APPROVE_LIVE_COSIM':'yes','AEGIS_APPROVE_LEARNED_POLICY':'yes'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'requires a verified checkpoint'):
                run_bridge(None, None, 30, None, policy_execute=True)

    def test_observer_accepts_external_clock_without_calling_tick(self):
        class World:
            def get_settings(self):
                return SimpleNamespace(synchronous_mode=True)

        world = World()  # No tick API: this observer cannot own the clock.
        check_clock_mode(world, 'observer')
        with self.assertRaises(RuntimeError):
            check_clock_mode(world, 'standalone')

    def test_unknown_clock_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            check_clock_mode(None, 'new-owner')

    def test_signal_checks_report_missing_landmarks_and_state_mismatch(self):
        sync = SimpleNamespace(
            sumo=SimpleNamespace(traffic_light_ids={'960', '961'},
                                 get_traffic_light_state=lambda _: 'G'),
            carla=SimpleNamespace(traffic_light_ids={'960'},
                                  get_traffic_light_state=lambda _: 'Red'))
        helper = SimpleNamespace(get_carla_traffic_light_state=lambda _: 'Green')
        result = check_lights(sync, helper, {'960', '961'})
        self.assertEqual(result['missing_signal_ids'], ['961'])
        self.assertEqual(result['light_mismatches'], [
            {'opendrive_id': '960', 'expected': 'Green', 'actual': 'Red'}])

    def test_signal_checks_accept_matching_selected_landmarks(self):
        side = SimpleNamespace(traffic_light_ids={'960'},
                               get_traffic_light_state=lambda _: 'Green')
        sync = SimpleNamespace(sumo=side, carla=side)
        helper = SimpleNamespace(get_carla_traffic_light_state=lambda state: state)
        self.assertEqual(check_lights(sync, helper, {'960'}),
                         {'missing_signal_ids': [], 'light_mismatches': []})


if __name__ == '__main__':
    unittest.main()
