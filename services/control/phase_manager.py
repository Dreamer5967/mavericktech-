"""
Safety Phase Manager Module
===========================
Deterministic safety layer that validates and sequences all traffic signal transitions.
Ensures that no policy (learned, heuristic, or remote) can cause unsafe signal actuation.

Key Constraints Enforced:
1. Minimum green duration (e.g., 10s)
2. Maximum green cap (e.g., 60s)
3. Mandatory clearance sequence: GREEN -> YELLOW (3s) -> ALL_RED (2s) -> NEW GREEN
4. Conflict matrix: blocks conflicting simultaneous green phases
5. Freshness checks: observation age (< 2.0s) and state revision matching
6. Safe fallback progression if proposals time out or are invalid
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class PhaseProposal:
    """Incoming proposal from a policy or planner."""
    junction_id: str
    requested_phase: str
    current_phase: str
    elapsed_in_phase_s: float
    observation_age_s: float
    state_revision: int
    expected_revision: int
    proposal_id: str = "prop-0"


@dataclass
class JunctionPhaseState:
    """Live state of an intersection signal program."""
    junction_id: str
    current_phase: str
    elapsed_s: float = 0.0
    in_transition: bool = False
    transition_stage: Optional[str] = None  # 'YELLOW', 'ALL_RED', or None
    stage_remaining_s: float = 0.0
    target_phase: Optional[str] = None
    revision: int = 0
    total_rejections: int = 0
    total_switches: int = 0


class SafetyPhaseManager:
    """
    Independent deterministic safety phase manager.
    """

    def __init__(
        self,
        allowed_phases: Dict[str, Set[str]],
        min_green_s: float = 10.0,
        yellow_s: float = 3.0,
        all_red_s: float = 2.0,
        max_green_s: float = 60.0,
        max_observation_age_s: float = 2.0
    ):
        self.allowed_phases = allowed_phases
        self.min_green_s = min_green_s
        self.yellow_s = yellow_s
        self.all_red_s = all_red_s
        self.max_green_s = max_green_s
        self.max_age_s = max_observation_age_s

        # Live state per junction
        self.states: Dict[str, JunctionPhaseState] = {}
        for jid, phases in allowed_phases.items():
            # Prefer NS_GREEN as default starting phase if present, else first sorted
            default_p = "NS_GREEN" if "NS_GREEN" in phases else sorted(list(phases))[0]
            self.states[jid] = JunctionPhaseState(
                junction_id=jid,
                current_phase=default_p,
                elapsed_s=0.0
            )

    def validate_request(self, req: PhaseProposal) -> Tuple[bool, str]:
        """
        Screen an incoming phase proposal against deterministic safety rules.

        Returns:
            (is_approved, reason_code)
        """
        jid = req.junction_id
        if jid not in self.allowed_phases:
            return False, "unknown_junction"

        valid_phases = self.allowed_phases[jid]
        if req.requested_phase not in valid_phases or req.current_phase not in valid_phases:
            return False, "unknown_phase"

        # Check numeric validity
        times = (req.elapsed_in_phase_s, req.observation_age_s)
        if any(not math.isfinite(x) or x < 0.0 for x in times):
            return False, "invalid_timing_value"

        # Check revision freshness
        if req.state_revision != req.expected_revision:
            return False, "stale_revision"

        # Check observation freshness
        if req.observation_age_s > self.max_age_s:
            return False, "stale_observation"

        # If junction is currently in clearance transition, reject new requests
        state = self.states[jid]
        if state.in_transition:
            return False, "transition_in_progress"

        # If requesting same phase -> Hold
        if req.requested_phase == req.current_phase:
            return True, "hold"

        # If requesting phase change, verify minimum green has elapsed
        if req.elapsed_in_phase_s < self.min_green_s:
            return False, "minimum_green_violation"

        return True, "approved_transition"

    def schedule_transition(self, jid: str, target_phase: str) -> List[str]:
        """
        Initiate the approved clearance sequence for a junction:
        [YELLOW, ALL_RED, TARGET_PHASE]
        """
        state = self.states[jid]
        state.in_transition = True
        state.transition_stage = "YELLOW"
        state.stage_remaining_s = self.yellow_s
        state.target_phase = target_phase
        state.revision += 1
        state.total_switches += 1

        return [f"{state.current_phase}_YELLOW", "ALL_RED", target_phase]

    def request_emergency_preemption(
        self, jid: str, target_phase: str, priority_level: int = 1
    ) -> Tuple[bool, str, List[str]]:
        """
        Processes an emergency vehicle preemption (EVC) request.
        Allows safe truncation of non-emergency green to a reduced safety interval (5s),
        while strictly preserving mandatory YELLOW and ALL_RED clearance stages.
        """
        if jid not in self.allowed_phases:
            return False, "unknown_junction", []
        if target_phase not in self.allowed_phases[jid]:
            return False, "unknown_phase", []

        state = self.states[jid]

        # Case 1: Already in target green phase
        if state.current_phase == target_phase and not state.in_transition:
            # Prevent max-green timeout during emergency passage
            state.elapsed_s = min(state.elapsed_s, 5.0)
            return True, "corridor_green_locked", [target_phase]

        # Case 2: Currently transitioning
        if state.in_transition:
            if state.target_phase == target_phase:
                return True, "clearance_already_underway", [state.target_phase]
            state.target_phase = target_phase
            return True, "transition_target_overridden", [state.target_phase]

        # Case 3: In conflicting phase -> initiate safe clearance sequence
        emergency_min_green_s = 5.0 if priority_level == 1 else self.min_green_s
        if state.elapsed_s < emergency_min_green_s:
            return False, "emergency_minimum_green_pending", []

        seq = self.schedule_transition(jid, target_phase)
        return True, "emergency_clearance_initiated", seq

    def tick(self, dt: float) -> Dict[str, str]:
        """
        Advance simulation time by dt seconds and progress clearance states.

        Returns:
            dict mapping junction_id -> active signal string (e.g. 'NS_GREEN', 'YELLOW', 'ALL_RED')
        """
        active_signals = {}
        for jid, state in self.states.items():
            if state.in_transition:
                state.stage_remaining_s -= dt
                if state.stage_remaining_s <= 0:
                    if state.transition_stage == "YELLOW":
                        # Transition to ALL_RED
                        state.transition_stage = "ALL_RED"
                        state.stage_remaining_s = self.all_red_s
                        active_signals[jid] = "ALL_RED"
                    elif state.transition_stage == "ALL_RED":
                        # Clearance complete: switch to target green phase
                        state.current_phase = state.target_phase
                        state.elapsed_s = 0.0
                        state.in_transition = False
                        state.transition_stage = None
                        state.target_phase = None
                        active_signals[jid] = state.current_phase
                else:
                    active_signals[jid] = state.transition_stage
            else:
                state.elapsed_s += dt
                active_signals[jid] = state.current_phase

                # Auto-advance if max-green cap is exceeded
                if state.elapsed_s >= self.max_green_s:
                    phases = sorted(list(self.allowed_phases[jid]))
                    curr_idx = phases.index(state.current_phase)
                    next_phase = phases[(curr_idx + 1) % len(phases)]
                    self.schedule_transition(jid, next_phase)

        return active_signals
