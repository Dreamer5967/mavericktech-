"""Compatibility imports for shared phase-request validation."""
from services.control.phase_guard import (
    SafetyPhaseGuard, TransitionRequest, check_request, transition_sequence,
)
