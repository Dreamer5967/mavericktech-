"""External artifact acceptance remains separate from configuration/unit tests."""
import os
from pathlib import Path
import unittest
from services.control.inference_entrypoint import AEGISInferenceEngine


class ExternalCheckpointTests(unittest.TestCase):
    def test_required_external_checkpoint_verification(self):
        path=Path(os.environ.get('AEGIS_P3_CHECKPOINT','checkpoints/mappo_cpu_best.pt'))
        if not path.is_file():
            if os.environ.get('AEGIS_REQUIRE_P3_CHECKPOINT')=='1':self.fail('Required compatible external checkpoint is missing.')
            self.skipTest('Compatible retrained checkpoint unavailable; no live policy sign-off.')
        engine=AEGISInferenceEngine(checkpoint_path=str(path),fail_closed=True,use_planner=False)
        self.assertTrue(engine.checkpoint_loaded)
