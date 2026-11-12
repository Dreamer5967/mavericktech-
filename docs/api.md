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
the latest snapshot rather than reuse old URLs. Use actual image dimensions
(currently 960x540), not dashboard placeholders.

The live schema is `aegis.p2.live-feed.v1-draft`; the offline replay schema is
`aegis.p2.camera-observations.v1-draft`. Exact fields are in `p2/live_feed.py` and
`p2/observations.py`, respectively. Preserve run/revision, camera/frame IDs,
original source simulation time, wall time, age, stale/missing flags and frame
references. Simulation and wall-clock age are distinct. Saved observations are
`REPLAY`; never replace their source timestamps to make them appear fresh.

Usable whole-image vehicle counts are nullable: stale, missing or failed data
must remain null. Whole-image counts do not establish lane occupancy or queues.
Lane counts and queue estimates remain null; `ready_for_live_policy` is false.
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
The engine returns proposed actions; its internal phase-manager output is not a
record of executed simulator actions. No P2 feed route applies those proposals.
