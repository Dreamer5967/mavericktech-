import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch
from training.mappo.actor import ActorMLP
from services.control.inference_entrypoint import AEGISInferenceEngine


class CheckpointIntegrityTests(unittest.TestCase):
    def test_hash_mismatch_is_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory(prefix='aegis-checkpoint-test-') as directory:
            path=Path(directory)/'fixture.pt'
            path.write_bytes(b'not-a-real-checkpoint')
            with patch('services.control.inference_entrypoint.torch.load') as load:
                with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
                    AEGISInferenceEngine(checkpoint_path=str(path),expected_checkpoint_sha256='0'*64)
                load.assert_not_called()

    def test_verified_tensor_fixture_loads_and_proposes_without_simulator(self):
        # Random test-only tensors, not a trained policy or a performance claim.
        torch.manual_seed(12)
        actor=ActorMLP(25,4,hidden_dim=64)
        with tempfile.TemporaryDirectory(prefix='aegis-checkpoint-test-') as directory:
            path=Path(directory)/'fixture.pt'
            torch.save({'actor_state_dict':actor.state_dict()},path)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            engine=AEGISInferenceEngine(checkpoint_path=str(path),expected_checkpoint_sha256=digest,use_planner=False)
            result=engine.step({f'J{i}':np.zeros(25,dtype=np.float32) for i in range(1,5)},
                               {f'J{i}':np.ones(4,dtype=bool) for i in range(1,5)},'offline-fixture',1,5)
            self.assertTrue(engine.checkpoint_loaded)
            self.assertEqual(set(result['actions']),{'J1','J2','J3','J4'})


if __name__=='__main__':
    unittest.main()
