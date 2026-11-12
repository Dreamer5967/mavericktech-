# Team branch review — 12 November 2026

Source review and selected local checks only; this is not a completion sign-off.
No teammate branches were merged or rewritten. Original roles remain unchanged.

## amal — a3eb805

Contains P1 task/checklist, slide outline, evidence index, cost template, and
additional phase-guard/firewall source and tests. No final PPTX was present.
The firewall uses text-pattern rules and role checks; end-to-end VQA security
and adversarial-model evaluation are not established by these helpers.

Local starter suite: **44 passed, 1 failed**. `test_helpers.PhaseTests.test_no_path`
fails because an empty reviewed transition mapping can fall back to defaults
instead of rejecting the transition. Resolve before merging that phase guard.

## shivanshu — 171a0fa

Contains actor/critic/trainer, estimator, phase manager, planner, inference
entrypoint, result files and tracked checkpoints. Local unittest discovery:
**13 passed, 1 test module import error** because `aegis_helpers` is absent from
the branch. No checkpoint was loaded, training rerun or simulator started.

Integration blockers:

1. Action mapping still contains `TBD_FROM_P2_INVENTORY` signal IDs. `junctions`
   is a dictionary, while inference/SUMO environment code iterates it as a list
   of junction objects.
2. Observation dimensions are inside `_metadata`, but inference reads them at
   the JSON root. These layouts must agree before initialization can succeed.
3. The model manifest names Town05 and SUMO 1.28.0; P2 uses Town10HD_Opt and
   SUMO 1.20.0. The network hash is a descriptive placeholder, not a full SHA256.
4. Training and benchmark runners use synthetic traffic/queue progression.
   Planner rollouts explicitly use synthetic belief dynamics, not independent
   SUMO processes. Their CSVs must not be described as measured CARLA–SUMO gains.
5. Inference can construct an untrained actor without a checkpoint; live
   inference should fail closed on missing verified artifacts/configuration.
6. `.pt` files are tracked, contrary to the project's no-weights Git policy.
   They are excluded from P2 publication. Coordinate removal/artifact storage
   with P3; shared history was not rewritten.

P2 signal mappings: cam_g1→719, cam_g3→23, cam_g4→189, cam_g5→468. Junction
aliases, lane ordering and legal phase mappings still need joint P2/P3 review.

## p4/operator-dashboard — a0cc75d

Contains React/TypeScript dashboard components, health/snapshot polling,
junction cards, readiness indicators and fault/reset request clients. Build
and application runtime checks were not performed in this review.

Remaining integration:

- CameraViewer renders a frame placeholder rather than an image element.
- Types expect fixture `junctions` and numeric queue estimates/intervals. P2
  publishes camera observations with unavailable lane/queue measurements null.
  Add an explicit adapter and nullable types; do not fabricate queue values.
- Camera metadata advertises 1920×1080, while P2 images are 960×540.
- Connect frame URLs, capture timestamps, camera IDs, and stale/missing states.
- No production VQA/two-model routing, Langfuse integration, or real incident/reset
  backend was present. Mock services and request clients do not complete those features.

## Immediate order

P4 connects its viewer to P2's actual frame/observation feed. P3 fixes schema
layouts and agrees on Town10 lane/action mappings with P2. P2 prepares traffic
demand and a bounded synchronized test after live-clock approval. Merge verified
source only and retain honest benchmark provenance.
