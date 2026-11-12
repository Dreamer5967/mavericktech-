"""
Planner Candidate Strategies Module
===================================
Defines the three competing recovery branches evaluated by the planner:

- Candidate A: Learned MAPPO policy
- Candidate B: Conservative fixed-time fallback
- Candidate C: Pressure / Priority heuristic (clears highest queue imbalance)
"""

from typing import Dict, List
import numpy as np


class CandidatePolicy:
    """Base interface for planner candidates."""
    name: str

    def select_action(self, jid: str, obs: np.ndarray, action_mask: np.ndarray) -> int:
        raise NotImplementedError


class CandidateA_Learned(CandidatePolicy):
    """Candidate A: Executes the trained MAPPO neural policy."""
    name = "learned_mappo"

    def __init__(self, actor_model):
        self.actor = actor_model

    def select_action(self, jid: str, obs: np.ndarray, action_mask: np.ndarray) -> int:
        action, _ = self.actor.get_action(obs, action_mask, deterministic=True)
        return action


class CandidateB_Conservative(CandidatePolicy):
    """Candidate B: Robust cyclic fallback with equal green allocation."""
    name = "conservative_fallback"

    def __init__(self, num_phases: int = 4, cycle_steps: int = 6):
        self.num_phases = num_phases
        self.cycle_steps = cycle_steps
        self.step = 0

    def select_action(self, jid: str, obs: np.ndarray, action_mask: np.ndarray) -> int:
        phase = (self.step // self.cycle_steps) % self.num_phases
        self.step += 1
        if action_mask[phase]:
            return phase
        # If masked, return first valid phase
        valid_indices = np.where(action_mask)[0]
        return int(valid_indices[0]) if len(valid_indices) > 0 else 0


class CandidateC_PressurePriority(CandidatePolicy):
    """
    Candidate C: Max-pressure / queue-disparity schedule.
    Directs green light toward the phase with the largest backlog.
    """
    name = "pressure_priority"

    def select_action(self, jid: str, obs: np.ndarray, action_mask: np.ndarray) -> int:
        # Lane queues are in obs[0:4]
        # Phase 0: NS_GREEN (serves lanes 0, 1)
        # Phase 1: EW_GREEN (serves lanes 2, 3)
        queues = obs[0:4]
        ns_pressure = queues[0] + queues[1] if len(queues) >= 2 else 0.0
        ew_pressure = queues[2] + queues[3] if len(queues) >= 4 else 0.0

        target_phase = 0 if ns_pressure >= ew_pressure else 1
        if target_phase < len(action_mask) and action_mask[target_phase]:
            return target_phase

        valid_indices = np.where(action_mask)[0]
        return int(valid_indices[0]) if len(valid_indices) > 0 else 0
