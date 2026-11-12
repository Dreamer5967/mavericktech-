# Lane calibration and policy mapping

The current **coverage profile** is `p2/camera_sites.coverage.json` with
`configs/lane_regions.coverage.json`. Its 1280x1280 overhead views put all 24
lane corridors in frame. Rotated-tile inference detects vehicles that the
single-pass overhead detector missed. Visual review and a controlled stationary
target test support **22 ROI occupancy counters**; lanes `20_3` and `20_4` remain
null because of tree canopy. Every lane contained one known test vehicle;
postprocessing suppressed nested rotated-box duplicates. This small controlled
test does not establish moving-traffic accuracy, dense-queue performance or queue
length estimation. All test vehicles and cameras were cleaned up.

The following inventory/projection table describes the older **oblique profile**.
It remains available as a lower-cost preview, without complete lane counts.

The 12 November 2026 inventory read the existing CARLA map and static SUMO bundle.
It did not tick, restart, load a map, create actors or install packages. The live
OpenDRIVE hash matched the converted bundle. The actual network SHA256 is
`3ef9501d4bb19f868f49395e39007876f834cbfe713f864a7ea8413f98115004`.

`configs/runtime_mapping.json` records the real signal programs, controlled
movements, incoming lane IDs and green states. `configs/lane_regions.json` maps
all 24 CARLA stop lanes to SUMO incoming lanes using their `origId` metadata,
including merged road segments. Polygon regions use actual lane widths and
curved network centerlines over up to 25 upstream metres, projected through the
tested camera transforms. Each stop point was within one metre of its matched
network centerline. Height uses the CARLA stop-point ground plane.

| Camera / policy junction | SUMO signal | Incoming lanes | Actual green phase indices | Lanes with projected area >=100 pixels |
|---|---|---:|---|---:|
| cam_g1 / J1 | 719 | 6 | 0, 3, 6 | 2 |
| cam_g3 / J2 | 23 | 6 | 0, 3, 6 | 2 |
| cam_g4 / J3 | 189 | 8 | 0, 3, 6, 9 | 4 |
| cam_g5 / J4 | 468 | 4 | 0, 3 | 2 |

Projected area is not proof of usable coverage. Oblique overlay inspection found edge
clipping at cam_g1 and small/distant lane regions at cam_g4. Even the clearer
cam_g3/cam_g5 regions do not cover their whole junctions. Occlusion and detector
accuracy were not validated for this older profile; its count publishing stays disabled. Whole-image
vehicle counts must not be substituted for lane counts or stopped queues.

## P3 compatibility

The remake's v2 candidate contract in `configs/action_mapping.json` groups the
physical lanes into four approach slots and permanently masks unused action
slots. It explicitly translates model indices to actual green phases. These
candidate mappings agree with the runtime inventory, but their review flags
remain false. `runtime_mapping.json` retains null reviewed-policy mappings until
contract approval; no lanes are silently truncated.

The candidate manifest now names the correct target network and explicitly marks
the old synthetic checkpoint incompatible and unverified. Matching dimensions
do not establish compatibility: aggregation, masks, normalization and action
semantics changed. Retraining and external artifact verification remain required.
`python -B -m p2.controller_gate` lists the remaining blockers. It can check an external artifact with
`--checkpoint C:/path/to/model.pt`; weights stay outside Git. The pure
`actor_vectors` adapter accepts explicit lane beliefs, masks, ages and phase
context; it rejects unexpected truth fields and missing-count substitutions.

Before learned control, P3 must establish a compatible checkpoint and reviewed
lane/action semantics (or train against the actual lane/phase contract). P2 must
validate sufficient camera coverage and lane observations. Clearance programs
and live execution then need a separate bounded validation. Policy actuation
remains disabled. The source fixes add explicit aggregation, reject all-false
masks and preserve hash verification with tensor-only checkpoint loading.
The inference engine emits no executable actions. Standalone training blocks
launch until the training contract and clearance paths are reviewed, checks the
network hash, translates green slots and uses explicit reviewed yellow/all-red
phase paths. These transitions have been tested with fake TraCI, not cloud-run.

## Reproduce offline

From the repository root, with the downloaded read-only inventory directory:

```powershell
python -B -m p2.runtime_mapping --inventory C:/path/to/lane-inventory --out C:/path/to/new-output
python -B -m p2.controller_gate
```

The builder verifies network/live-map hashes, unique lane mappings and stop-point
alignment before writing new JSON files. It starts no simulator. Raw map bundles
and overlay images remain outside Git under local evidence.
