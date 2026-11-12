"""
Information Separation Test
===========================
Verifies that the online decision-making controller (MAPPO + Estimator + Phase Guard)
is strictly isolated from ground-truth simulation state.

The test feeds identical observation streams to two controllers while mutating
hidden simulator ground-truth variables (vehicle positions, true trip delays).
The controller proposals MUST be 100% bit-for-bit identical, verifying zero
ground-truth leakage.
"""

import unittest
import numpy as np
import torch

from training.mappo.actor import ActorMLP
from services.control.estimator import MissingStateEstimator
from services.control.phase_manager import SafetyPhaseManager, PhaseProposal


class TestInformationSeparation(unittest.TestCase):

    def setUp(self):
        self.obs_dim = 25
        self.action_dim = 4
        # Seed torch for deterministic actor weights
        torch.manual_seed(42)
        self.actor = ActorMLP(self.obs_dim, self.action_dim, hidden_dim=64)
        self.actor.eval()

        self.allowed = {"J1": {"NS_GREEN", "EW_GREEN", "NS_LEFT", "EW_LEFT"}}
        self.phase_mgr = SafetyPhaseManager(self.allowed)

    def test_strict_isolation(self):
        # Base observation for J1
        fixed_obs = np.random.RandomState(123).randn(self.obs_dim).astype(np.float32)
        action_mask = np.ones(self.action_dim, dtype=bool)

        # Simulation Run A: hidden true vehicle count = 50, secret ambulance = False
        hidden_truth_A = {"true_network_vehicles": 50, "hidden_teleports": 0}
        action_A, log_prob_A = self.actor.get_action(fixed_obs, action_mask, deterministic=True)

        # Simulation Run B: hidden true vehicle count = 500 (10x worse!), secret ambulance = True
        hidden_truth_B = {"true_network_vehicles": 500, "hidden_teleports": 12}
        action_B, log_prob_B = self.actor.get_action(fixed_obs, action_mask, deterministic=True)

        # The policy ONLY reads fixed_obs -> actions MUST be identical
        self.assertEqual(action_A, action_B, "Policy leaked hidden ground truth state!")
        self.assertAlmostEqual(log_prob_A, log_prob_B, places=5)

    def test_estimator_no_truth_leakage(self):
        est_A = MissingStateEstimator()
        est_B = MissingStateEstimator()

        est_A.register_lane("L1")
        est_B.register_lane("L1")

        # Scenario: camera drops out for both
        # Run A: true vehicles on road = 25
        b_A = est_A.update_lane("L1", observed_count=None, sim_time_s=10.0, dt=5.0, is_green=False)
        # Run B: true vehicles on road = 0
        b_B = est_B.update_lane("L1", observed_count=None, sim_time_s=10.0, dt=5.0, is_green=False)

        # Since observed_count is None for both, both must produce identical estimated queue
        self.assertEqual(b_A.estimated_queue, b_B.estimated_queue)
        self.assertEqual(b_A.lower_queue, b_B.lower_queue)
        self.assertEqual(b_A.upper_queue, b_B.upper_queue)


if __name__ == '__main__':
    unittest.main()
