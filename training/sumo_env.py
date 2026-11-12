"""
AEGIS Multi-Agent SUMO Traffic Environment
==========================================
Gymnasium-compatible multi-agent environment wrapping 4 junctions from
a SUMO network via TraCI. Each junction is treated as an independent agent
with its own observation and action space.

This environment is the core training/evaluation interface for Person 3.
It does NOT access CARLA — all simulation runs in headless SUMO.

Observation contract follows: configs/observation_schema.json
Action contract follows:     configs/action_mapping.json
"""

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import gymnasium as gym
import numpy as np

try:
    import traci
    import sumolib
except ImportError:
    raise ImportError(
        "Install SUMO Python tools: pip install traci sumolib eclipse-sumo"
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AEGISTrafficEnv:
    """
    Multi-agent SUMO traffic environment for MAPPO training.

    Each of the 4 junctions is an agent with:
      - Observation: lane queues, missing masks, observation ages,
                     current phase one-hot, elapsed phase time,
                     neighbor inflow, junction identity
      - Action:      discrete green-phase index (masked by availability)
      - Reward:      shared team reward based on network-level metrics

    The environment enforces phase transitions through the safety guard
    (min-green, yellow, clearance) internally during training.
    """

    def __init__(
        self,
        net_file: str,
        route_file: str,
        config_dir: Optional[str] = None,
        decision_interval: int = 5,
        episode_length: int = 600,
        warmup_steps: int = 100,
        gui: bool = False,
        port: Optional[int] = None,
        fault_rate: float = 0.0,
        fault_seed: Optional[int] = None,
        label: str = "aegis",
    ):
        """
        Args:
            net_file:          Path to SUMO .net.xml network file
            route_file:        Path to SUMO .rou.xml route/demand file
            config_dir:        Path to configs/ directory (auto-detected if None)
            decision_interval: Seconds between agent decisions
            episode_length:    Total episode length in sim seconds
            warmup_steps:      Sim seconds of warmup before agents act
            gui:               If True, launch sumo-gui instead of sumo
            port:              TraCI port (auto-assigned if None)
            fault_rate:        Probability of dropping each camera observation [0, 1]
            fault_seed:        RNG seed for fault injection (None = use episode seed)
            label:             TraCI connection label
        """
        self.net_file = net_file
        self.route_file = route_file
        self.decision_interval = decision_interval
        self.episode_length = episode_length
        self.warmup_steps = warmup_steps
        self.gui = gui
        self.port = port
        self.fault_rate = fault_rate
        self.fault_seed = fault_seed
        self.label = label

        # Load configs
        cfg_dir = Path(config_dir) if config_dir else PROJECT_ROOT / "configs"
        with open(cfg_dir / "action_mapping.json") as f:
            self.action_config = json.load(f)
        with open(cfg_dir / "observation_schema.json") as f:
            self.obs_config = json.load(f)
        with open(cfg_dir / "reward_config.json") as f:
            self.reward_config = json.load(f)

        # Junction setup
        self.num_junctions = self.obs_config["num_junctions"]
        self.num_lanes = self.obs_config["num_lanes_per_junction"]
        self.junction_ids = [j["alias"] for j in self.action_config["junctions"]]
        self.tls_ids = [j["sumo_tls_id"] for j in self.action_config["junctions"]]
        self.num_phases = [j["num_phases"] for j in self.action_config["junctions"]]
        self.max_phases = max(self.num_phases)
        self.phase_names = [j["phase_names"] for j in self.action_config["junctions"]]

        # Phase transition parameters
        self.min_green_s = self.action_config["junctions"][0].get("min_green_s", 10)
        self.yellow_s = self.action_config["junctions"][0].get("yellow_s", 3)
        self.all_red_s = self.action_config["junctions"][0].get("all_red_s", 2)
        self.max_green_s = self.action_config["junctions"][0].get("max_green_s", 60)

        # Observation dimensions
        self.obs_dim = (
            self.num_lanes        # normalized lane queues
            + self.num_lanes      # missing masks
            + self.num_lanes      # observation ages
            + self.max_phases     # current phase one-hot
            + 1                   # elapsed phase time (normalized)
            + self.num_junctions  # neighbor inflow
            + self.num_junctions  # junction identity one-hot
        )

        # Reward weights
        self.w_queue = self.reward_config.get("queue_weight", 1.0)
        self.w_spillback = self.reward_config.get("spillback_weight", 0.5)
        self.w_switch = self.reward_config.get("switch_weight", 0.1)

        # Internal state
        self._conn = None
        self._sumo_process = None
        self._step_count = 0
        self._sim_time = 0.0
        self._current_phases = [0] * self.num_junctions
        self._phase_elapsed = [0.0] * self.num_junctions
        self._in_transition = [False] * self.num_junctions
        self._transition_remaining = [0.0] * self.num_junctions
        self._pending_phase = [0] * self.num_junctions
        self._last_observations = {}
        self._fault_rng = None
        self._lane_capacity = 15.0  # estimated max queue per lane

        # Per-lane tracking for the estimator
        self._lane_queues = np.zeros((self.num_junctions, self.num_lanes))
        self._missing_masks = np.zeros((self.num_junctions, self.num_lanes), dtype=bool)
        self._obs_ages = np.zeros((self.num_junctions, self.num_lanes))

    # ──────────────────────── Observation Space ────────────────────────

    def _get_lane_ids_for_junction(self, junction_idx: int) -> list[str]:
        """Get controlled incoming lane IDs for a junction from SUMO."""
        tls_id = self.tls_ids[junction_idx]
        try:
            links = traci.trafficlight.getControlledLinks(tls_id)
            incoming_lanes = []
            seen = set()
            for link_group in links:
                for link in link_group:
                    lane = link[0]  # incoming lane
                    if lane not in seen:
                        incoming_lanes.append(lane)
                        seen.add(lane)
            return incoming_lanes[: self.num_lanes]
        except traci.TraCIException:
            # Fallback: generate placeholder lane IDs
            return [f"{tls_id}_lane_{i}" for i in range(self.num_lanes)]

    def _get_queue_for_lane(self, lane_id: str) -> float:
        """Get the number of halting vehicles on a lane."""
        try:
            return float(traci.lane.getLastStepHaltingNumber(lane_id))
        except traci.TraCIException:
            return 0.0

    def _get_observation(self, junction_idx: int) -> np.ndarray:
        """
        Build the observation vector for a single junction.
        Applies fault injection (camera dropout) if configured.
        """
        lane_ids = self._get_lane_ids_for_junction(junction_idx)

        # Raw queue observations
        raw_queues = np.array(
            [self._get_queue_for_lane(lid) for lid in lane_ids], dtype=np.float32
        )

        # Fault injection: randomly drop camera observations
        missing = np.zeros(self.num_lanes, dtype=bool)
        if self.fault_rate > 0 and self._fault_rng is not None:
            for i in range(len(lane_ids)):
                if self._fault_rng.random() < self.fault_rate:
                    missing[i] = True

        # Apply missing mask
        observed_queues = np.copy(raw_queues)
        obs_ages = np.zeros(self.num_lanes, dtype=np.float32)
        for i in range(self.num_lanes):
            if missing[i]:
                # Camera is down: use last known estimate
                observed_queues[i] = self._lane_queues[junction_idx, i]
                obs_ages[i] = self._obs_ages[junction_idx, i] + self.decision_interval
            else:
                # Camera is available: update estimate
                obs_ages[i] = 0.0

        # Update internal tracking
        self._lane_queues[junction_idx] = observed_queues
        self._missing_masks[junction_idx] = missing
        self._obs_ages[junction_idx] = obs_ages

        # Normalize queues to [0, 1]
        norm_queues = np.clip(observed_queues / self._lane_capacity, 0.0, 1.0)

        # Current phase one-hot
        phase_onehot = np.zeros(self.max_phases, dtype=np.float32)
        phase_onehot[self._current_phases[junction_idx]] = 1.0

        # Elapsed phase time (normalized to max_green)
        norm_elapsed = np.array(
            [self._phase_elapsed[junction_idx] / self.max_green_s], dtype=np.float32
        )

        # Neighbor inflow estimate (simplified: sum of departures from neighbors)
        neighbor_inflow = np.zeros(self.num_junctions, dtype=np.float32)
        for j in range(self.num_junctions):
            if j != junction_idx:
                neighbor_inflow[j] = np.mean(self._lane_queues[j]) / self._lane_capacity

        # Junction identity one-hot
        junction_onehot = np.zeros(self.num_junctions, dtype=np.float32)
        junction_onehot[junction_idx] = 1.0

        obs = np.concatenate([
            norm_queues,
            missing.astype(np.float32),
            obs_ages / 30.0,  # normalize ages (30s is quite stale)
            phase_onehot,
            norm_elapsed,
            neighbor_inflow,
            junction_onehot,
        ])
        return obs

    def _get_action_mask(self, junction_idx: int) -> np.ndarray:
        """
        Returns a boolean mask of valid actions for this junction.
        If in transition or min-green not met, only 'hold' (current phase) is valid.
        """
        mask = np.zeros(self.max_phases, dtype=bool)
        n_phases = self.num_phases[junction_idx]

        if self._in_transition[junction_idx]:
            # During yellow/clearance, only current pending target is valid
            mask[self._pending_phase[junction_idx]] = True
        elif self._phase_elapsed[junction_idx] < self.min_green_s:
            # Min green not met: can only hold current phase
            mask[self._current_phases[junction_idx]] = True
        else:
            # All phases available
            mask[:n_phases] = True

        return mask

    # ──────────────────────── Reward ────────────────────────

    def _compute_reward(self) -> float:
        """
        Compute shared team reward based on network-level metrics.
        R = -(w1 * norm_queue + w2 * spillback + w3 * switches)
        """
        # Total normalized queue across all junctions
        total_queue = 0.0
        spillback_count = 0
        for j in range(self.num_junctions):
            for i in range(self.num_lanes):
                q = self._lane_queues[j, i] / self._lane_capacity
                total_queue += q
                if q > 0.8:
                    spillback_count += 1

        norm_queue = total_queue / (self.num_junctions * self.num_lanes)
        norm_spillback = spillback_count / (self.num_junctions * self.num_lanes)

        # Phase switch penalty (counted in step())
        # Set externally before calling this
        norm_switches = self._switches_this_step / self.num_junctions

        reward = -(
            self.w_queue * norm_queue
            + self.w_spillback * norm_spillback
            + self.w_switch * norm_switches
        )
        return reward

    # ──────────────────────── Phase Transitions ────────────────────────

    def _apply_action(self, junction_idx: int, action: int):
        """
        Apply a green-phase action to a junction, enforcing safety transitions.
        """
        current = self._current_phases[junction_idx]

        if self._in_transition[junction_idx]:
            # Still in yellow/clearance — ignore new actions
            return

        if action == current:
            # Hold current phase — just increment elapsed time
            return

        if self._phase_elapsed[junction_idx] < self.min_green_s:
            # Min green not met — reject and hold
            return

        # Start transition: current → yellow → all_red → target
        self._in_transition[junction_idx] = True
        self._pending_phase[junction_idx] = action
        self._transition_remaining[junction_idx] = self.yellow_s + self.all_red_s
        self._switches_this_step += 1

    def _advance_transitions(self, dt: float):
        """Advance any in-progress phase transitions by dt seconds."""
        for j in range(self.num_junctions):
            if self._in_transition[j]:
                self._transition_remaining[j] -= dt
                if self._transition_remaining[j] <= 0:
                    # Transition complete: switch to target phase
                    self._current_phases[j] = self._pending_phase[j]
                    self._phase_elapsed[j] = 0.0
                    self._in_transition[j] = False
                    self._transition_remaining[j] = 0.0
                    # Apply the new phase in SUMO
                    self._set_sumo_phase(j, self._current_phases[j])
            else:
                self._phase_elapsed[j] += dt

    def _set_sumo_phase(self, junction_idx: int, phase_idx: int):
        """Set the SUMO traffic light to a specific phase."""
        tls_id = self.tls_ids[junction_idx]
        try:
            traci.trafficlight.setPhase(tls_id, phase_idx)
        except traci.TraCIException as e:
            # TLS ID might not match; log but don't crash
            pass

    # ──────────────────────── Episode Control ────────────────────────

    def reset(self, seed: Optional[int] = None) -> dict[str, Any]:
        """
        Reset the environment: start a new SUMO simulation episode.

        Returns:
            dict with keys per junction: 'obs', 'action_mask'
        """
        self.close()

        # Build SUMO command
        sumo_binary = "sumo-gui" if self.gui else "sumo"

        # Try to find SUMO binary
        sumo_home = os.environ.get("SUMO_HOME", "")
        sumo_bin_path = None
        for candidate in [
            os.path.join(sumo_home, "bin", sumo_binary),
            sumo_binary,
        ]:
            if os.path.isfile(candidate) or self._which(candidate):
                sumo_bin_path = candidate
                break

        if sumo_bin_path is None:
            # Try eclipse-sumo pip package
            try:
                import sumo

                sumo_bin_path = os.path.join(
                    os.path.dirname(sumo.__file__), "bin", sumo_binary
                )
            except ImportError:
                sumo_bin_path = sumo_binary  # Hope it's on PATH

        # Assign port
        if self.port is None:
            import socket
            with socket.socket() as s:
                s.bind(("", 0))
                self.port = s.getsockname()[1]

        sumo_cmd = [
            sumo_bin_path,
            "-n", self.net_file,
            "-r", self.route_file,
            "--no-step-log", "true",
            "--waiting-time-memory", "1000",
            "--no-warnings", "true",
            "--duration-log", "false",
            "--tripinfo-output", str(PROJECT_ROOT / "results" / f"tripinfo_{self.label}.xml"),
            "--seed", str(seed if seed is not None else 42),
            "--remote-port", str(self.port),
        ]

        # Start SUMO
        self._sumo_process = subprocess.Popen(
            sumo_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Connect via TraCI
        time.sleep(0.5)
        traci.init(self.port, label=self.label)
        self._conn = traci

        # Reset internal state
        self._step_count = 0
        self._sim_time = 0.0
        self._current_phases = [0] * self.num_junctions
        self._phase_elapsed = [0.0] * self.num_junctions
        self._in_transition = [False] * self.num_junctions
        self._transition_remaining = [0.0] * self.num_junctions
        self._pending_phase = [0] * self.num_junctions
        self._lane_queues = np.zeros((self.num_junctions, self.num_lanes))
        self._missing_masks = np.zeros(
            (self.num_junctions, self.num_lanes), dtype=bool
        )
        self._obs_ages = np.zeros((self.num_junctions, self.num_lanes))
        self._switches_this_step = 0

        # Fault RNG
        fault_s = self.fault_seed if self.fault_seed is not None else seed
        self._fault_rng = np.random.RandomState(fault_s) if self.fault_rate > 0 else None

        # Warmup
        for _ in range(self.warmup_steps):
            traci.simulationStep()
        self._sim_time = traci.simulation.getTime()

        # Collect initial observations
        return self._collect_obs()

    def step(self, actions: dict[str, int]) -> tuple[dict, float, bool, dict]:
        """
        Execute one decision step across all junctions.

        Args:
            actions: dict mapping junction alias -> phase index

        Returns:
            (observations, reward, done, info)
        """
        self._switches_this_step = 0

        # Apply actions
        for j, jid in enumerate(self.junction_ids):
            if jid in actions:
                self._apply_action(j, actions[jid])

        # Advance simulation by decision_interval
        steps_to_run = self.decision_interval
        for _ in range(steps_to_run):
            traci.simulationStep()
            self._sim_time = traci.simulation.getTime()
            self._advance_transitions(1.0)

        self._step_count += 1

        # Check done
        done = self._sim_time >= self.episode_length

        # Collect observations
        obs = self._collect_obs()

        # Compute reward
        reward = self._compute_reward()

        # Info dict with per-junction metrics
        info = {
            "sim_time": self._sim_time,
            "step": self._step_count,
            "total_waiting": self._get_total_waiting_time(),
            "total_halting": self._get_total_halting_vehicles(),
            "completed_trips": self._get_completed_trips(),
            "switches": self._switches_this_step,
        }

        return obs, reward, done, info

    def _collect_obs(self) -> dict[str, Any]:
        """Collect observations and action masks for all junctions."""
        result = {}
        for j, jid in enumerate(self.junction_ids):
            result[jid] = {
                "obs": self._get_observation(j),
                "action_mask": self._get_action_mask(j),
            }
        return result

    # ──────────────────────── Metrics ────────────────────────

    def _get_total_waiting_time(self) -> float:
        """Total accumulated waiting time across all vehicles."""
        try:
            total = 0.0
            for veh_id in traci.vehicle.getIDList():
                total += traci.vehicle.getAccumulatedWaitingTime(veh_id)
            return total
        except traci.TraCIException:
            return 0.0

    def _get_total_halting_vehicles(self) -> int:
        """Total number of halting vehicles in the network."""
        try:
            return sum(
                traci.lane.getLastStepHaltingNumber(lane)
                for lane in traci.lane.getIDList()
            )
        except traci.TraCIException:
            return 0

    def _get_completed_trips(self) -> int:
        """Number of vehicles that have completed their trips."""
        try:
            return traci.simulation.getArrivedNumber()
        except traci.TraCIException:
            return 0

    # ──────────────────────── Lifecycle ────────────────────────

    def close(self):
        """Shut down the SUMO simulation cleanly."""
        try:
            if self._conn is not None:
                traci.close()
        except (traci.TraCIException, traci.FatalTraCIError):
            pass
        self._conn = None

        if self._sumo_process is not None:
            self._sumo_process.terminate()
            try:
                self._sumo_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._sumo_process.kill()
            self._sumo_process = None

        self.port = None  # Re-assign next time

    @staticmethod
    def _which(program: str) -> Optional[str]:
        """Check if a program is on PATH."""
        import shutil
        return shutil.which(program)

    def __del__(self):
        self.close()
