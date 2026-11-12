"""
Unit Tests for MissingStateEstimator
===================================
Verifies queue conservation, uncertainty bounds, and reconciliation.
"""

import unittest
from services.control.estimator import MissingStateEstimator


class TestMissingStateEstimator(unittest.TestCase):

    def setUp(self):
        self.est = MissingStateEstimator(
            default_capacity=20.0,
            saturation_flow_rate_veh_s=0.5,
            nominal_arrival_rate_veh_s=0.2,
            uncertainty_growth_rate=0.1,
            reconciliation_alpha=0.5
        )
        self.lane = "J1_lane_0"
        self.est.register_lane(self.lane, capacity=20.0)

    def test_camera_available_tight_bounds(self):
        b = self.est.update_lane(self.lane, observed_count=5, sim_time_s=10.0, dt=5.0, is_green=False)
        self.assertEqual(b.estimated_queue, 5.0)
        self.assertFalse(b.missing)
        self.assertLessEqual(b.lower_queue, b.estimated_queue)
        self.assertLessEqual(b.estimated_queue, b.upper_queue)
        self.assertEqual(b.observation_age_s, 0.0)

    def test_camera_dropout_does_not_zero_queue(self):
        # Initial observation: 8 vehicles
        self.est.update_lane(self.lane, observed_count=8, sim_time_s=10.0, dt=5.0, is_green=False)

        # Camera fails for 3 consecutive steps (light is RED)
        for t in [15.0, 20.0, 25.0]:
            b = self.est.update_lane(self.lane, observed_count=None, sim_time_s=t, dt=5.0, is_green=False)

        # On RED, arrivals accumulate: queue must be > 8, definitely NOT 0
        self.assertTrue(b.missing)
        self.assertGreater(b.estimated_queue, 8.0)
        self.assertEqual(b.observation_age_s, 15.0)
        # Bounds must have expanded
        self.assertLess(b.lower_queue, b.estimated_queue)
        self.assertGreater(b.upper_queue, b.estimated_queue)

    def test_departures_only_on_green(self):
        # Initial queue 10 vehicles
        self.est.update_lane(self.lane, observed_count=10, sim_time_s=10.0, dt=5.0, is_green=False)

        # Camera down, but light is GREEN for 10 seconds: departures = 0.5 * 10 = 5 vehicles
        b = self.est.update_lane(self.lane, observed_count=None, sim_time_s=20.0, dt=10.0, is_green=True)
        # Net queue: 10 + (0.2*10 arrivals) - (0.5*10 departures) = 10 + 2 - 5 = 7
        self.assertAlmostEqual(b.estimated_queue, 7.0, places=2)

    def test_smooth_reconciliation(self):
        # Camera down, estimated queue drifts
        self.est.update_lane(self.lane, observed_count=5, sim_time_s=10.0, dt=5.0, is_green=False)
        self.est.update_lane(self.lane, observed_count=None, sim_time_s=15.0, dt=5.0, is_green=False)

        # Camera returns with true count = 10
        b = self.est.update_lane(self.lane, observed_count=10, sim_time_s=20.0, dt=5.0, is_green=False)
        self.assertFalse(b.missing)
        # With alpha=0.5, new estimate blends old estimate and 10 smoothly
        self.assertGreater(b.estimated_queue, 5.0)
        self.assertLessEqual(b.estimated_queue, 10.0)

    def test_bounds_invariant(self):
        for _ in range(10):
            b = self.est.update_lane(self.lane, observed_count=None, sim_time_s=50.0, dt=5.0, is_green=False)
            self.assertTrue(0.0 <= b.lower_queue <= b.estimated_queue <= b.upper_queue <= 20.0)


if __name__ == '__main__':
    unittest.main()
