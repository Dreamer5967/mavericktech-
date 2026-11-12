"""
AEGIS Phase Guard Matrix Verification Suite
===========================================
Executes the 12 Phase Guard Test Cases & Edge Cases specified by P1:
  TC-01: Standard Valid Transition
  TC-02: Hold Phase
  TC-03: Minimum Green Violation
  TC-04: Stale World Revision
  TC-05: Stale Observation Age
  TC-06: Unknown Phase Identifier
  TC-07: Negative Elapsed Time
  TC-08: Non-Finite Input (NaN / Inf)
  TC-09: Valid Clearance Sequence
  TC-10: Missing Transition Path
  TC-11: Camera Dropout Handling (LaneObservation)
  TC-12: Illegal Missing Zero (LaneObservation)
"""

import math
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aegis_helpers.contracts import LaneObservation
from aegis_helpers.phase_guard import (
    TransitionRequest,
    check_request,
    transition_sequence,
)


class PhaseGuardSpecificationTests(unittest.TestCase):
    """
    Direct implementation of TC-01 through TC-12 from the P1 specification.
    """

    def setUp(self):
        self.allowed_phases = {"NS", "EW"}
        self.approved_paths = {
            ("NS", "EW"): ["NS_YELLOW", "ALL_RED", "EW"],
            ("EW", "NS"): ["EW_YELLOW", "ALL_RED", "NS"],
        }

    # TC-01: Standard Valid Transition
    def test_tc01_standard_valid_transition(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=15.0,
            observation_age_s=0.5,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertTrue(approved, "TC-01 should be approved")
        self.assertEqual(reason, "queue_validated_transition")
        print("\n[PASS] TC-01: Standard Valid Transition -> (True, 'queue_validated_transition')")

    # TC-02: Hold Phase
    def test_tc02_hold_phase(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="NS",
            elapsed_s=4.0,
            observation_age_s=0.2,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertTrue(approved, "TC-02 should be approved")
        self.assertEqual(reason, "hold")
        print("[PASS] TC-02: Hold Phase -> (True, 'hold')")

    # TC-03: Minimum Green Violation
    def test_tc03_minimum_green_violation(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=2.0,  # < 10.0s min
            observation_age_s=0.5,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases, minimum_green_s=10.0)
        self.assertFalse(approved, "TC-03 should be rejected")
        self.assertEqual(reason, "minimum_green")
        print("[PASS] TC-03: Minimum Green Violation -> (False, 'minimum_green')")

    # TC-04: Stale World Revision
    def test_tc04_stale_world_revision(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=15.0,
            observation_age_s=0.5,
            state_revision=4,  # outdated
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertFalse(approved, "TC-04 should be rejected")
        self.assertEqual(reason, "stale_revision")
        print("[PASS] TC-04: Stale World Revision -> (False, 'stale_revision')")

    # TC-05: Stale Observation Age
    def test_tc05_stale_observation_age(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=15.0,
            observation_age_s=3.5,  # > 2.0s max
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases, max_age_s=2.0)
        self.assertFalse(approved, "TC-05 should be rejected")
        self.assertEqual(reason, "stale_state")
        print("[PASS] TC-05: Stale Observation Age -> (False, 'stale_state')")

    # TC-06: Unknown Phase Identifier
    def test_tc06_unknown_phase_identifier(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="XYZ_GREEN",  # invalid
            elapsed_s=15.0,
            observation_age_s=0.5,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertFalse(approved, "TC-06 should be rejected")
        self.assertEqual(reason, "unknown_phase")
        print("[PASS] TC-06: Unknown Phase Identifier -> (False, 'unknown_phase')")

    # TC-07: Negative Elapsed Time
    def test_tc07_negative_elapsed_time(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=-1.0,  # negative
            observation_age_s=0.5,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertFalse(approved, "TC-07 should be rejected")
        self.assertEqual(reason, "invalid_time")
        print("[PASS] TC-07: Negative Elapsed Time -> (False, 'invalid_time')")

    # TC-08: Non-Finite Input (NaN / Inf)
    def test_tc08_non_finite_input(self):
        req = TransitionRequest(
            current_phase="NS",
            requested_phase="EW",
            elapsed_s=math.nan,  # NaN
            observation_age_s=0.5,
            state_revision=5,
            expected_revision=5,
        )
        approved, reason = check_request(req, self.allowed_phases)
        self.assertFalse(approved, "TC-08 should be rejected")
        self.assertEqual(reason, "invalid_time")
        print("[PASS] TC-08: Non-Finite Input (NaN) -> (False, 'invalid_time')")

    # TC-09: Valid Clearance Sequence
    def test_tc09_valid_clearance_sequence(self):
        seq = transition_sequence("NS", "EW", self.approved_paths)
        expected = ["NS_YELLOW", "ALL_RED", "EW"]
        self.assertEqual(seq, expected)
        print(f"[PASS] TC-09: Valid Clearance Sequence -> {seq}")

    # TC-10: Missing Transition Path
    def test_tc10_missing_transition_path(self):
        with self.assertRaises(ValueError):
            transition_sequence("NS", "DIAGONAL", self.approved_paths)
        print("[PASS] TC-10: Missing Transition Path -> Raises ValueError as expected")

    # TC-11: Camera Dropout Handling
    def test_tc11_camera_dropout_handling(self):
        obs = LaneObservation(
            lane_id="lane_north_0",
            observed_count=None,
            estimated_queue=7.0,
            lower_queue=4.0,
            upper_queue=10.0,
            observed_at_sim_s=None,
            sim_time_s=120.0,
            source="estimate",
            missing=True,
        )
        validated = obs.validate()
        self.assertTrue(validated.missing)
        self.assertIsNone(validated.observed_count)
        self.assertEqual(validated.lower_queue, 4.0)
        self.assertEqual(validated.upper_queue, 10.0)
        print("[PASS] TC-11: Camera Dropout Handling -> Valid LaneObservation with bounds [4.0, 10.0]")

    # TC-12: Illegal Missing Zero
    def test_tc12_illegal_missing_zero(self):
        obs = LaneObservation(
            lane_id="lane_north_0",
            observed_count=0,  # illegal when missing is True
            estimated_queue=0.0,
            lower_queue=0.0,
            upper_queue=5.0,
            observed_at_sim_s=None,
            sim_time_s=120.0,
            source="estimate",
            missing=True,
        )
        with self.assertRaises(ValueError) as ctx:
            obs.validate()
        self.assertIn("Missing sensor must have null raw count", str(ctx.exception))
        print("[PASS] TC-12: Illegal Missing Zero -> Caught ValueError: 'Missing sensor must have null raw count'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
