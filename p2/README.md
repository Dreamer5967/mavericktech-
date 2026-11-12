# Simulation and perception

Read [runtime status](../docs/runtime.md) before cloud execution and
[the camera API](../docs/api.md) for frontend integration.

| Tool | Purpose |
|---|---|
| `capture_four.py` | Bounded four-camera capture with warmed YOLO and owned-sensor cleanup |
| `live_feed.py` | Continuous observations and annotated JPEG previews on loopback port 8765 |
| `observations.py` | Validate saved observations as explicitly labelled replay |
| `replay_compare.py` | Offline detection diagnostics on hash-verified images |
| `build_runner.py`, `build_feed_runner.py` | Package source/config into SSH-streamed runners |
| `Invoke-P2Capture.ps1` | Interactive SSH execution and logging |
| `Get-P2Evidence.ps1` | Download evidence runs |
| `prepare_map.py` | Export the existing map and convert static network data |
| `prepare_demand.py` | Generate seeded routes without running a simulator |
| `cosim_smoke.sh` | Guarded 30-second stock CARLA–SUMO bridge test |
| `validate_pipeline.py` | Approved combined camera observer and one bounded bridge clock owner |
| `bridge_validation.py` | Stock bridge wrapper with read-only signal/vehicle evaluator checks |
| `runtime_mapping.py` | Offline hash-verified lane geometry and actual signal program inventory |
| `lane_calibration.py` | Camera projection helpers for lane regions |
| `controller_gate.py` | Offline checkpoint, network, lane-slot and green-action compatibility audit |
| `setup_sumo.py` | Hash-pinned package setup; already completed on this instance |

`camera_sites.oblique.json` is the tested angled configuration; its partial
approach views do not establish lane coverage. `camera_sites.candidate.json`
retains the original overhead configuration.

Describe the camera configuration locally without cloud contact:

```powershell
py -3.14 -B -m p2.capture_four --config p2/camera_sites.oblique.json
```

Build a capture runner locally:

```powershell
py -3.14 -B -m p2.build_runner --config p2/camera_sites.oblique.json --out C:/path/to/run_capture.sh
```

The runner requires `AEGIS_APPROVE_FOUR_CAMERA_CAPTURE=yes`. It creates cameras,
uses the GPU and writes evidence; it does not tick or change the map. Check owned
sensor cleanup results before retrying an interrupted run.

For an approved standalone feed, use the existing cloud interpreter from the
source checkout and forward port 8765 over authenticated SSH:

```bash
/workspace/aegis/venv-sim/bin/python -m p2.live_feed --config p2/camera_sites.oblique.json --execute --duration 600
```

The published standalone worker expects asynchronous CARLA and owns no clock.
Stop the standalone worker before starting the stock synchronous bridge. For a
combined run, `validate_pipeline.py` starts the feed with `--clock-mode observer`
before launching its single bridge child; the observer never ticks or changes
world settings. It verifies advancing fresh frames and JPEG decoding, saves
timestamped observations and evaluator records separately, and checks cleanup.
Use `--execute` and `AEGIS_APPROVE_LIVE_COSIM=yes` only for an approved run of at
most 30 seconds. Run from an isolated source checkout using the existing venv
interpreter, the reviewed `--scenario` and `--config` paths. Without `--execute`,
both validation modules only describe the test.

`cosim_smoke.sh` also requires
`AEGIS_APPROVE_LIVE_COSIM=yes`; it advances clocks and changes synchronization
settings for its bounded run. Do not start it without approval and an available
clock owner.

Run local tests with `python -B -m unittest discover -s p2/tests -v`.
They use fakes and fixtures and do not establish live performance.

Run `python -B -m p2.controller_gate` for the current policy compatibility audit.
See [lane mapping status](../docs/lane_mapping.md) for the verified geometry,
camera coverage limits and actual SUMO phase indices. This command never connects
to a simulator or loads a checkpoint into a model.
