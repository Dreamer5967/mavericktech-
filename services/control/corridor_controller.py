"""
AEGIS-EVC Corridor Controller Module
====================================
Coordinates arterial green wave preemption and predictive queue flushing
across multiple signalized intersections.

Integrates with:
  - SafetyPhaseManager (services.control.phase_manager)
  - SecurityFirewall (services.security.firewall)
  - MAPPO Recovery Compensation
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

from services.control.phase_manager import SafetyPhaseManager
from services.security.firewall import SecurityFirewall, SecurityContext


class CorridorMode(str, Enum):
    STANDBY = "STANDBY"
    FLUSHING = "FLUSHING"
    ACTIVE = "ACTIVE"
    RECOVERY = "RECOVERY"


@dataclass
class PriorityVehicleState:
    vehicle_id: str
    vehicle_type: str  # 'ambulance', 'fire_truck', 'organ_courier'
    priority_level: int  # 1 (Highest) to 3 (Standard)
    route_junctions: List[str]
    position_m: float
    speed_mps: float
    target_speed_mps: float = 16.67  # ~60 km/h


@dataclass
class JunctionFlushingState:
    junction_id: str
    corridor_phase: str
    cross_street_phase: str
    distance_m: float
    estimated_queue: float
    flush_duration_required_s: float
    is_preempted: bool = False
    compensation_seconds: float = 0.0


class CorridorController:
    """
    AEGIS Emergency Green Corridor Controller.
    Computes optimal look-ahead queue clearance times and orchestrates
    multi-junction green waves with deterministic safety clearances.
    """

    def __init__(
        self,
        phase_manager: SafetyPhaseManager,
        firewall: Optional[SecurityFirewall] = None,
        junction_distances_m: Optional[Dict[str, float]] = None,
        saturation_flow_rate_veh_s: float = 0.5,  # ~1800 veh/hr/lane
        vehicle_startup_lost_time_s: float = 2.5,
    ):
        self.phase_mgr = phase_manager
        self.firewall = firewall or SecurityFirewall()
        self.saturation_rate = saturation_flow_rate_veh_s
        self.startup_lost_time = vehicle_startup_lost_time_s

        # Default distances for arterial corridor (Town10)
        self.distances = junction_distances_m or {
            "J1": 200.0,
            "J2": 450.0,
            "J3": 700.0,
            "J4": 950.0,
        }

        self.mode = CorridorMode.STANDBY
        self.active_vehicle: Optional[PriorityVehicleState] = None
        self.junction_states: Dict[str, JunctionFlushingState] = {}
        self.event_log: List[Dict] = []

        self._init_junction_states()

    def _init_junction_states(self):
        for jid, dist in self.distances.items():
            self.junction_states[jid] = JunctionFlushingState(
                junction_id=jid,
                corridor_phase="NS_GREEN",
                cross_street_phase="EW_GREEN",
                distance_m=dist,
                estimated_queue=4.0,
                flush_duration_required_s=0.0,
            )

    def calculate_flush_time_s(self, queue_vehicles: float) -> float:
        """
        Calculates the required pre-flush green duration:
        t_flush = t_startup + (queue / s)
        """
        if queue_vehicles <= 0:
            return 0.0
        return self.startup_lost_time + (queue_vehicles / self.saturation_rate)

    def dispatch_corridor(
        self,
        token: str,
        vehicle_id: str,
        vehicle_type: str = "ambulance",
        priority_level: int = 1,
        route: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Authenticates and activates the emergency green corridor.
        """
        # 1. Security Authorization Gate
        ctx = self.firewall.authenticate(f"Bearer {token}")
        authorized, auth_msg = self.firewall.authorize_actuation(ctx, "dispatch_corridor")
        if not authorized:
            self._log("DISPATCH_BLOCKED", {"reason": auth_msg, "token_prefix": token[:4]})
            return False, f"SECURITY_FIREWALL_REJECTED: {auth_msg}"

        # 2. Priority conflict check
        if self.mode in {CorridorMode.FLUSHING, CorridorMode.ACTIVE} and self.active_vehicle:
            if self.active_vehicle.priority_level <= priority_level:
                return False, f"CORRIDOR_CONFLICT: Equal or higher priority vehicle {self.active_vehicle.vehicle_id} in transit"

        # 3. Setup corridor
        target_route = route or list(self.distances.keys())
        self.active_vehicle = PriorityVehicleState(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            priority_level=priority_level,
            route_junctions=target_route,
            position_m=0.0,
            speed_mps=16.67,
        )
        self.mode = CorridorMode.FLUSHING

        # Calculate initial queue flush durations
        for jid in target_route:
            if jid in self.junction_states:
                js = self.junction_states[jid]
                js.flush_duration_required_s = self.calculate_flush_time_s(js.estimated_queue)

        self._log("CORRIDOR_DISPATCHED", {
            "vehicle_id": vehicle_id,
            "type": vehicle_type,
            "priority": priority_level,
            "route": target_route,
        })
        return True, "CORRIDOR_ACTIVE"

    def step(self, dt: float) -> Dict[str, Any]:
        """
        Advances corridor progression by dt seconds.
        Evaluates look-ahead ETA, triggers preemption, and applies compensation.
        """
        if self.mode == CorridorMode.STANDBY or not self.active_vehicle:
            return self.get_status()

        # Update vehicle position
        veh = self.active_vehicle
        veh.position_m += veh.speed_mps * dt

        all_completed = True
        for jid in veh.route_junctions:
            if jid not in self.junction_states:
                continue
            js = self.junction_states[jid]
            dist_to_j = js.distance_m - veh.position_m
            eta_s = dist_to_j / max(veh.speed_mps, 0.1)

            # Stage A: Approaching intersection (Look-Ahead Pre-Flushing)
            # Trigger pre-flush if ETA <= required flush time + 5s buffer
            trigger_horizon_s = js.flush_duration_required_s + 6.0
            if 0 < dist_to_j and eta_s <= trigger_horizon_s:
                all_completed = False
                if not js.is_preempted:
                    # Request safe preemption from SafetyPhaseManager
                    ok, code, seq = self.phase_mgr.request_emergency_preemption(
                        jid, js.corridor_phase, veh.priority_level
                    )
                    if ok:
                        js.is_preempted = True
                        self._log("PRE_FLUSH_TRIGGERED", {
                            "junction_id": jid,
                            "eta_s": round(eta_s, 1),
                            "action": code,
                            "sequence": seq,
                        })

                # Simulate queue reduction during pre-flush
                if js.estimated_queue > 0:
                    js.estimated_queue = max(0.0, js.estimated_queue - self.saturation_rate * dt)

            # Stage B: Vehicle inside junction conflict area
            elif -20.0 <= dist_to_j <= 0.0:
                all_completed = False
                self.phase_mgr.request_emergency_preemption(
                    jid, js.corridor_phase, veh.priority_level
                )

            # Stage C: Vehicle has passed junction -> Post-corridor MAPPO recovery
            elif dist_to_j < -20.0:
                if js.is_preempted:
                    js.is_preempted = False
                    # Calculate compensatory green time for starved cross-street approach:
                    # Compensation = lost time during preemption (typically 12-20s)
                    js.compensation_seconds = min(25.0, 15.0 + js.estimated_queue * 1.5)
                    self._log("POST_CORRIDOR_RECOVERY", {
                        "junction_id": jid,
                        "compensate_s": round(js.compensation_seconds, 1),
                    })
                    # Schedule transition back to cross street
                    self.phase_mgr.schedule_transition(jid, js.cross_street_phase)

            else:
                all_completed = False

        if all_completed:
            self._log("CORRIDOR_COMPLETED", {"vehicle_id": veh.vehicle_id})
            self.mode = CorridorMode.STANDBY
            self.active_vehicle = None

        return self.get_status()

    def cancel(self, token: str) -> Tuple[bool, str]:
        """Cancels corridor and resets preemption state."""
        ctx = self.firewall.authenticate(f"Bearer {token}")
        if not ctx.can_actuate:
            return False, "PERMISSION_DENIED"

        self.mode = CorridorMode.STANDBY
        self.active_vehicle = None
        for js in self.junction_states.values():
            js.is_preempted = False
        self._log("CORRIDOR_CANCELLED", {"operator": ctx.role})
        return True, "CANCELLED"

    def get_status(self) -> Dict[str, Any]:
        veh_data = None
        if self.active_vehicle:
            veh_data = {
                "vehicle_id": self.active_vehicle.vehicle_id,
                "type": self.active_vehicle.vehicle_type,
                "priority": self.active_vehicle.priority_level,
                "position_m": round(self.active_vehicle.position_m, 1),
                "speed_mps": round(self.active_vehicle.speed_mps, 1),
            }

        return {
            "mode": self.mode.value,
            "vehicle": veh_data,
            "junctions": {
                jid: {
                    "distance_m": js.distance_m,
                    "estimated_queue": round(js.estimated_queue, 1),
                    "is_preempted": js.is_preempted,
                    "compensation_s": round(js.compensation_seconds, 1),
                }
                for jid, js in self.junction_states.items()
            },
            "recent_events": self.event_log[-5:],
        }

    def _log(self, event_name: str, payload: Dict):
        self.event_log.append({
            "timestamp": round(time.time(), 2),
            "event": event_name,
            "details": payload,
        })
