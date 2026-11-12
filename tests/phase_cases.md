# AEGIS Phase Guard Test Cases & Edge Case Specification
**Owner: P1 (Authored) | Hand-off To: P3 (Implementation & Verification)**

> [!NOTE]
> This document specifies the boundary and edge cases that the Phase Guard / Safety Manager must validate before any proposed signal transition is executed on SUMO or CARLA.

---

## 1. Safety Principles
1. **Never skip clearance**: Transitions between conflicting green phases must pass through `YELLOW` and `ALL_RED` intervals.
2. **Never violate minimum green**: An active green phase must remain active for at least `minimum_green_s` (default 10.0s).
3. **Reject stale proposals**: Decisions based on obsolete state revisions (`state_revision != expected_revision`) or delayed observations (`observation_age_s > max_age_s`) must be rejected.
4. **Resilient to missing cameras**: If a camera drops out (`observed_count is None`), use queue interval bounds `[lower_queue, upper_queue]`; never treat missing raw data as zero traffic.
5. **Deterministic fail-safe**: If a proposal is rejected, the signal must maintain its current safe state (`hold`) or follow a predefined fallback timing cycle.

---

## 2. Test Cases Matrix

| Test ID | Scenario Description | Input Parameters | Expected Result | Reason Code |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Standard Valid Transition | `current: NS`, `requested: EW`, `elapsed: 15.0s`, `age: 0.5s`, `rev: 5`, `exp_rev: 5` | `(True, "queue_validated_transition")` | Valid transition with sufficient green time. |
| **TC-02** | Hold Phase | `current: NS`, `requested: NS`, `elapsed: 4.0s`, `age: 0.2s`, `rev: 5`, `exp_rev: 5` | `(True, "hold")` | Requesting same phase is always valid. |
| **TC-03** | Minimum Green Violation | `current: NS`, `requested: EW`, `elapsed: 2.0s` (< 10.0s min), `age: 0.5s` | `(False, "minimum_green")` | Rejects premature termination of green phase. |
| **TC-04** | Stale World Revision | `current: NS`, `requested: EW`, `rev: 4`, `exp_rev: 5` | `(False, "stale_revision")` | Proposer acted on outdated world state. |
| **TC-05** | Stale Observation Age | `current: NS`, `requested: EW`, `elapsed: 15.0s`, `age: 3.5s` (> 2.0s max) | `(False, "stale_state")` | Sensor latency exceeded safety threshold. |
| **TC-06** | Unknown Phase Identifier | `current: NS`, `requested: "XYZ_GREEN"` | `(False, "unknown_phase")` | Requested phase not in junction allowed set. |
| **TC-07** | Negative Elapsed Time | `current: NS`, `requested: EW`, `elapsed: -1.0s` | `(False, "invalid_time")` | Non-finite or negative time value. |
| **TC-08** | Non-Finite Input (NaN / Inf) | `current: NS`, `requested: EW`, `elapsed: math.nan` | `(False, "invalid_time")` | Corrupted floating point value rejected. |
| **TC-09** | Valid Clearance Sequence | Transition from `NS` to `EW` | `['NS_YELLOW', 'ALL_RED', 'EW']` | Complete intermediate clearance sequence. |
| **TC-10** | Missing Transition Path | Transition from `NS` to `DIAGONAL` with no path in approved map | Raises `ValueError` | Unconfigured or dangerous transition path rejected. |
| **TC-11** | Camera Dropout Handling | `observed_count: None`, `missing: True`, `lower: 4`, `upper: 10` | Valid `LaneObservation` | Evaluator uses uncertainty interval instead of 0. |
| **TC-12** | Illegal Missing Zero | `observed_count: 0`, `missing: True` | Fails `LaneObservation.validate()` | A missing sensor cannot claim 0 observed cars. |

---

## 3. Unit Test Verification Script (Python)

To run these checks locally:
```bash
python -m unittest tests/test_helpers.py -v
```

*(Extended test cases to be integrated into `starter/tests/test_helpers.py` during Gate 2).*
