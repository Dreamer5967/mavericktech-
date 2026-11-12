"""Toy schedule validator; not a certified traffic safety system.
Real map-specific signal conflicts/clearance programs must be validated separately.
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

def check_request(r: TransitionRequest, allowed: set[str],
                  minimum_green_s: float = 10.0, max_age_s: float = 2.0) -> tuple[bool,str]:
    if r.current_phase not in allowed or r.requested_phase not in allowed:
        return False,'unknown_phase'
    if any(not math.isfinite(x) or x < 0 for x in (r.elapsed_s,r.observation_age_s,minimum_green_s,max_age_s)):
        return False,'invalid_time'
    if r.state_revision != r.expected_revision:return False,'stale_revision'
    if r.observation_age_s > max_age_s:return False,'stale_state'
    if r.current_phase != r.requested_phase and r.elapsed_s < minimum_green_s:
        return False,'minimum_green'
    return True,('hold' if r.current_phase==r.requested_phase else 'queue_validated_transition')

def transition_sequence(current: str, target: str, approved: dict[tuple[str,str],list[str]]) -> list[str]:
    if current==target:return [current]
    seq=approved.get((current,target))
    if not seq or seq[-1]!=target:raise ValueError('No reviewed transition path')
    return list(seq)
