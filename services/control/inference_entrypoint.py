"""
Inference Entrypoint for Person 2 (Live Coordinator)
=====================================================
A clean, lightweight, inference-only module with zero training dependencies.
Called by P2's CARLA-SUMO synchronization bridge on each decision step.

Input:  Observation dictionary matching configs/observation_schema.json
Output: Validated action dictionary: { "J1": sumo_phase_idx, "J2": sumo_phase_idx, ... }

SAFETY CONTRACT (enforced, do not remove):
  - policy_action_index → sumo_phase_index translation is mandatory.
    Raw model output indices are NEVER used directly as SUMO phase indices.
  - Per-junction action masks permanently disable slots with no corresponding
    SUMO green phase (e.g. slot 3 for J1/J2, slots 2+3 for J4).
  - actuation_permitted must be True in action_mapping.json before any
    output from this engine may be applied to the live simulator.
"""

import os
import json
import torch
import numpy as np
from typing import Dict, Any, Optional, List

from training.mappo.actor import ActorMLP
from services.control.phase_manager import SafetyPhaseManager, PhaseProposal
from services.planner.coordinator import RecoveryPlannerCoordinator


def _build_permanent_mask(junction_cfg: dict, max_action_slots: int) -> np.ndarray:
    """
    Build a boolean action mask for a junction where permanently unused slots
    (no corresponding SUMO green phase) are always False.
    """
    mask = np.ones(max_action_slots, dtype=bool)
    for dead_slot in junction_cfg.get("action_mask_always_false", []):
        if 0 <= dead_slot < max_action_slots:
            mask[dead_slot] = False
    return mask


def _build_policy_to_sumo_map(junction_cfg: dict) -> Dict[int, Optional[int]]:
    """
    Returns mapping: policy_action_idx (int) -> sumo_phase_index (int or None).
    None means the slot has no corresponding SUMO phase and must be masked.
    """
    raw = junction_cfg.get("policy_action_phase_mapping", {})
    result = {}
    for k, v in raw.items():
        policy_idx = int(k)
        result[policy_idx] = v["sumo_phase_index"] if v is not None else None
    return result


