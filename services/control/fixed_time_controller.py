"""
Fixed-Time Baseline Controller
===============================
A simple cyclic controller that applies equal-duration green phases
to each junction in a round-robin fashion. This is the comparison
baseline for all MAPPO experiments.

This controller is deterministic and does not use any learned parameters.
"""

from typing import Optional


class FixedTimeController:
    """
    Cycles through green phases at each junction with equal duration.

    Parameters:
        junction_ids:   List of junction alias strings (e.g., ["J1", "J2", "J3", "J4"])
        num_phases:     Number of green phases per junction
        phase_duration: Duration of each green phase in decision steps
                        (e.g., 6 steps × 5s interval = 30s per phase)
    """

    def __init__(
        self,
        junction_ids: list[str],
        num_phases: int = 4,
        phase_duration: int = 6,
    ):
        self.junction_ids = junction_ids
        self.num_phases = num_phases
        self.phase_duration = phase_duration

        # Current phase index and step counter per junction
        self._current_phase = {jid: 0 for jid in junction_ids}
        self._steps_in_phase = {jid: 0 for jid in junction_ids}

    def reset(self):
        """Reset all junctions to phase 0, step 0."""
        for jid in self.junction_ids:
            self._current_phase[jid] = 0
            self._steps_in_phase[jid] = 0

    def get_actions(self, obs: Optional[dict] = None) -> dict[str, int]:
        """
        Get the next action for each junction.
        Observations are ignored — this is a fixed-time controller.

        Returns:
            dict mapping junction_id -> phase_index
        """
        actions = {}
        for jid in self.junction_ids:
            actions[jid] = self._current_phase[jid]

            self._steps_in_phase[jid] += 1
            if self._steps_in_phase[jid] >= self.phase_duration:
                # Advance to next phase
                self._current_phase[jid] = (
                    self._current_phase[jid] + 1
                ) % self.num_phases
                self._steps_in_phase[jid] = 0

        return actions

    def __repr__(self):
        return (
            f"FixedTimeController(junctions={self.junction_ids}, "
            f"phases={self.num_phases}, duration={self.phase_duration})"
        )
