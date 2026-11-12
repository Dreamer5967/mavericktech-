"""
Inference Entrypoint for Person 2 (Live Coordinator)
===================================================
A clean, lightweight, inference-only module with zero training dependencies.
Called by P2's CARLA-SUMO synchronization bridge on each decision step.

Input:  Observation dictionary matching configs/observation_schema.json
Output: Validated action dictionary: { "J1": phase_idx, "J2": phase_idx, ... }
"""

import os
import json
import hashlib
import torch
import numpy as np
from typing import Dict, Any, Optional, List

from training.mappo.actor import ActorMLP
from services.control.phase_manager import SafetyPhaseManager, PhaseProposal
from services.planner.coordinator import RecoveryPlannerCoordinator


class AEGISInferenceEngine:
    """
    Production inference engine for live traffic signal control.
    Integrates Actor policy, Safety Phase Manager, and Recovery Planner.
    Fails closed if verified model checkpoint or configuration is missing.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        config_dir: Optional[str] = None,
        use_planner: bool = True,
        fail_closed: bool = True,
        device: str = "cpu",
        expected_checkpoint_sha256: Optional[str] = None,
    ):
        self.device = device
        self.use_planner = use_planner
        self.fail_closed = fail_closed

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cfg_dir = config_dir or os.path.join(base_dir, "configs")

        with open(os.path.join(cfg_dir, "observation_schema.json")) as f:
            self.obs_schema = json.load(f)
        with open(os.path.join(cfg_dir, "action_mapping.json")) as f:
            self.action_schema = json.load(f)

        # Resilient schema parsing: handles root or _metadata placement
        meta = self.obs_schema.get("_metadata", {})
        self.num_junctions = self.obs_schema.get("num_junctions", meta.get("num_junctions", 4))
        self.num_lanes = self.obs_schema.get("num_lanes_per_junction", meta.get("num_lanes_per_junction", 4))

        # Resilient junction parsing: handles list or dict
        junctions_raw = self.action_schema.get("junctions", [])
        if isinstance(junctions_raw, dict):
            self.junction_list = list(junctions_raw.values())
        else:
            self.junction_list = list(junctions_raw)

        if not self.junction_list:
            raise ValueError("[AEGIS Init Error] No junctions defined in action_mapping.json")

        self.max_phases = max(j.get("num_phases", len(j.get("phase_names", [4]))) for j in self.junction_list)

        # Calculate exact obs dimension
        self.obs_dim = (
            self.num_lanes * 3 + self.max_phases + 1 + self.num_junctions * 2
        )

        # Load Actor - Fail closed on missing/unverified checkpoint
        self.actor = ActorMLP(self.obs_dim, self.max_phases, hidden_dim=64).to(device)
        if checkpoint_path and os.path.isfile(checkpoint_path):
            if self.fail_closed or expected_checkpoint_sha256 is not None:
                expected = expected_checkpoint_sha256
                if expected is None:
                    manifest_file = os.path.join(base_dir, "manifests", "model_manifest.json")
                    with open(manifest_file) as manifest_stream:
                        expected = json.load(manifest_stream).get("checkpoint_sha256")
                if not isinstance(expected, str) or len(expected) != 64:
                    raise ValueError("Verified checkpoint SHA256 is required for live inference.")
                digest = hashlib.sha256()
                with open(checkpoint_path, "rb") as checkpoint_stream:
                    for chunk in iter(lambda: checkpoint_stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != expected:
                    raise ValueError("Checkpoint SHA256 mismatch; inference is blocked.")
            state = torch.load(checkpoint_path, map_location=device, weights_only=True)
            if "actor_state_dict" in state:
                self.actor.load_state_dict(state["actor_state_dict"])
            else:
                self.actor.load_state_dict(state)
            self.checkpoint_loaded = True
        else:
            if self.fail_closed:
                raise FileNotFoundError(
                    f"[AEGIS Security Fail-Closed] Live inference cannot run without a verified "
                    f"checkpoint artifact. Provided path: '{checkpoint_path}'. "
                    f"To bypass for debugging only, set fail_closed=False."
                )
            self.checkpoint_loaded = False

        self.actor.eval()

        # Build Phase Manager
        allowed_phases = {
            j["alias"]: set(j["phase_names"]) for j in self.junction_list
        }
        first_j = self.junction_list[0]
        self.phase_mgr = SafetyPhaseManager(
            allowed_phases=allowed_phases,
            min_green_s=first_j.get("min_green_s", 10.0),
            yellow_s=first_j.get("yellow_s", 3.0),
            all_red_s=first_j.get("all_red_s", 2.0),
            max_green_s=first_j.get("max_green_s", 60.0),
        )

        # Recovery Planner
        self.planner = RecoveryPlannerCoordinator(
            actor_model=self.actor,
            horizon_s=30,
            decision_dt=self.obs_schema.get("decision_interval_s", meta.get("decision_interval_s", 5))
        )

    def step(
        self,
        observations: Dict[str, np.ndarray],
        action_masks: Dict[str, np.ndarray],
        run_id: str,
        state_revision: int,
        sim_time_s: float
    ) -> Dict[str, Any]:
        """
        Produce a validated action proposal for each intersection.

        Returns:
            dict containing:
              - 'actions': dict mapping junction_id -> phase_index
              - 'planner_records': list of candidate evaluations (for UI)
              - 'active_signals': dict mapping junction_id -> signal string
        """
        executed_actions = {}
        planner_records = []

        if self.use_planner:
            plan = self.planner.plan(
                current_obs=observations,
                action_masks=action_masks,
                run_id=run_id,
                state_revision=state_revision,
                sim_time_s=sim_time_s
            )
            planner_records = plan.get("candidate_evaluations", [])

            for jid, obs in observations.items():
                mask = action_masks.get(jid, np.ones(self.max_phases, dtype=bool))
                action_idx = plan["first_action"]
                if not mask[action_idx]:
                    valid_indices = np.where(mask)[0]
                    action_idx = int(valid_indices[0]) if len(valid_indices) > 0 else 0
                executed_actions[jid] = action_idx
        else:
            for jid, obs in observations.items():
                mask = action_masks.get(jid, np.ones(self.max_phases, dtype=bool))
                act, _ = self.actor.get_action(obs, mask, deterministic=True)
                executed_actions[jid] = act

        # Advance phase manager safety timer
        dt = self.obs_schema.get("decision_interval_s", 5.0)
        active_signals = self.phase_mgr.tick(dt=dt)

        return {
            "actions": executed_actions,
            "planner_records": planner_records,
            "active_signals": active_signals,
            "state_revision": state_revision + 1,
            "sim_time_s": sim_time_s
        }
