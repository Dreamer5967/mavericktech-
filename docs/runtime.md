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
Lane and policy-action mappings remain unverified.

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

Combined cameras with synchronized traffic have not been cloud-tested.
Per-signal phase equality, lane counts, queues, learned-policy control and P4
frontend integration remain incomplete. Policy readiness is false.

Before execution, check the existing map, synchronization owner and RGB sensors.
Clock advancement or environment changes require approval. Clean up only actors
owned by the current worker. Never restart CARLA or load a map automatically.
