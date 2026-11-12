"""
P2 Integration Verification Suite
==================================
Directly tests all 6 integration blockers raised in the P2 review:
  1. action_mapping.json layout & signal IDs (cam_g1->719, cam_g3->23, cam_g4->189, cam_g5->468)
  2. observation_schema.json root & metadata dimension accessibility
  3. model_manifest.json (Town10HD_Opt, SUMO 1.20.0, 64-char SHA256 network hash)
  4. AEGISInferenceEngine fail-closed security on missing checkpoint
  5. AEGISInferenceEngine successful live inference step with Town10HD_Opt P2 mapping
  6. Git tracking verification: zero .pt files in git index
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

from services.control.inference_entrypoint import AEGISInferenceEngine


class P2IntegrationVerificationTests(unittest.TestCase):

    def setUp(self):
        self.config_dir = os.path.join(BASE_DIR, "configs")
        with open(os.path.join(self.config_dir, "action_mapping.json")) as f:
            self.action_cfg = json.load(f)
        with open(os.path.join(self.config_dir, "observation_schema.json")) as f:
            self.obs_cfg = json.load(f)
        with open(os.path.join(BASE_DIR, "manifests", "model_manifest.json")) as f:
            self.manifest = json.load(f)

    def test_01_action_mapping_p2_signal_ids(self):
        """Blocker 1: Action mapping must contain real P2 signal IDs and list layout."""
        junctions = self.action_cfg["junctions"]
        self.assertIsInstance(junctions, list, "junctions must be a list of junction objects")
        self.assertEqual(len(junctions), 4, "Must have exactly 4 junctions")

        expected_mapping = {
            "cam_g1": "719",
            "cam_g3": "23",
            "cam_g4": "189",
            "cam_g5": "468"
        }
        for j in junctions:
            cam_id = j["camera_id"]
            self.assertIn(cam_id, expected_mapping, f"Unexpected camera {cam_id}")
            self.assertEqual(str(j["sumo_tls_id"]), expected_mapping[cam_id])
            self.assertNotEqual(j["sumo_tls_id"], "TBD_FROM_P2_INVENTORY")
        print("\n[PASS] 1. P2 signal mappings verified: cam_g1->719, cam_g3->23, cam_g4->189, cam_g5->468")

    def test_02_observation_schema_dimensions(self):
        """Blocker 2: Observation dimensions must be accessible at root and in _metadata."""
        # Check root access
        self.assertEqual(self.obs_cfg["num_junctions"], 4)
        self.assertEqual(self.obs_cfg["num_lanes_per_junction"], 4)
        self.assertEqual(self.obs_cfg["decision_interval_s"], 5)
        # Check metadata access
        self.assertEqual(self.obs_cfg["_metadata"]["num_junctions"], 4)
        self.assertEqual(self.obs_cfg["_metadata"]["num_lanes_per_junction"], 4)
        print("[PASS] 2. Observation schema dimensions verified at both root and _metadata")

    def test_03_model_manifest_town10_and_hash(self):
        """Blocker 3: Manifest must name Town10HD_Opt, SUMO 1.20.0, and 64-char SHA256."""
        self.assertEqual(self.manifest["map"], "Town10HD_Opt")
        self.assertEqual(self.manifest["library_versions"]["sumo_target"], "1.20.0")
        net_hash = self.manifest["network_hash"]
        self.assertEqual(len(net_hash), 64, f"Network hash must be 64-char SHA256 hex, got: {net_hash}")
        self.assertEqual(self.manifest["data_mode"], "SYNTHETIC_PRE_COSIM_EVALUATION")
        print(f"[PASS] 3. Manifest verified: Town10HD_Opt, SUMO 1.20.0, SHA256={net_hash[:16]}...")

    def test_04_inference_fails_closed_when_checkpoint_missing(self):
        """Blocker 5: Live inference must fail closed when checkpoint is missing."""
        with self.assertRaises(FileNotFoundError) as ctx:
            AEGISInferenceEngine(checkpoint_path="non_existent_model.pt", fail_closed=True)
        self.assertIn("[AEGIS Security Fail-Closed]", str(ctx.exception))
        print("[PASS] 4. Inference engine safely fails closed when checkpoint is missing")

    def test_05_inference_live_step_succeeds(self):
        """Blocker 1 & 5: Live inference initializes and steps with Town10HD_Opt mapping."""
        ckpt = os.environ.get("AEGIS_P3_CHECKPOINT", os.path.join(BASE_DIR, "checkpoints", "mappo_cpu_best.pt"))
        if not os.path.isfile(ckpt):
            if os.environ.get("AEGIS_REQUIRE_P3_CHECKPOINT") == "1":
                self.fail(f"Required external checkpoint missing at {ckpt}")
            self.skipTest("External checkpoint unavailable; this is not a live inference sign-off.")

        engine = AEGISInferenceEngine(checkpoint_path=ckpt, fail_closed=True)
        self.assertEqual(len(engine.junction_list), 4)

        # 4 junctions with 25-dim observation vector
        dummy_obs = {f"J{i+1}": np.zeros(25, dtype=np.float32) for i in range(4)}
        dummy_masks = {f"J{i+1}": np.ones(4, dtype=bool) for i in range(4)}

        out = engine.step(
            observations=dummy_obs,
            action_masks=dummy_masks,
            run_id="live-p2-test",
            state_revision=1,
            sim_time_s=5.0
        )
        self.assertIn("actions", out)
        self.assertEqual(len(out["actions"]), 4)
        for jid in ["J1", "J2", "J3", "J4"]:
            self.assertIn(jid, out["actions"])
            self.assertIn(out["actions"][jid], [0, 1, 2, 3])
        print(f"[PASS] 5. Live inference step succeeded: actions={out['actions']}")

    def test_06_no_tracked_pt_weights_in_git(self):
        """Blocker 6: Checkpoint weights (*.pt) must NOT be tracked in git index."""
        result = subprocess.run(
            ["git", "ls-files", "checkpoints/"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        tracked_files = [line for line in result.stdout.strip().split("\n") if line.endswith(".pt")]
        self.assertEqual(
            tracked_files,
            [],
            f"Found tracked .pt files in git: {tracked_files}"
        )
        print("[PASS] 6. Git index verified: zero *.pt weight files tracked in git")


if __name__ == "__main__":
    unittest.main(verbosity=2)
