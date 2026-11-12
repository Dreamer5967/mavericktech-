"""
Checkpoint Evaluator
====================
Loads a frozen policy checkpoint and evaluates performance across specified seeds.
Outputs per-episode evaluation metrics.

Usage:
  python training/evaluate.py --checkpoint checkpoints/mappo_stage1_best.pt --seeds 8,9,10
"""

import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from training.mappo.actor import ActorMLP


def evaluate_checkpoint(checkpoint_path: str, seeds: list[int], fault_rate: float = 0.0):
    print("=" * 60)
    print(f"EVALUATING CHECKPOINT: {os.path.basename(checkpoint_path)}")
    print(f"Seeds: {seeds} | Fault Rate: {fault_rate}")
    print("=" * 60)

    obs_dim = 25
    action_dim = 4
    num_agents = 4

    actor = ActorMLP(obs_dim, action_dim, hidden_dim=64)
    state = torch.load(checkpoint_path, map_location="cpu")
    if "actor_state_dict" in state:
        actor.load_state_dict(state["actor_state_dict"])
    else:
        actor.load_state_dict(state)
    actor.eval()

    steps = 120
    dt = 5
    records = []

    for seed in seeds:
        rng = np.random.RandomState(seed)
        lane_queues = rng.uniform(2.0, 5.0, size=(num_agents, 4))
        current_phases = np.zeros(num_agents, dtype=int)
        phase_elapsed = np.zeros(num_agents, dtype=float)

        total_waiting_s = 0.0
        completed_trips = 0

        for step in range(steps):
            for i in range(num_agents):
                norm_q = np.clip(lane_queues[i] / 15.0, 0.0, 1.0)
                missing = (rng.random(4) < fault_rate).astype(np.float32) if fault_rate > 0 else np.zeros(4, dtype=np.float32)
                ages = np.zeros(4, dtype=np.float32)

                phase_onehot = np.zeros(action_dim, dtype=np.float32)
                phase_onehot[current_phases[i]] = 1.0

                elapsed = np.array([phase_elapsed[i] / 60.0], dtype=np.float32)
                inflow = np.full(num_agents, 0.2, dtype=np.float32)
                jid_onehot = np.zeros(num_agents, dtype=np.float32)
                jid_onehot[i] = 1.0

                obs = np.concatenate([norm_q, missing, ages, phase_onehot, elapsed, inflow, jid_onehot])
                mask = np.ones(action_dim, dtype=bool)

                if phase_elapsed[i] < 10.0:
                    mask[:] = False
                    mask[current_phases[i]] = True

                act, _ = actor.get_action(obs, mask, deterministic=True)

                if act != current_phases[i]:
                    current_phases[i] = act
                    phase_elapsed[i] = 0.0
                else:
                    phase_elapsed[i] += dt

                # Traffic dynamics
                arrivals = rng.poisson(1.2, size=4)
                lane_queues[i] += arrivals
                if current_phases[i] == 0:
                    lane_queues[i, 0:2] = np.maximum(0.0, lane_queues[i, 0:2] - 2.2)
                elif current_phases[i] == 1:
                    lane_queues[i, 2:4] = np.maximum(0.0, lane_queues[i, 2:4] - 2.2)

                q_sum = float(np.sum(lane_queues[i]))
                total_waiting_s += q_sum * dt
                completed_trips += int(np.sum(arrivals) * 0.85)

            mean_wait = total_waiting_s / max(1, completed_trips)

        records.append({
            "seed": seed,
            "fault_rate": fault_rate,
            "mean_waiting_s": round(mean_wait, 2),
            "completed_trips": completed_trips,
            "remaining_vehicles": int(np.sum(lane_queues))
        })
        print(f"Seed {seed:3d} -> Mean Waiting: {mean_wait:.2f}s | Completed Trips: {completed_trips}")

    df = pd.DataFrame(records)
    print("\nEVALUATION SUMMARY:")
    print(df.to_string(index=False))
    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="checkpoints/mappo_cpu_best.pt")
    parser.add_argument("--seeds", type=str, default="8,9,10")
    parser.add_argument("--fault-rate", type=float, default=0.0)
    args = parser.parse_args()

    seed_list = [int(s.strip()) for s in args.seeds.split(",")]
    evaluate_checkpoint(args.checkpoint, seed_list, args.fault_rate)
