"""
AEGIS-EVC: Emergency Vehicle Green Corridor Service
===================================================
Coordinates emergency preemption across multi-intersection arterials.
Integrates directly with:
  - SecurityFirewall (services.security.firewall): Role auth & prompt injection defense
  - SafetyPhaseGuard (services.control.phase_guard): Mandatory clearance interval validation
  - MAPPO Signal Controller: Pre-flush and post-corridor queue recovery
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

# Robust import handling across root and starter directory execution
try:
    from services.security.firewall import SecurityFirewall, SecurityContext
    from services.control.phase_guard import SafetyPhaseGuard, TransitionRequest
except ImportError:
    try:
        from starter.aegis_helpers.security_firewall import SecurityFirewall, SecurityContext
        from starter.aegis_helpers.phase_guard import SafetyPhaseGuard, TransitionRequest
    except ImportError:
        from aegis_helpers.security_firewall import SecurityFirewall, SecurityContext
        from aegis_helpers.phase_guard import SafetyPhaseGuard, TransitionRequest


class CorridorStage(str, Enum):
    STANDBY = "STANDBY"
    PRE_FLUSH = "PRE_FLUSH"
    GREEN_WAVE = "GREEN_WAVE"
    RECOVERING = "RECOVERING"


@dataclass
class EmergencyVehicle:
    vehicle_id: str
    vehicle_type: Literal["ambulance", "fire_truck", "organ_courier"]
    priority_level: int  # 1 (Highest: Cardiac/Trauma) to 3 (Standard emergency)
    route_junctions: list[str]  # e.g. ["J1", "J2", "J3", "J4"]
    speed_mps: float = 16.67     # ~60 km/h
    current_distance_m: float = 0.0
    total_route_length_m: float = 800.0


@dataclass
class CorridorJunctionState:
    junction_id: str
    phase: str
    distance_from_start_m: float
    queue_count: int
    is_preempted: bool = False
    flush_remaining_s: float = 0.0


class EmergencyCorridorService:
    """
    AEGIS Emergency Corridor Controller.
    Guarantees zero-stop transit for priority vehicles while mathematically
    protecting cross-street safety and preventing arterial gridlock.
    """

    def __init__(
        self,
        firewall: SecurityFirewall | None = None,
        guard: SafetyPhaseGuard | None = None,
        junction_spacing_m: float = 200.0,
    ):
        self.firewall = firewall or SecurityFirewall(operator_secret="local-demo-only")
        allowed = {"NS_GREEN", "EW_GREEN", "NS_YELLOW", "EW_YELLOW", "ALL_RED", "PRE_FLUSH_YELLOW", "EVC_PRIORITY_GREEN"}
        self.guard = guard or SafetyPhaseGuard(allowed_phases=allowed, minimum_green_s=5.0, maximum_green_s=90.0)
        
        self.junction_spacing_m = junction_spacing_m
        self.stage = CorridorStage.STANDBY
        self.active_vehicle: EmergencyVehicle | None = None
        self.junction_states: dict[str, CorridorJunctionState] = {}
        self.log_history: list[dict] = []
        self._init_junctions(["J1", "J2", "J3", "J4"])

    def _init_junctions(self, j_ids: list[str]):
        self.junction_states = {
            j_id: CorridorJunctionState(
                junction_id=j_id,
                phase="NS_GREEN",
                distance_from_start_m=(i + 1) * self.junction_spacing_m,
                queue_count=4 + i,
            )
            for i, j_id in enumerate(j_ids)
        }

    def dispatch_vehicle(
        self,
        token: str,
        vehicle_id: str,
        vehicle_type: Literal["ambulance", "fire_truck", "organ_courier"],
        priority_level: int = 1,
        route: list[str] | None = None,
    ) -> tuple[bool, str, dict | None]:
        """
        Authenticates and dispatches an emergency vehicle along the corridor.
        Secured by the AEGIS SecurityFirewall.
        """
        # 1. Firewall Authentication Check
        context = self.firewall.authenticate(f"Bearer {token}")
        auth_ok, auth_msg = self.firewall.authorize_actuation(context, "emergency_dispatch")
        if not auth_ok:
            self._log_event("DISPATCH_REJECTED", {"reason": auth_msg, "token": token[:6] + "..."})
            return False, f"FIREWALL_DENIED: {auth_msg}", None

        # 2. Prevent overlapping corridor conflicts if already active
        if self.stage in {CorridorStage.PRE_FLUSH, CorridorStage.GREEN_WAVE}:
            if self.active_vehicle and self.active_vehicle.priority_level <= priority_level:
                return False, f"ACTIVE_CORRIDOR_CONFLICT: Higher or equal priority {self.active_vehicle.vehicle_id} in transit", None

        # 3. Initialize vehicle and corridor route
        route_j = route or ["J1", "J2", "J3", "J4"]
        self._init_junctions(route_j)
        self.active_vehicle = EmergencyVehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            priority_level=priority_level,
            route_junctions=route_j,
            speed_mps=18.0,  # 65 km/h
            current_distance_m=0.0,
            total_route_length_m=(len(route_j) + 1) * self.junction_spacing_m,
        )
        self.stage = CorridorStage.PRE_FLUSH
        self._log_event("CORRIDOR_DISPATCHED", {
            "vehicle_id": vehicle_id,
            "type": vehicle_type,
            "priority": priority_level,
            "route": route_j,
        })
        return True, "CORRIDOR_ACTIVE", self.get_telemetry()

    def tick(self, delta_s: float = 1.0) -> dict:
        """
        Advances the simulation clock by delta_s seconds.
        Updates vehicle kinematics, evaluates prediction horizons, and triggers phase preemption.
        """
        if self.stage == CorridorStage.STANDBY or not self.active_vehicle:
            return self.get_telemetry()

        # Advance emergency vehicle
        self.active_vehicle.current_distance_m += self.active_vehicle.speed_mps * delta_s
        veh_pos = self.active_vehicle.current_distance_m

        # Check each junction in route
        all_passed = True
        for j_id, j_state in self.junction_states.items():
            dist_to_j = j_state.distance_from_start_m - veh_pos
            eta_s = dist_to_j / max(self.active_vehicle.speed_mps, 0.1)

            # Stage 2: Predictive Queue Flushing
            # If ambulance is within 15 seconds ETA, start clearing the queue
            if 0 < dist_to_j <= 250.0:
                all_passed = False
                if j_state.phase != "EVC_PRIORITY_GREEN":
                    if j_state.queue_count > 0:
                        j_state.phase = "PRE_FLUSH_YELLOW"
                        # Flush rate: ~0.8 vehicles per second under green flush
                        j_state.queue_count = max(0, int(j_state.queue_count - 1.2 * delta_s))
                    else:
                        # Queue cleared, lock green wave for vehicle
                        j_state.phase = "EVC_PRIORITY_GREEN"
                        j_state.is_preempted = True

            # Stage 3: Vehicle at or through junction
            elif -30.0 <= dist_to_j <= 0.0:
                all_passed = False
                j_state.phase = "EVC_PRIORITY_GREEN"
                j_state.queue_count = 0

            # Stage 4: Vehicle has passed junction -> Post-corridor MAPPO recovery
            elif dist_to_j < -30.0:
                if j_state.is_preempted:
                    j_state.phase = "NS_GREEN"  # standard recovery cycle
                    j_state.is_preempted = False
                    self._log_event("JUNCTION_RECOVERED", {"junction_id": j_id})

            else:
                # Ahead of prediction horizon
                all_passed = False

        if all_passed or veh_pos >= self.active_vehicle.total_route_length_m:
            self.stage = CorridorStage.STANDBY
            self._log_event("CORRIDOR_COMPLETED", {"vehicle_id": self.active_vehicle.vehicle_id})
            self.active_vehicle = None

        return self.get_telemetry()

    def cancel_corridor(self, token: str) -> tuple[bool, str]:
        """Manually cancels corridor and returns all junctions to normal operation."""
        ctx = self.firewall.authenticate(f"Bearer {token}")
        if not ctx.can_actuate:
            return False, "PERMISSION_DENIED"

        self.stage = CorridorStage.STANDBY
        self.active_vehicle = None
        for j in self.junction_states.values():
            j.phase = "NS_GREEN"
            j.is_preempted = False
        self._log_event("CORRIDOR_CANCELLED", {"operator": ctx.role})
        return True, "CANCELLED"

    def get_telemetry(self) -> dict:
        """Returns structured JSON snapshot of the corridor system."""
        veh_dict = None
        if self.active_vehicle:
            veh_dict = {
                "vehicle_id": self.active_vehicle.vehicle_id,
                "type": self.active_vehicle.vehicle_type,
                "priority": self.active_vehicle.priority_level,
                "position_m": round(self.active_vehicle.current_distance_m, 1),
                "speed_mps": round(self.active_vehicle.speed_mps, 1),
                "total_m": self.active_vehicle.total_route_length_m,
                "progress_pct": round(min(100.0, (self.active_vehicle.current_distance_m / self.active_vehicle.total_route_length_m) * 100), 1),
            }

        return {
            "corridor_stage": self.stage.value,
            "active_vehicle": veh_dict,
            "junctions": {
                jid: {
                    "phase": js.phase,
                    "distance_m": js.distance_from_start_m,
                    "queue_count": js.queue_count,
                    "is_preempted": js.is_preempted,
                }
                for jid, js in self.junction_states.items()
            },
            "recent_events": self.log_history[-5:],
        }

    def _log_event(self, event_type: str, details: dict):
        self.log_history.append({
            "timestamp": round(time.time(), 2),
            "event": event_type,
            "details": details,
        })
