"""
P2 Integration Verification Suite — v2
========================================
Tests all integration blockers raised in the P2 geometry review:
  1. action_mapping.json: correct P2 TLS signal IDs, geometry-aligned structure
  2. observation_schema.json: dimensions accessible at root and _metadata
  3. model_manifest.json: correct network SHA256 (P2 verified), Town10HD_Opt, SUMO 1.20.0
  4. Inference engine: fail-closed on missing checkpoint
  5. Inference engine: actuation gate blocks init when _actuation_permitted=false
  6. Per-junction permanent action masks are correctly built from geometry config
  7. policy_to_sumo_phase translation is well-formed for all active slots
  8. Git tracking: zero .pt files in git index
"""

import json
import os
import subprocess
import sys
import unittest
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.control.inference_entrypoint import (
    AEGISInferenceEngine,
    _build_permanent_mask,
    _build_policy_to_sumo_map,
)

# P2-verified geometry (from configs/runtime_mapping.json on main branch)
P2_GEOMETRY = {
    "J1": {"sumo_tls_id": "719", "actual_lanes": 6, "green_phases": [0, 3, 6],  "masked_slots": [3]},
    "J2": {"sumo_tls_id": "23",  "actual_lanes": 6, "green_phases": [0, 3, 6],  "masked_slots": [3]},
    "J3": {"sumo_tls_id": "189", "actual_lanes": 8, "green_phases": [0, 3, 6, 9], "masked_slots": []},
    "J4": {"sumo_tls_id": "468", "actual_lanes": 4, "green_phases": [0, 3],     "masked_slots": [2, 3]},
}

P2_NETWORK_SHA256 = "3ef9501d4bb19f868f49395e39007876f834cbfe713f864a7ea8413f98115004"


