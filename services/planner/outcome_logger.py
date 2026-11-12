"""
Outcome Logger Module
=====================
Logs counterfactual planner predictions alongside actual observed outcomes
for decision auditing and provenance tracking.
"""

import os
import json
import csv
from typing import Dict, Any, Optional
import pandas as pd


class OutcomeLogger:
    """
    Tracks predicted lookahead scores and pairs them with observed outcomes.
    """

    def __init__(self, log_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.log_path = log_path or os.path.join(base_dir, "results", "planner_predictions_vs_outcomes.csv")
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}
        os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.log_path):
            fieldnames = [
                "decision_id", "run_id", "sim_time_s", "selected_candidate",
                "predicted_cost", "predicted_queue_delay", "observed_queue_delay",
                "prediction_error", "constraint_admissible"
            ]
            with open(self.log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    def log_prediction(
        self,
        decision_id: str,
        run_id: str,
        sim_time_s: float,
        selected_candidate: str,
        predicted_cost: float,
        predicted_queue_delay: float
    ):
        """Store prediction pending observation verification."""
        self.pending_decisions[decision_id] = {
            "decision_id": decision_id,
            "run_id": run_id,
            "sim_time_s": sim_time_s,
            "selected_candidate": selected_candidate,
            "predicted_cost": round(predicted_cost, 3),
            "predicted_queue_delay": round(predicted_queue_delay, 3)
        }

    def record_outcome(self, decision_id: str, observed_queue_delay: float):
        """Pair observed outcome with earlier prediction and append to disk."""
        if decision_id not in self.pending_decisions:
            return

        rec = self.pending_decisions.pop(decision_id)
        obs_delay = round(observed_queue_delay, 3)
        error = round(abs(rec["predicted_queue_delay"] - obs_delay), 3)

        row = {
            "decision_id": rec["decision_id"],
            "run_id": rec["run_id"],
            "sim_time_s": rec["sim_time_s"],
            "selected_candidate": rec["selected_candidate"],
            "predicted_cost": rec["predicted_cost"],
            "predicted_queue_delay": rec["predicted_queue_delay"],
            "observed_queue_delay": obs_delay,
            "prediction_error": error,
            "constraint_admissible": True
        }

        with open(self.log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writerow(row)
