"""External artifact acceptance remains separate from configuration/unit tests."""
import os
import json
from pathlib import Path
import unittest
from services.control.inference_entrypoint import AEGISInferenceEngine


class ExternalCheckpointTests(unittest.TestCase):
    def test_required_external_checkpoint_verification(self):
        path=Path(os.environ.get('AEGIS_P3_CHECKPOINT','checkpoints/mappo_cpu_best.pt'))
        if not path.is_file():
            if os.environ.get('AEGIS_REQUIRE_P3_CHECKPOINT')=='1':self.fail('Required compatible external checkpoint is missing.')
            self.skipTest('Compatible retrained checkpoint unavailable; no live policy sign-off.')
        manifest=json.loads((Path(__file__).resolve().parents[1]/'manifests/model_manifest.json').read_text())
        engine=AEGISInferenceEngine(checkpoint_path=str(path),fail_closed=True,use_planner=False,
            expected_checkpoint_sha256=manifest['checkpoint_sha256'])
        self.assertTrue(engine.checkpoint_loaded)
