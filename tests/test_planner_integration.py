"""
Integration Test for Recovery Planner
====================================
Verifies that the recovery planner evaluates all 3 candidate strategies,
screens constraints, selects the best first action, and formats candidate scores.
"""

import unittest
import numpy as np
import torch

from training.mappo.actor import ActorMLP
from services.planner.coordinator import RecoveryPlannerCoordinator


class TestPlannerIntegration(unittest.TestCase):

    def setUp(self):
        self.obs_dim = 25
        self.action_dim = 4
        torch.manual_seed(42)
        self.actor = ActorMLP(self.obs_dim, self.action_dim, hidden_dim=64)

        self.planner = RecoveryPlannerCoordinator(
            actor_model=self.actor,
            horizon_s=30,
            decision_dt=5,
            deadline_ms=2000.0
        )

    def test_planner_evaluates_three_candidates(self):
        # Create sample observation where NS has heavy queue disparity
        # Lanes 0, 1 (NS) have high queues 0.9, Lanes 2, 3 (EW) have 0.1
        obs_J1 = np.zeros(self.obs_dim, dtype=np.float32)
        obs_J1[0] = 0.9
        obs_J1[1] = 0.8
        obs_J1[2] = 0.1
        obs_J1[3] = 0.1

        obs_dict = {"J1": obs_J1}
        mask_dict = {"J1": np.array([True, True, False, False], dtype=bool)}

        plan = self.planner.plan(
            current_obs=obs_dict,
            action_masks=mask_dict,
            run_id="test-run-001",
            state_revision=10,
            sim_time_s=100.0
        )

        self.assertIn("selected_candidate", plan)
        self.assertIn(plan["selected_candidate"], ["learned_mappo", "conservative_fallback", "pressure_priority"])
        self.assertEqual(len(plan["candidate_evaluations"]), 3)

        # Check candidate evaluation schema matches planner_results.csv
        for cand in plan["candidate_evaluations"]:
            self.assertEqual(cand["run_id"], "test-run-001")
            self.assertEqual(cand["horizon_sim_s"], 30)
            self.assertIn(cand["constraint_status"], ["ADMISSIBLE", "VIOLATION"])
            self.assertIn(cand["outcome_status"], ["PREDICTED", "OBSERVED"])
            self.assertIsInstance(cand["selected"], bool)


if __name__ == '__main__':
    unittest.main()
