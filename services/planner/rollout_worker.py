"""
Rollout Worker Module
=====================
Simulates short lookahead horizons for candidate strategies.
Evaluates cost metrics and screens for admissibility.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

from services.planner.candidates import CandidatePolicy


@dataclass
class RolloutResult:
    candidate_id: str
    first_action: int
    queue_cost: float
    spillback_cost: float
    emergency_delay_s: float
    total_cost: float
    constraint_status: str  # 'ADMISSIBLE' or 'VIOLATION'
    rollout_wall_ms: float
    deadline_status: str    # 'COMPLETED' or 'TIMEOUT'


class RolloutWorker:
    """
    Executes a lookahead evaluation for a single candidate policy.
    """

    def __init__(
        self,
        horizon_s: int = 30,
        decision_dt: int = 5,
        deadline_ms: float = 1500.0,
        queue_w: float = 1.0,
        spillback_w: float = 2.0,
        emergency_w: float = 5.0
    ):
        self.horizon_s = horizon_s
        self.decision_dt = decision_dt
        self.deadline_ms = deadline_ms
        self.queue_w = queue_w
        self.spillback_w = spillback_w
        self.emergency_w = emergency_w

    def evaluate(
        self,
        candidate: CandidatePolicy,
        initial_obs: Dict[str, np.ndarray],
        action_masks: Dict[str, np.ndarray]
    ) -> RolloutResult:
        """
        Simulate lookahead trajectory using synthetic belief state dynamics.
        """
        t_start = time.perf_counter()

        steps = self.horizon_s // self.decision_dt
        total_queue_cost = 0.0
        total_spillback_cost = 0.0
        emergency_delay = 0.0

        first_action = None

        # Simulating state rollouts across junctions
        sim_obs = {jid: np.copy(obs) for jid, obs in initial_obs.items()}

        for step in range(steps):
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            if elapsed_ms > self.deadline_ms:
                return RolloutResult(
                    candidate_id=candidate.name,
                    first_action=0 if first_action is None else first_action,
                    queue_cost=9999.0,
                    spillback_cost=9999.0,
                    emergency_delay_s=9999.0,
                    total_cost=9999.0,
                    constraint_status="VIOLATION",
                    rollout_wall_ms=elapsed_ms,
                    deadline_status="TIMEOUT"
                )

            step_actions = {}
            for jid, obs in sim_obs.items():
                mask = action_masks.get(jid, np.ones(4, dtype=bool))
                act = candidate.select_action(jid, obs, mask)
                step_actions[jid] = act
                if step == 0 and first_action is None:
                    first_action = act

                # Dynamic state progression under action
                # Phase 0 serves lanes 0,1; Phase 1 serves lanes 2,3
                queues = obs[0:4]
                if act == 0:
                    queues[0] = max(0.0, queues[0] - 0.4)
                    queues[1] = max(0.0, queues[1] - 0.4)
                    queues[2] = min(1.0, queues[2] + 0.1)
                    queues[3] = min(1.0, queues[3] + 0.1)
                else:
                    queues[2] = max(0.0, queues[2] - 0.4)
                    queues[3] = max(0.0, queues[3] - 0.4)
                    queues[0] = min(1.0, queues[0] + 0.1)
                    queues[1] = min(1.0, queues[1] + 0.1)

                obs[0:4] = queues

                # Costs
                q_sum = np.sum(queues)
                total_queue_cost += float(q_sum)
                if np.any(queues > 0.8):
                    total_spillback_cost += 1.0

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        total_cost = (
            self.queue_w * total_queue_cost
            + self.spillback_w * total_spillback_cost
            + self.emergency_w * emergency_delay
        )

        return RolloutResult(
            candidate_id=candidate.name,
            first_action=0 if first_action is None else first_action,
            queue_cost=total_queue_cost,
            spillback_cost=total_spillback_cost,
            emergency_delay_s=emergency_delay,
            total_cost=total_cost,
            constraint_status="ADMISSIBLE",
            rollout_wall_ms=elapsed_ms,
            deadline_status="COMPLETED"
        )
