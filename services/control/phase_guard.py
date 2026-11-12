"""Offline phase-request checks and generic clearance-path validation.
Map-specific conflicts and clearance durations need separate verification.
This module does not execute simulator actions or certify traffic safety.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class TransitionRequest:
    current_phase: str
    requested_phase: str
    elapsed_s: float
    observation_age_s: float
    state_revision: int
    expected_revision: int

# Default reviewed transition sequence dictionary for a standard 4-way intersection
DEFAULT_APPROVED_TRANSITIONS = {
    ("NS_GREEN", "EW_GREEN"): ["NS_YELLOW", "ALL_RED", "EW_GREEN"],
    ("EW_GREEN", "NS_GREEN"): ["EW_YELLOW", "ALL_RED", "NS_GREEN"],
    ("NS", "EW"): ["YELLOW", "ALL_RED", "EW"],
    ("EW", "NS"): ["YELLOW", "ALL_RED", "NS"],
}

# Conflicting phase pairs that can NEVER be active at the same time
CONFLICTING_GREENS = {
    ("NS_GREEN", "EW_GREEN"),
    ("EW_GREEN", "NS_GREEN"),
    ("NS", "EW"),
    ("EW", "NS"),
}

class SafetyPhaseGuard:
    """Traffic safety guard that inspects and validates every proposed signal change."""

    def __init__(self, allowed_phases: set[str], minimum_green_s: float = 10.0,
                 maximum_green_s: float = 60.0, max_age_s: float = 2.0,
                 approved_transitions: dict[tuple[str, str], list[str]] | None = None):
        self.allowed_phases = allowed_phases
        self.minimum_green_s = minimum_green_s
        self.maximum_green_s = maximum_green_s
        self.max_age_s = max_age_s
        self.approved_transitions = (DEFAULT_APPROVED_TRANSITIONS if approved_transitions is None
                                     else approved_transitions)

    def check_request(self, r: TransitionRequest) -> tuple[bool, str]:
        """Validates transition request timing, revision, and legality."""
        # 1. Unknown phase check
        if r.current_phase not in self.allowed_phases or r.requested_phase not in self.allowed_phases:
            return False, "unknown_phase"
        
        # 2. Finite non-negative numbers check
        time_vals = (r.elapsed_s, r.observation_age_s, self.minimum_green_s, self.maximum_green_s, self.max_age_s)
        if any(not math.isfinite(x) or x < 0 for x in time_vals):
            return False, "invalid_time"
        
        # 3. State revision check (prevent acting on outdated world ticks)
        if r.state_revision != r.expected_revision:
            return False, "stale_revision"
        
        # 4. Sensor observation age check (prevent delayed inference)
        if r.observation_age_s > self.max_age_s:
            return False, "stale_state"
        
        # 5. Hold request (maintaining current phase)
        if r.current_phase == r.requested_phase:
            if r.elapsed_s >= self.maximum_green_s:
                # Max green timeout: force rotation to avoid starving conflicting approaches
                return False, "maximum_green_exceeded"
            return True, "hold"
        
        # 6. Minimum green time enforcement
        if r.elapsed_s < self.minimum_green_s:
            return False, "minimum_green"
        
        # 7. Check if a reviewed transition path exists
        try:
            self.get_clearance_sequence(r.current_phase, r.requested_phase)
        except ValueError:
            return False, "no_reviewed_path"
        
        return True, "queue_validated_transition"

    def get_clearance_sequence(self, current: str, target: str) -> list[str]:
        """Returns the mandatory sequence of clearance stages (e.g. Yellow -> All-Red -> Target)."""
        if current == target:
            return [current]
        
        seq = self.approved_transitions.get((current, target))
        if not seq or seq[-1] != target:
            raise ValueError(f"No reviewed transition path from '{current}' to '{target}'")
        return list(seq)

# Backward compatibility functions for starter kit
def check_request(r: TransitionRequest, allowed: set[str],
                  minimum_green_s: float = 10.0, max_age_s: float = 2.0) -> tuple[bool, str]:
    guard = SafetyPhaseGuard(allowed_phases=allowed, minimum_green_s=minimum_green_s, max_age_s=max_age_s)
    return guard.check_request(r)

def transition_sequence(current: str, target: str, approved: dict[tuple[str, str], list[str]]) -> list[str]:
    guard = SafetyPhaseGuard(allowed_phases={current, target}, approved_transitions=approved)
    return guard.get_clearance_sequence(current, target)
