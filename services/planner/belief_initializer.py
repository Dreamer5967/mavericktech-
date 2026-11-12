"""
Belief State Initializer
========================
Constructs a synthetic traffic configuration from a LaneBelief state.
Strictly adheres to the observation boundary: does NOT read simulator truth.
"""

from typing import Dict, Any, List
import numpy as np


class BeliefStateInitializer:
    """
    Synthesizes initial vehicle queues and approach conditions for planner lookahead.
    """

    def __init__(self, lane_capacity: float = 15.0):
        self.lane_capacity = lane_capacity

    def initialize_from_beliefs(self, beliefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a synthetic simulation configuration from current belief state.

        Args:
            beliefs: dict mapping lane_id -> LaneBelief or observation array

        Returns:
            dict containing synthetic queue counts, active phase, and arrival assumptions
        """
        synthetic_state = {}
        for lane_id, b in beliefs.items():
            if hasattr(b, 'estimated_queue'):
                q = b.estimated_queue
                lower = b.lower_queue
                upper = b.upper_queue
                missing = b.missing
            elif isinstance(b, np.ndarray):
                q = float(b[0]) * self.lane_capacity
                lower = max(0.0, q - 1.0)
                upper = min(self.lane_capacity, q + 1.0)
                missing = False
            else:
                q = 2.0
                lower, upper, missing = 1.0, 3.0, False

            synthetic_state[lane_id] = {
                "nominal_queue": float(np.clip(q, 0.0, self.lane_capacity)),
                "lower_queue": float(lower),
                "upper_queue": float(upper),
                "camera_missing": missing
            }
        return synthetic_state
