# 18. Shared APIs, data contracts, and storage

Use explicit versioned messages and a single-writer event log. SQLite is adequate for a bounded prototype if only the backend writes; JSONL is convenient for append-only experiment artifacts. Do not let four processes write one JSON file concurrently. Large frames are stored as files with hashes and paths, not duplicated into every event.

## Suggested application endpoints

| Endpoint | Purpose | Authority |
|---|---|---|
| GET /health | Service readiness and data mode | Read-only |
| GET /api/v1/snapshot | Latest observation-only state | Read-only |
| GET /api/v1/frames/{frame_id} | Approved recorded image | Read-only |
| GET /api/v1/events | Event stream / history | Read-only |
| POST /api/v1/incidents | Allowlisted simulated fault request | Operator role |
| POST /api/v1/questions | Image + question / selected evidence | Question role; no control access |
| POST /api/v1/reset | Stop/reset/restart current scenario | Operator role + confirmation |
| GET /api/v1/experiments/{id} | Evaluation summary and provenance | Read-only |

The included mock implements only health, snapshot, fixture fault, and fixture reset endpoints. Its route names are development fixtures, not a declaration that these real endpoints are finished.

## Proposal and execution are different records

```json
{
  "proposal_id": "prop-014",
  "run_id": "run-008",
  "based_on_revision": 72,
  "created_at_sim_s": 180.0,
  "expires_at_sim_s": 185.0,
  "junction_id": "J2",
  "action_id": "APPROVED_GREEN_1",
  "requested_duration_s": 10.0,
  "source": "mappo_plus_recovery",
  "checkpoint_hash": "ACTUAL_SHA256"
}
```

The coordinator validates authentication, run/revision freshness, allowed action mapping, timing, and the approved transition path. It emits either a rejection reason or a scheduled action. A later execution record stores actual phase changes. The UI must not equate proposal acceptance with completed execution.

## Tables / event collections

| Collection | Essential fields |
|---|---|
| runs | run_id, mode, map_hash, demand_seed, fault_seed, versions, start/end |
| observations | revision, sim_time, junction/lane, raw count/null, estimate, bounds, source |
| frames | frame_id, camera_id, source_time, hash, relative_path |
| proposals | proposal_id, run_id, revision, schedule, source, expiry |
| executions | proposal_id, checker_result, actual_phase, execution_time |
| incidents | request_id, authorized_actor, type, target, scheduled/applied/end |
| planner_results | snapshot_hash, candidate_id, belief_seed, metrics, deadline_status |
| questions | session_id, frame/decision reference, category, route, response, latency |
| security_events | threat_type, detector_output, actual_label where evaluated, boundary_result |
| evaluations | split, seed, metric_name, value, unit, reference_source |

All request IDs are unique within a run. Duplicate incident/reset requests must not execute twice. Validate enum values and reject nonfinite numbers. Use separate simulation timestamps and wall-clock timestamps. A plan may be stale even if the wall clock is recent when the simulation is accelerated.

## Ground-truth boundary

Place evaluator reference data under a separate directory or service. The controller gets only the observation schema. Training may use reference state for critic/reward calculation, but every live message must identify its actual observation source. Write a test that rejects unexpected fields such as `true_vehicle_positions` at the policy boundary.