class AEGISInferenceEngine:
    """
    Production inference engine for live traffic signal control.

    Integrates Actor policy, Safety Phase Manager, and Recovery Planner.
    Enforces the policy_action → sumo_phase_index translation contract.
    Fails closed if verified model checkpoint or configuration is missing.

    OUTPUT SEMANTICS:
      'actions' maps junction_alias -> sumo_phase_index (not policy index).
      P2 must apply the returned sumo_phase_index to traci.trafficlight.setPhase().
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        config_dir: Optional[str] = None,
        use_planner: bool = True,
        fail_closed: bool = True,
        device: str = "cpu"
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

        # Safety gate: refuse to run if actuation is blocked in config
        if self.action_schema.get("_actuation_permitted", False) is False and fail_closed:
            raise RuntimeError(
                "[AEGIS Safety Gate] action_mapping.json declares _actuation_permitted=false. "
                "Live policy actuation is blocked until P2/P3 jointly review and approve the "
                "lane_slot_aggregation and policy_action_phase_mapping for every junction. "
                "To run in read-only/diagnostic mode set fail_closed=False."
            )

        # Resilient schema parsing: handles root or _metadata placement
        meta = self.obs_schema.get("_metadata", {})
        self.num_junctions = self.obs_schema.get("num_junctions", meta.get("num_junctions", 4))
        self.num_lanes = self.obs_schema.get(
            "max_model_lane_slots",
            self.obs_schema.get("num_lanes_per_junction", meta.get("num_lanes_per_junction", 4))
        )

        # Resilient junction parsing: handles list or dict
        junctions_raw = self.action_schema.get("junctions", [])
        if isinstance(junctions_raw, dict):
            self.junction_list = list(junctions_raw.values())
        else:
            self.junction_list = list(junctions_raw)

        if not self.junction_list:
            raise ValueError("[AEGIS Init Error] No junctions defined in action_mapping.json")

        # Max model action slots (fixed at 4 for obs vector compatibility)
        self.max_phases = self.obs_schema.get(
            "max_model_action_slots",
            max(j.get("num_model_action_slots", 4) for j in self.junction_list)
        )

        # Build per-junction permanent masks and sumo phase translation tables
        self._permanent_masks: Dict[str, np.ndarray] = {}
        self._policy_to_sumo: Dict[str, Dict[int, Optional[int]]] = {}
        for j in self.junction_list:
            alias = j["alias"]
            self._permanent_masks[alias] = _build_permanent_mask(j, self.max_phases)
            self._policy_to_sumo[alias] = _build_policy_to_sumo_map(j)

        # Calculate exact obs dimension (must match trained model)
        self.obs_dim = (
            self.num_lanes * 3 + self.max_phases + 1 + self.num_junctions * 2
        )
        # = 4*3 + 4 + 1 + 4*2 = 25

        # Load Actor — fail closed on missing/unverified checkpoint
        self.actor = ActorMLP(self.obs_dim, self.max_phases, hidden_dim=64).to(device)
        if checkpoint_path and os.path.isfile(checkpoint_path):
            state = torch.load(checkpoint_path, map_location=device)
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
                    f"To bypass for read-only diagnostics only, set fail_closed=False."
                )
            self.checkpoint_loaded = False

        self.actor.eval()

        # Build Phase Manager using per-junction SUMO phase labels from mapping
        # Phase names are the sumo_phase_index values (as strings) since
        # generic NS/EW labels are no longer valid without P2 review.
        allowed_phases = {}
        for j in self.junction_list:
            alias = j["alias"]
            valid_sumo_indices = {
                str(v["sumo_phase_index"])
                for v in j.get("policy_action_phase_mapping", {}).values()
                if v is not None
            }
            allowed_phases[alias] = valid_sumo_indices if valid_sumo_indices else {"0"}

        first_j = self.junction_list[0]
        self.phase_mgr = SafetyPhaseManager(
            allowed_phases=allowed_phases,
            min_green_s=first_j.get("min_green_s", 7.0),
            yellow_s=first_j.get("yellow_s", 3.0),
            all_red_s=first_j.get("all_red_s", 2.0),
            max_green_s=first_j.get("max_green_s", 60.0),
        )

        # Recovery Planner
        decision_dt = self.obs_schema.get("decision_interval_s", meta.get("decision_interval_s", 5))
        self.planner = RecoveryPlannerCoordinator(
            actor_model=self.actor,
            horizon_s=30,
            decision_dt=decision_dt
        )

    def _apply_permanent_mask(self, jid: str, caller_mask: np.ndarray) -> np.ndarray:
        """Combine caller-supplied mask with permanent structural mask for this junction."""
        perm = self._permanent_masks.get(jid, np.ones(self.max_phases, dtype=bool))
        return np.logical_and(caller_mask, perm)

    def _policy_to_sumo_phase(self, jid: str, policy_idx: int) -> int:
        """
        Translate a policy action index to the corresponding SUMO phase index.
        Raises ValueError if the mapping is null (should have been masked).
        """
        mapping = self._policy_to_sumo.get(jid, {})
        sumo_idx = mapping.get(policy_idx)
        if sumo_idx is None:
            raise ValueError(
                f"[AEGIS Translation Error] Junction {jid}: policy action index {policy_idx} "
                f"has no SUMO phase mapping (slot is permanently masked). "
                f"This indicates an action mask failure upstream."
            )
        return sumo_idx

    def step(
        self,
        observations: Dict[str, np.ndarray],
        action_masks: Dict[str, np.ndarray],
        run_id: str,
        state_revision: int,
        sim_time_s: float
    ) -> Dict[str, Any]:
        """
        Produce a validated SUMO phase proposal for each intersection.

        Returns:
            dict containing:
              - 'actions': dict mapping junction_alias -> sumo_phase_index
                           (safe to pass directly to traci.trafficlight.setPhase)
              - 'policy_actions': dict mapping junction_alias -> policy_action_index
                                  (for logging and planner use only)
              - 'planner_records': list of candidate evaluations (for P4 UI)
              - 'active_signals': dict from safety phase manager
        """
        policy_actions: Dict[str, int] = {}
        executed_actions: Dict[str, int] = {}
        planner_records = []

        if self.use_planner:
            # Apply permanent masks before planner sees them
            masked_masks = {
                jid: self._apply_permanent_mask(jid, action_masks.get(jid, np.ones(self.max_phases, dtype=bool)))
                for jid in observations
            }
            plan = self.planner.plan(
                current_obs=observations,
                action_masks=masked_masks,
                run_id=run_id,
                state_revision=state_revision,
                sim_time_s=sim_time_s
            )
            planner_records = plan.get("candidate_evaluations", [])

            for jid in observations:
                mask = masked_masks[jid]
                policy_idx = plan["first_action"]
                if not mask[policy_idx]:
                    valid_indices = np.where(mask)[0]
                    policy_idx = int(valid_indices[0]) if len(valid_indices) > 0 else 0
                policy_actions[jid] = policy_idx
                executed_actions[jid] = self._policy_to_sumo_phase(jid, policy_idx)
        else:
            for jid, obs in observations.items():
                mask = self._apply_permanent_mask(
                    jid,
                    action_masks.get(jid, np.ones(self.max_phases, dtype=bool))
                )
                policy_idx, _ = self.actor.get_action(obs, mask, deterministic=True)
                policy_actions[jid] = policy_idx
                executed_actions[jid] = self._policy_to_sumo_phase(jid, policy_idx)

        # Advance phase manager safety timer
        dt = self.obs_schema.get("decision_interval_s", 5.0)
        active_signals = self.phase_mgr.tick(dt=dt)

        return {
            "actions": executed_actions,          # sumo_phase_index per junction
            "policy_actions": policy_actions,     # policy_action_index per junction (logging only)
            "planner_records": planner_records,
            "active_signals": active_signals,
            "state_revision": state_revision + 1,
            "sim_time_s": sim_time_s
        }
