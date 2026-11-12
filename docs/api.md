# Camera observation API

The P2 adapter is read-only, binds to loopback port 8765 and is accessible through
authenticated SSH forwarding. P4 owns application authentication and operator,
question and reset routes.

| Implemented route | Purpose |
|---|---|
| `GET /health` | Readiness and data mode |
| `GET /api/v1/snapshot` | Latest observations and frame references |
| `GET /api/v1/frames/{frame_id}` | Annotated JPEG from the bounded cache |
| `GET /api/v1/events` | Recent observation event history |

POST requests are rejected. Frame references expire as the cache advances; fetch
the latest snapshot rather than reuse old URLs. Use the configured image
dimensions: 960x540 for the oblique profile or 1280x1280 for the coverage profile.

The live schema is `aegis.p2.live-feed.v1-draft`; the offline replay schema is
`aegis.p2.camera-observations.v1-draft`. Exact fields are in `p2/live_feed.py` and
`p2/observations.py`, respectively. Preserve run/revision, camera/frame IDs,
original source simulation time, wall time, age, stale/missing flags and frame
references. Simulation and wall-clock age are distinct. Saved observations are
`REPLAY`; never replace their source timestamps to make them appear fresh.

Usable whole-image vehicle counts are nullable: stale, missing or failed data
must remain null. Whole-image counts do not establish lane occupancy or queues.
With the validated coverage profile and matching `--lane-regions`, `lane_counts`
maps SUMO lane IDs to detected vehicle occupancy in reviewed ROIs. The 22 usable
regions can publish counts; two tree-occluded regions stay null. Stale, failed or
dropped camera data masks all its usable lane counts to null without changing
the original frame/source timestamps. `lane_count_semantics` identifies this as
`detected_vehicle_roi_occupancy`; it is not a stopped-queue measurement. Other
profiles retain null lane counts. `queue_estimate` remains null and
`ready_for_live_policy` is false. `active_faults` identifies deliberately dropped
camera IDs during a bounded CLI fault test.
Never pass evaluator ground truth into policy observations.

When control is integrated, keep proposal, scheduled action and actual execution
as distinct records. Incidents, reset, questions and experiment routes remain
separate P4 work and are not implemented by this adapter.

## Policy source integration

`services/control/inference_entrypoint.py` consumes per-junction feature vectors
and action masks; it does not consume the raw camera snapshot directly. The
model declares four lane slots per junction. Whole-image counts cannot fill
those lane slots. A reviewed lane adapter, real phase-index mapping and runtime
network-hash verification are still required before connecting live control.

Checkpoint loading verifies SHA256 against `manifests/model_manifest.json`
(or an explicitly supplied expected digest for an offline fixture) and uses
`torch.load(weights_only=True)`. The declared external artifact has not yet been
verified. A correctly formatted manifest is not proof of model provenance.
The v2 engine returns `proposed_sumo_phases`, `policy_actions` and
`requires_transition_validation=true`. Its `actions` and `active_signals` maps
are empty and `actuation_permitted` is always false. A proposal is never safe to
pass directly to `setPhase`. No P2 feed route applies these proposals.

V2 slots aggregate the declared physical lanes by approach. Any unavailable
member masks the aggregate slot; it is not treated as a complete measured count.
Beliefs sum across lanes and normalize by 15 vehicles per physical lane times
the number of lanes in the slot. Structurally unused slots have zero features
and a true missing mask. This candidate normalization/aggregation contract still
requires review and retraining. ROI vehicle occupancy is not a queue measurement.
