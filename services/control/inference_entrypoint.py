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
import torch
import numpy as np
from typing import Dict, Any, Optional

from training.mappo.actor import ActorMLP
from services.control.phase_manager import SafetyPhaseManager, PhaseProposal
from services.planner.coordinator import RecoveryPlannerCoordinator


class AEGISInferenceEngine:
    """
    Production inference engine for live traffic signal control.
    Integrates Actor policy, Safety Phase Manager, and Recovery Planner.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        config_dir: Optional[str] = None,
        use_planner: bool = True,
        device: str = "cpu"
    ):
        self.device = device
        self.use_planner = use_planner

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cfg_dir = config_dir or os.path.join(base_dir, "configs")

        with open(os.path.join(cfg_dir, "observation_schema.json")) as f:
            self.obs_schema = json.load(f)
        with open(os.path.join(cfg_dir, "action_mapping.json")) as f:
            self.action_schema = json.load(f)

        self.num_junctions = self.obs_schema["num_junctions"]
        self.num_lanes = self.obs_schema["num_lanes_per_junction"]
        self.max_phases = max(j["num_phases"] for j in self.action_schema["junctions"])

        # Calculate exact obs dimension
        self.obs_dim = (
            self.num_lanes * 3 + self.max_phases + 1 + self.num_junctions * 2
        )

        # Load Actor
        self.actor = ActorMLP(self.obs_dim, self.max_phases, hidden_dim=64).to(device)
        if checkpoint_path and os.path.exists(checkpoint_path):
            state = torch.load(checkpoint_path, map_location=device)
            if "actor_state_dict" in state:
                self.actor.load_state_dict(state["actor_state_dict"])
            else:
                self.actor.load_state_dict(state)
        self.actor.eval()

        # Build Phase Manager
        allowed_phases = {
            j["alias"]: set(j["phase_names"]) for j in self.action_schema["junctions"]
        }
        self.phase_mgr = SafetyPhaseManager(
            allowed_phases=allowed_phases,
            min_green_s=self.action_schema["junctions"][0].get("min_green_s", 10.0),
            yellow_s=self.action_schema["junctions"][0].get("yellow_s", 3.0),
            all_red_s=self.action_schema["junctions"][0].get("all_red_s", 2.0),
            max_green_s=self.action_schema["junctions"][0].get("max_green_s", 60.0),
        )

        # Recovery Planner
        self.planner = RecoveryPlannerCoordinator(
            actor_model=self.actor,
            horizon_s=30,
            decision_dt=self.obs_schema.get("decision_interval_s", 5)
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
            # Plan across all junctions
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
                # For demonstration, winning first action applies
                action_idx = plan["first_action"]
                if not mask[action_idx]:
                    valid_indices = np.where(mask)[0]
                    action_idx = int(valid_indices[0]) if len(valid_indices) > 0 else 0
                executed_actions[jid] = action_idx
        else:
            # Direct Actor inference without lookahead planner
            for jid, obs in observations.items():
                mask = action_masks.get(jid, np.ones(self.max_phases, dtype=bool))
                act, _ = self.actor.get_action(obs, mask, deterministic=True)
                executed_actions[jid] = act

        # Advance phase manager safety timer
        active_signals = self.phase_mgr.tick(dt=self.obs_schema.get("decision_interval_s", 5.0))

        return {
            "actions": executed_actions,
            "planner_records": planner_records,
            "active_signals": active_signals,
            "state_revision": state_revision + 1,
            "sim_time_s": sim_time_s
        }
