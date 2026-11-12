"""
Planner Timing Benchmark
========================
Measures the wall-clock execution time of the 3-branch recovery planner across
multiple decision steps. Ensures the planner satisfies real-time execution deadlines.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from training.mappo.actor import ActorMLP
from services.planner.coordinator import RecoveryPlannerCoordinator


def benchmark_planner_timing(num_trials: int = 50):
    print("=" * 60)
    print(f"BENCHMARKING RECOVERY PLANNER WALL-CLOCK TIMING ({num_trials} trials)")
    print("=" * 60)

    obs_dim = 25
    action_dim = 4
    torch.manual_seed(42)
    actor = ActorMLP(obs_dim, action_dim, hidden_dim=64)

    planner = RecoveryPlannerCoordinator(actor, horizon_s=30, decision_dt=5, deadline_ms=2000.0)

    rows = []
    for trial in range(1, num_trials + 1):
        rng = np.random.RandomState(trial)
        obs_dict = {f"J{j+1}": rng.uniform(0.1, 0.9, size=obs_dim).astype(np.float32) for j in range(4)}
        mask_dict = {f"J{j+1}": np.ones(action_dim, dtype=bool) for j in range(4)}

        t0 = time.perf_counter()
        plan = planner.plan(obs_dict, mask_dict, f"timing-trial-{trial}", trial, trial * 5.0)
        wall_ms = (time.perf_counter() - t0) * 1000.0

        rows.append({
            "trial": trial,
            "wall_clock_ms": round(wall_ms, 2),
            "selected_candidate": plan["selected_candidate"],
            "first_action": plan["first_action"],
            "deadline_exceeded": wall_ms > 2000.0
        })

    df = pd.DataFrame(rows)
    out_path = os.path.join(BASE_DIR, "results", "planner_timing.csv")
    df.to_csv(out_path, index=False)

    mean_ms = df["wall_clock_ms"].mean()
    p95_ms = df["wall_clock_ms"].quantile(0.95)
    max_ms = df["wall_clock_ms"].max()

    print(f"Mean Lookahead Time: {mean_ms:.2f} ms")
    print(f"95th Percentile Time: {p95_ms:.2f} ms")
    print(f"Max Lookahead Time: {max_ms:.2f} ms")
    print(f"Deadlines Exceeded: {df['deadline_exceeded'].sum()} / {num_trials}")
    print(f"Saved timing benchmarks to {out_path}")


if __name__ == '__main__':
    benchmark_planner_timing()
