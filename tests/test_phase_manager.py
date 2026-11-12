"""
Unit Tests for SafetyPhaseManager
=================================
Verifies minimum green, clearance sequence, freshness checks, and constraints.
"""

import unittest
from services.control.phase_manager import SafetyPhaseManager, PhaseProposal


class TestSafetyPhaseManager(unittest.TestCase):

    def setUp(self):
        self.allowed = {
            "J1": {"NS_GREEN", "EW_GREEN", "NS_LEFT", "EW_LEFT"},
            "J2": {"NS_GREEN", "EW_GREEN"},
        }
        self.mgr = SafetyPhaseManager(
            allowed_phases=self.allowed,
            min_green_s=10.0,
            yellow_s=3.0,
            all_red_s=2.0,
            max_green_s=60.0,
            max_observation_age_s=2.0
        )

    def test_valid_hold(self):
        prop = PhaseProposal(
            junction_id="J1",
            requested_phase="NS_GREEN",
            current_phase="NS_GREEN",
            elapsed_in_phase_s=5.0,
            observation_age_s=0.5,
            state_revision=1,
            expected_revision=1
        )
        ok, reason = self.mgr.validate_request(prop)
        self.assertTrue(ok)
        self.assertEqual(reason, "hold")

    def test_minimum_green_rejection(self):
        # Only 4 seconds elapsed in current phase (min_green=10)
        prop = PhaseProposal(
            junction_id="J1",
            requested_phase="EW_GREEN",
            current_phase="NS_GREEN",
            elapsed_in_phase_s=4.0,
            observation_age_s=0.5,
            state_revision=1,
            expected_revision=1
        )
        ok, reason = self.mgr.validate_request(prop)
        self.assertFalse(ok)
        self.assertEqual(reason, "minimum_green_violation")

    def test_stale_observation_rejection(self):
        # Observation is 3.5 seconds old (max allowed = 2.0s)
        prop = PhaseProposal(
            junction_id="J1",
            requested_phase="EW_GREEN",
            current_phase="NS_GREEN",
            elapsed_in_phase_s=15.0,
            observation_age_s=3.5,
            state_revision=1,
            expected_revision=1
        )
        ok, reason = self.mgr.validate_request(prop)
        self.assertFalse(ok)
        self.assertEqual(reason, "stale_observation")

    def test_stale_revision_rejection(self):
        # Revision mismatch
        prop = PhaseProposal(
            junction_id="J1",
            requested_phase="EW_GREEN",
            current_phase="NS_GREEN",
            elapsed_in_phase_s=15.0,
            observation_age_s=0.5,
            state_revision=1,
            expected_revision=2
        )
        ok, reason = self.mgr.validate_request(prop)
        self.assertFalse(ok)
        self.assertEqual(reason, "stale_revision")

    def test_clearance_sequencing(self):
        # Initiate valid transition from NS_GREEN to EW_GREEN
        seq = self.mgr.schedule_transition("J1", "EW_GREEN")
        self.assertEqual(seq, ["NS_GREEN_YELLOW", "ALL_RED", "EW_GREEN"])

        # At t=0, junction is in transition (YELLOW)
        signals = self.mgr.tick(1.0)
        self.assertEqual(signals["J1"], "YELLOW")

        # Advance through 3s yellow
        signals = self.mgr.tick(2.0)
        # Should now be in ALL_RED
        self.assertEqual(signals["J1"], "ALL_RED")

        # Advance through 2s all-red
        signals = self.mgr.tick(2.0)
        # Transition complete -> active signal is now EW_GREEN
        self.assertEqual(signals["J1"], "EW_GREEN")
        self.assertFalse(self.mgr.states["J1"].in_transition)


if __name__ == '__main__':
    unittest.main()
