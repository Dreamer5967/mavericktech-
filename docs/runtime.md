# Current runtime

Last verified cloud results: 12 November 2026. These are completed runs, not a
claim that a feed or bridge is currently running.

## Existing installation

- Workspace: `/workspace/aegis`; CARLA: `/workspace/aegis/carla`.
- Python: `/workspace/aegis/venv-sim/bin/python`, version 3.10.13.
- CARLA 0.9.15, map `Carla/Maps/Town10HD_Opt`, RTX 3090 Ti.
- YOLOv10n checkpoint: `/root/yolov10n.pt`, excluded from Git.
- Approved venv packages: eclipse-sumo, traci and sumolib 1.20.0; lxml 5.3.0.
  Use `venv-sim/bin/sumo` and `venv-sim/bin/netconvert`; system SUMO remains 1.4.0.
- `SUMO_HOME=/workspace/aegis/venv-sim/lib/python3.10/site-packages/sumo`.

The package setup preserved working perception libraries. Do not reinstall CARLA
or repeat setup as a routine prerequisite.

## Simulation inputs

Map bundle: `/workspace/aegis/maps/town10-map-20261112T071329Z-dff47bc2`.
Demand: `/workspace/aegis/scenarios/town10-demand-20261112T080350Z-bacdddb4/scenario.sumocfg`.
Demand contains 12 passenger routes and 48 scheduled vehicles, seed 42, with a
0.05-second step. Camera/signal IDs: cam_g1=719, cam_g3=23, cam_g4=189, cam_g5=468.
All 24 physical lane IDs and actual signal programs are now inventoried in
`configs/runtime_mapping.json`; [policy compatibility and camera coverage](lane_mapping.md)
remain unverified.

## Completed validation

- Four angled cameras with warmed YOLO: ages 0.523–0.617 simulation seconds,
  maximum inter-camera skew 0.094 seconds; car counts 0, 2, 0, 3. Visual review
  found missed cars and occlusion. Evidence run under `evidence/multicam`:
  `p2-smoke-20261112T070404Z-86ad7e08`.
- Ten-minute continuous feed: four JPEG URLs and increasing revisions verified;
  sampled ages 0.13–0.25 simulation seconds. The published adapter provides
  roughly two observation/preview updates per second. Higher-FPS delivery was
  not validated.
- Approved 30-second stock bridge test: SUMO reached 28.05 simulation seconds;
  57 observer samples and up to 14 CARLA vehicle actors. Cleanup restored
  asynchronous mode on the same map. No restart or map load. The legacy bridge
  needs a process-local `traci.sumolib=sumolib` alias. Warnings for landmarks
  955/956 did not involve the four selected signals. Evidence:
  `/workspace/aegis/evidence/cosim-smoke/test-20261112T081204Z-6199.jsonl`.

## Remaining validation

Combined cameras and synchronized traffic passed an approved bounded test on
12 November 2026, using merged main commit `de2883a` plus the observer/validation
modules. Evidence run: `pipeline-20261112T091232Z-8ce0c931` under
`/workspace/aegis/evidence/pipeline-validation/p2-combined-2961dcd55cbc46f6ac0a933ee5f86e72`.

- One bridge clock owner ran for 30 seconds; SUMO finished at 29.95 seconds.
- 30 evaluator checks found no missing selected landmarks and no CARLA/SUMO
  signal-state mismatches; up to 14 vehicles were mirrored into CARLA.
- 63 snapshots were sampled while synchronous mode was observed. Each camera
  was fresh in 58; startup-stale observations retained null usable counts.
  Cameras supplied 56–57 distinct fresh frames each. Fresh sample simulation
  ages were 0–0.396 seconds, with per-camera medians 0.15–0.20 seconds.
- All four HTTP JPEGs decoded at 960x540; downloaded hashes matched. Visual
  inspection confirmed annotated vehicle detections and partial approach views.
- The camera worker reported no errors or cleanup failures; no RGB sensors
  remained. The post-check confirmed the same map and asynchronous mode.

This validates fixed-time synchronization with camera observations. Lane counts,
queues, learned-policy control and P4 frontend integration remain incomplete.
Policy readiness is false; evaluator signal/actor reference data is kept out of
the observation API.

## Independent lane-count and fault validation

The 1280x1280 overhead coverage profile was tested on the existing asynchronous
world, with no manual ticks, restart or map change. All 24 lane ROIs are in frame.
A controlled 24-vehicle stationary-target test detected targets in every region;
duplicate suppression corrected two overcounts on the saved detections. Twenty-two
clear ROIs are enabled; tree-occluded lanes `20_3` and `20_4` stay null. This is
limited detector/assignment validation, not a traffic or queue-accuracy benchmark.
All owned test vehicles and cameras were removed. Evidence run:
`p2-smoke-20261112T095308Z-fb29b96b` under `evidence/lane-fixture`.

The subsequent live lane-feed/dropout test passed over 156 sampled snapshots:
22 lane IDs published counts, both occluded lanes stayed null, and cam_g3's
8-second interruption produced 30 stale samples with null counts and one unchanged
source frame/timestamp. The camera recovered; cam_g1/cam_g4/cam_g5 delivered
8/8/7 distinct fresh frames during the fault. JPEGs decoded at 1280x1280 and
cleanup reported no errors or remaining RGB actors. Sampled fresh-frame median
ages were 1.00-1.17 simulation seconds. Observed per-camera processed-frame
updates were about 0.68-0.70/s, or 0.53/s for the intentionally interrupted camera;
higher FPS is not claimed. This is slower than the simpler oblique preview.
Run: `lane-feed-d3f5706949` under
`/workspace/aegis/evidence/lane-feed/p2-lane-feed-0f0fd396338f434f801e6a1e6d414ad4`.

Source timestamps, staleness masking and queue/policy boundaries remain enforced.
The tests expired and stopped; they are not a permanently running deployment.

Before execution, check the existing map, synchronization owner and RGB sensors.
Clock advancement or environment changes require approval. Clean up only actors
owned by the current worker. Never restart CARLA or load a map automatically.
