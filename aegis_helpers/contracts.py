"""Minimal observation boundary with no simulator truth fields."""
from dataclasses import dataclass, asdict
import math
@dataclass(frozen=True)
class LaneObservation:
    lane_id: str
    observed_count: int | None
    estimated_queue: float
    lower_queue: float
    upper_queue: float
    observed_at_sim_s: float | None
    sim_time_s: float
    source: str
    missing: bool
    def validate(self):
        if not self.lane_id: raise ValueError('lane_id required')
        if self.source not in {'camera','estimate','mock'}: raise ValueError('Unknown source')
        vals=(self.estimated_queue,self.lower_queue,self.upper_queue,self.sim_time_s)
        if any(not math.isfinite(x) or x < 0 for x in vals): raise ValueError('Invalid number')
        if not self.lower_queue <= self.estimated_queue <= self.upper_queue: raise ValueError('Bad interval')
        if self.observed_count is not None and (isinstance(self.observed_count,bool) or not isinstance(self.observed_count,int) or self.observed_count < 0):
            raise ValueError('Count must be a nonnegative integer or null')
        if self.missing and self.observed_count is not None: raise ValueError('Missing sensor must have null raw count')
        if self.observed_at_sim_s is not None:
            if not math.isfinite(self.observed_at_sim_s) or not 0 <= self.observed_at_sim_s <= self.sim_time_s:
                raise ValueError('Observation timestamp is invalid')
        if self.source=='camera' and (self.missing or self.observed_count is None or self.observed_at_sim_s is None):
            raise ValueError('Camera observation needs a count and timestamp')
        return self
    def as_dict(self):return asdict(self.validate())
