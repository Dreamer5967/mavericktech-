"""
Recovery Planner Coordinator
============================
Coordinates the evaluation of candidate schedules:
1. Dispatches rollouts across Candidate A, B, and C
2. Screens candidates for constraint violations
3. Selects the minimum-cost admissible plan
4. Extracts only the first action for live coordinator execution
5. Exports structured records for the dashboard and evaluation CSV
"""

import hashlib
import time
from typing import Dict, List, Tuple
import numpy as np

from services.planner.candidates import CandidateA_Learned, CandidateB_Conservative, CandidateC_PressurePriority
from services.planner.rollout_worker import RolloutWorker, RolloutResult


class RecoveryPlannerCoordinator:
    """
    Online advisory lookahead planner.
    """

    def __init__(
        self,
        actor_model,
        horizon_s: int = 30,
        decision_dt: int = 5,
        deadline_ms: float = 2000.0
    ):
        self.actor = actor_model
        self.horizon_s = horizon_s
        self.decision_dt = decision_dt
        self.deadline_ms = deadline_ms

        self.candidates = [
            CandidateA_Learned(self.actor),
            CandidateB_Conservative(num_phases=4, cycle_steps=6),
            CandidateC_PressurePriority(),
        ]
        self.worker = RolloutWorker(horizon_s=horizon_s, decision_dt=decision_dt, deadline_ms=deadline_ms)

    def plan(
        self,
        current_obs: Dict[str, np.ndarray],
        action_masks: Dict[str, np.ndarray],
        run_id: str,
        state_revision: int,
        sim_time_s: float
    ) -> Dict:
        """
        Evaluate candidate schedules and select the optimal admissible action.

        Returns:
            dict containing winning proposal and full candidate evaluation records
        """
        # Hash current observation state for provenance tracking
        obs_bytes = b"".join(arr.tobytes() for arr in current_obs.values())
        belief_hash = hashlib.sha256(obs_bytes).hexdigest()[:12]

        results: List[RolloutResult] = []
        for candidate in self.candidates:
            res = self.worker.evaluate(candidate, current_obs, action_masks)
            results.append(res)

        # Screen admissible candidates
        admissible = [r for r in results if r.constraint_status == "ADMISSIBLE" and r.deadline_status == "COMPLETED"]
        if admissible:
            best_res = min(admissible, key=lambda r: r.total_cost)
        else:
            # Fallback to Conservative (Candidate B)
            best_res = next((r for r in results if r.candidate_id == "conservative_fallback"), results[0])

        proposal = {
            "proposal_id": f"prop-{state_revision}-{best_res.first_action}",
            "run_id": run_id,
            "based_on_revision": state_revision,
            "sim_time_s": sim_time_s,
            "expires_at_sim_s": sim_time_s + self.decision_dt,
            "selected_candidate": best_res.candidate_id,
            "first_action": best_res.first_action,
            "belief_hash": belief_hash,
            "candidate_evaluations": [
                {
                    "run_id": run_id,
                    "decision_id": f"dec-{state_revision}",
                    "belief_hash": belief_hash,
                    "candidate_id": r.candidate_id,
                    "horizon_sim_s": self.horizon_s,
                    "queue_cost": round(r.queue_cost, 3),
                    "spillback_cost": round(r.spillback_cost, 3),
                    "emergency_delay_s": round(r.emergency_delay_s, 3),
                    "constraint_status": r.constraint_status,
                    "rollout_ms": round(r.rollout_wall_ms, 2),
                    "selected": (r.candidate_id == best_res.candidate_id),
                    "outcome_status": "PREDICTED"
                }
                for r in results
            ]
        }
        return proposal
