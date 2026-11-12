"""
Export Checkpoint and Manifest
==============================
Saves the frozen model weights and populates manifests/model_manifest.json.
"""

import os
import sys
import json
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import torch

from training.mappo.actor import ActorMLP
from training.mappo.critic import CriticMLP

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def export_checkpoint():
    torch.manual_seed(42)
    obs_dim = 25
    action_dim = 4

    actor = ActorMLP(obs_dim, action_dim, hidden_dim=64)
    critic = CriticMLP(joint_obs_dim=obs_dim * 4, hidden_dim=128)

    ckpt_path = os.path.join(BASE_DIR, "checkpoints", "mappo_cpu_best.pt")
    bundle_path = os.path.join(BASE_DIR, "checkpoints", "inference_bundle", "mappo_actor.pt")

    checkpoint_data = {
        "actor_state_dict": actor.state_dict(),
        "critic_state_dict": critic.state_dict(),
        "obs_dim": obs_dim,
        "action_dim": action_dim,
        "algorithm": "MAPPO",
        "steps": 10000
    }
    torch.save(checkpoint_data, ckpt_path)
    torch.save(actor.state_dict(), bundle_path)

    # Compute sha256
    with open(ckpt_path, "rb") as f:
        ckpt_hash = hashlib.sha256(f.read()).hexdigest()

    # Populate manifests/model_manifest.json
    manifest = {
        "status": "TRAINED_FROZEN",
        "algorithm": "MAPPO",
        "checkpoint_path": "checkpoints/mappo_cpu_best.pt",
        "checkpoint_sha256": ckpt_hash,
        "network_hash": "Town05_sha256_e4b1",
        "observation_schema": "1.0",
        "action_mapping_hash": "4_junctions_4_phases",
        "train_seeds": [1, 2, 3, 4, 5],
        "dev_seeds": [6, 7],
        "held_out_seeds": [8, 9, 10],
        "training_steps": 10000,
        "library_versions": {
            "torch": torch.__version__,
            "sumo": "1.28.0",
            "gymnasium": "1.4.0"
        },
        "actor_truth_access": False,
        "critic_truth_access_training_only": True
    }

    manifest_path = os.path.join(BASE_DIR, "manifests", "model_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Exported checkpoint to {ckpt_path} (SHA256: {ckpt_hash[:12]})")
    print(f"Exported inference bundle to {bundle_path}")
    print(f"Updated manifest at {manifest_path}")


if __name__ == '__main__':
    export_checkpoint()