class P2IntegrationVerificationTests(unittest.TestCase):

    def setUp(self):
        self.config_dir = os.path.join(BASE_DIR, "configs")
        with open(os.path.join(self.config_dir, "action_mapping.json")) as f:
            self.action_cfg = json.load(f)
        with open(os.path.join(self.config_dir, "observation_schema.json")) as f:
            self.obs_cfg = json.load(f)
        with open(os.path.join(BASE_DIR, "manifests", "model_manifest.json")) as f:
            self.manifest = json.load(f)

    # ------------------------------------------------------------------
    # B1: Signal IDs & geometry-aligned structure
    # ------------------------------------------------------------------
    def test_01_action_mapping_p2_signal_ids_and_geometry(self):
        """B1: action_mapping must have correct TLS IDs and geometry-aligned fields."""
        junctions = self.action_cfg["junctions"]
        self.assertIsInstance(junctions, list, "junctions must be a list")
        self.assertEqual(len(junctions), 4, "Must have exactly 4 junctions")

        expected_tls = {"cam_g1": "719", "cam_g3": "23", "cam_g4": "189", "cam_g5": "468"}
        for j in junctions:
            cam = j["camera_id"]
            self.assertIn(cam, expected_tls, f"Unexpected camera_id: {cam}")
            self.assertEqual(str(j["sumo_tls_id"]), expected_tls[cam])
            self.assertNotEqual(j["sumo_tls_id"], "TBD_FROM_P2_INVENTORY")
            # Geometry fields must be present
            self.assertIn("num_incoming_lanes", j, f"{j['alias']}: missing num_incoming_lanes")
            self.assertIn("num_green_phases", j, f"{j['alias']}: missing num_green_phases")
            self.assertIn("policy_action_phase_mapping", j, f"{j['alias']}: missing policy_action_phase_mapping")

        print("\n[PASS] 1. P2 signal mappings + geometry fields verified: cam_g1->719, cam_g3->23, cam_g4->189, cam_g5->468")

    # ------------------------------------------------------------------
    # B2: Observation schema dimensions at root and _metadata
    # ------------------------------------------------------------------
    def test_02_observation_schema_dimensions(self):
        """B2: Observation dimensions must be accessible at root and in _metadata."""
        self.assertEqual(self.obs_cfg["num_junctions"], 4)
        self.assertEqual(self.obs_cfg["max_model_lane_slots"], 4)
        self.assertEqual(self.obs_cfg["decision_interval_s"], 5)
        # _metadata must have backward-compat fields
        meta = self.obs_cfg["_metadata"]
        self.assertEqual(meta["num_junctions"], 4)
        self.assertEqual(meta["num_lanes_per_junction"], 4)
        # obs_dim documented
        self.assertEqual(self.obs_cfg.get("_obs_dim_per_junction"), 25)
        print("[PASS] 2. Observation schema dimensions verified at both root and _metadata (obs_dim=25)")

    # ------------------------------------------------------------------
    # B3: Manifest network hash = P2 actual hash
    # ------------------------------------------------------------------
    def test_03_model_manifest_p2_network_hash_and_town10(self):
        """B3: Manifest must declare the P2-verified network SHA256 for Town10HD_Opt."""
        self.assertEqual(self.manifest["map"], "Town10HD_Opt")
        self.assertEqual(self.manifest["library_versions"]["sumo_target"], "1.20.0")

        net_hash = self.manifest["network_sha256"]
        self.assertEqual(len(net_hash), 64, f"network_sha256 must be 64-char hex, got: {net_hash!r}")
        self.assertEqual(
            net_hash, P2_NETWORK_SHA256,
            f"network_sha256 must match P2-verified hash.\n"
            f"  Manifest:  {net_hash}\n"
            f"  P2 actual: {P2_NETWORK_SHA256}"
        )
        ckpt_sha = self.manifest.get("checkpoint_sha256", "")
        if self.manifest.get("status") == "TRAINED_SUMO_OFFLINE_CAMERA_UNVALIDATED":
            self.assertRegex(ckpt_sha, r"^[0-9a-f]{64}$",
                             "retrained external checkpoint must have a verified SHA256")
            self.assertEqual(self.manifest["data_mode"], "REAL_SUMO_ROI_SENSOR_MODEL_WITH_SYNTHETIC_DROPOUT")
            self.assertTrue(self.manifest.get("deployment_status", "").startswith("BLOCKED_"))
        else:
            self.assertIn("UNVERIFIED", ckpt_sha.upper(),
                          "checkpoint_sha256 must be marked UNVERIFIED until retrain + external verification")
            self.assertEqual(self.manifest["data_mode"], "SYNTHETIC_PRE_COSIM_EVALUATION")
        self.assertFalse(self.manifest.get("actuation_permitted", True),
                         "actuation_permitted must be False until P2/P3 joint review is complete")
        print(f"[PASS] 3. Manifest network SHA256 matches P2 actual: {net_hash[:16]}...")

    # ------------------------------------------------------------------
    # B4: Fail-closed on missing checkpoint
    # ------------------------------------------------------------------
    def test_04_inference_fails_closed_when_checkpoint_missing(self):
        """B4: Live inference must fail closed when checkpoint is missing."""
        with self.assertRaises((FileNotFoundError, RuntimeError)) as ctx:
            AEGISInferenceEngine(checkpoint_path="non_existent_model.pt", fail_closed=True)
        err_msg = str(ctx.exception)
        self.assertTrue(
            "[AEGIS Security Fail-Closed]" in err_msg or "[AEGIS Safety Gate]" in err_msg,
            f"Expected AEGIS fail-closed message, got: {err_msg}"
        )
        print("[PASS] 4. Inference engine safely fails closed on missing checkpoint / actuation gate")

    # ------------------------------------------------------------------
    # B5: Per-junction permanent action masks match P2 geometry
    # ------------------------------------------------------------------
    def test_05_permanent_action_masks_match_p2_geometry(self):
        """B5: Permanent action masks must permanently block slots with no SUMO green phase."""
        junctions = self.action_cfg["junctions"]
        for j in junctions:
            alias = j["alias"]
            expected_dead = set(P2_GEOMETRY[alias]["masked_slots"])
            mask = _build_permanent_mask(j, max_action_slots=4)
            for dead_slot in expected_dead:
                self.assertFalse(mask[dead_slot],
                    f"{alias}: slot {dead_slot} should be permanently masked (no SUMO green phase)")
            # Active slots should be True
            for slot in range(4):
                if slot not in expected_dead:
                    self.assertTrue(mask[slot],
                        f"{alias}: slot {slot} should be active (has SUMO green phase)")
        print("[PASS] 5. Per-junction permanent action masks match P2 geometry (J1:[3], J2:[3], J3:[], J4:[2,3])")

    # ------------------------------------------------------------------
    # B6: Policy-to-SUMO translation maps only to real phase indices
    # ------------------------------------------------------------------
    def test_06_policy_to_sumo_mapping_valid(self):
        """B6: policy_action_phase_mapping must translate to actual SUMO green phase indices."""
        junctions = self.action_cfg["junctions"]
        for j in junctions:
            alias = j["alias"]
            expected_sumo_phases = set(P2_GEOMETRY[alias]["green_phases"])
            mapping = _build_policy_to_sumo_map(j)
            for policy_idx, sumo_idx in mapping.items():
                if sumo_idx is None:
                    self.assertIn(policy_idx, P2_GEOMETRY[alias]["masked_slots"],
                        f"{alias}: null mapping at slot {policy_idx} but it's not in masked_slots")
                else:
                    self.assertIn(sumo_idx, expected_sumo_phases,
                        f"{alias}: sumo_phase_index {sumo_idx} not in P2 green phases {expected_sumo_phases}")
        print("[PASS] 6. All policy_action_phase_mapping values are valid P2 SUMO green phase indices")

    # ------------------------------------------------------------------
    # B7: Per-junction geometry counts match P2 actual
    # ------------------------------------------------------------------
    def test_07_per_junction_geometry_counts(self):
        """B7: num_incoming_lanes and num_green_phases must match P2 actual network."""
        junctions = self.action_cfg["junctions"]
        for j in junctions:
            alias = j["alias"]
            self.assertEqual(
                j["num_incoming_lanes"], P2_GEOMETRY[alias]["actual_lanes"],
                f"{alias}: num_incoming_lanes mismatch with P2 actual"
            )
            self.assertEqual(
                j["num_green_phases"], len(P2_GEOMETRY[alias]["green_phases"]),
                f"{alias}: num_green_phases mismatch with P2 actual"
            )
        print("[PASS] 7. Per-junction lane and phase counts match P2 actual: J1=6L/3P, J2=6L/3P, J3=8L/4P, J4=4L/2P")

    # ------------------------------------------------------------------
    # B8: No .pt weights tracked in git
    # ------------------------------------------------------------------
    def test_08_no_tracked_pt_weights_in_git(self):
        """B8: Checkpoint weights (*.pt) must NOT be tracked in the git index."""
        result = subprocess.run(
            ["git", "ls-files", "checkpoints/"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        tracked_pt = [l for l in result.stdout.strip().split("\n") if l.endswith(".pt")]
        self.assertEqual(tracked_pt, [],
            f"Found tracked .pt files in git index: {tracked_pt}")
        print("[PASS] 8. Git index verified: zero *.pt weight files tracked in git")


if __name__ == "__main__":
    unittest.main(verbosity=2)
