"""
Missing-State Estimator Module
==============================
Maintains per-lane queue estimates and uncertainty intervals when cameras fail.

Strictly adheres to the information boundary:
- Never queries simulator ground-truth (e.g. traci.vehicle)
- Only updates from LaneObservation messages (camera or prior estimate)
- Enforces queue conservation:
    Q_next = clamp(Q_prev + arrivals - departures, 0, capacity)
- Expands uncertainty intervals [lower, upper] as observation age increases
- Reconciles smoothly when camera recovers
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np


@dataclass
class LaneBelief:
    """Belief state for an individual lane."""
    lane_id: str
    estimated_queue: float
    lower_queue: float
    upper_queue: float
    observation_age_s: float
    last_observed_at_sim_s: Optional[float]
    missing: bool
    capacity: float = 15.0


class MissingStateEstimator:
    """
    Belief-state tracker for all controlled lanes across the 4 junctions.
    """

    def __init__(
        self,
        default_capacity: float = 15.0,
        saturation_flow_rate_veh_s: float = 0.5,  # ~1800 veh/hr = 0.5 veh/s on green
        nominal_arrival_rate_veh_s: float = 0.15, # ~540 veh/hr arrival
        uncertainty_growth_rate: float = 0.08,    # queue interval expands by 0.08 veh/sec missing
        reconciliation_alpha: float = 0.4         # smooth blend when camera recovers
    ):
        self.default_capacity = default_capacity
        self.sat_flow = saturation_flow_rate_veh_s
        self.nominal_arrival = nominal_arrival_rate_veh_s
        self.uncertainty_growth = uncertainty_growth_rate
        self.alpha = reconciliation_alpha

        # Storage: lane_id -> LaneBelief
        self.beliefs: Dict[str, LaneBelief] = {}

    def register_lane(self, lane_id: str, capacity: Optional[float] = None):
        """Register a lane to be tracked by the estimator."""
        cap = capacity if capacity is not None else self.default_capacity
        self.beliefs[lane_id] = LaneBelief(
            lane_id=lane_id,
            estimated_queue=0.0,
            lower_queue=0.0,
            upper_queue=0.0,
            observation_age_s=0.0,
            last_observed_at_sim_s=0.0,
            missing=False,
            capacity=cap
        )

    def update_lane(
        self,
        lane_id: str,
        observed_count: Optional[int],
        sim_time_s: float,
        dt: float,
        is_green: bool,
        upstream_inflow_est: Optional[float] = None
    ) -> LaneBelief:
        """
        Update belief state for a single lane given incoming sensor message.

        Args:
            lane_id: Identifier of the lane
            observed_count: Integer vehicle count from camera, or None if camera is down
            sim_time_s: Current simulation timestamp in seconds
            dt: Time elapsed since last decision step (seconds)
            is_green: Whether this lane currently has green light
            upstream_inflow_est: Optional upstream neighbor departure rate
        """
        if lane_id not in self.beliefs:
            self.register_lane(lane_id)

        belief = self.beliefs[lane_id]
        capacity = belief.capacity

        if observed_count is not None:
            # Camera AVAILABLE
            raw_count = float(observed_count)

            if belief.missing:
                # Smooth reconciliation when camera just recovered
                smoothed_q = (1.0 - self.alpha) * belief.estimated_queue + self.alpha * raw_count
                belief.estimated_queue = float(np.clip(smoothed_q, 0.0, capacity))
            else:
                belief.estimated_queue = float(np.clip(raw_count, 0.0, capacity))

            # Direct observation has tight bounds
            belief.lower_queue = max(0.0, math.floor(belief.estimated_queue))
            belief.upper_queue = min(capacity, math.ceil(belief.estimated_queue) + 1.0)
            belief.observation_age_s = 0.0
            belief.last_observed_at_sim_s = sim_time_s
            belief.missing = False

        else:
            # Camera MISSING: Apply conservation rule
            # Departures: 0 if red, sat_flow * dt if green
            departures = (self.sat_flow * dt) if is_green else 0.0
            # Arrivals: upstream inflow if known, else nominal rate
            arrivals = (upstream_inflow_est * dt) if upstream_inflow_est is not None else (self.nominal_arrival * dt)

            # Conservation update: Q_{t+1} = clamp(Q_t + A - D, 0, capacity)
            new_est = belief.estimated_queue + arrivals - departures
            belief.estimated_queue = float(np.clip(new_est, 0.0, capacity))

            # Age increases
            belief.observation_age_s += dt
            belief.missing = True

            # Uncertainty interval expands over time
            expansion = self.uncertainty_growth * belief.observation_age_s
            belief.lower_queue = float(np.clip(belief.estimated_queue - expansion, 0.0, capacity))
            belief.upper_queue = float(np.clip(belief.estimated_queue + expansion, belief.lower_queue, capacity))

        return belief

    def get_belief(self, lane_id: str) -> Optional[LaneBelief]:
        """Retrieve current belief state for a lane."""
        return self.beliefs.get(lane_id)

    def get_all_beliefs(self) -> Dict[str, LaneBelief]:
        """Retrieve all lane beliefs."""
        return self.beliefs
