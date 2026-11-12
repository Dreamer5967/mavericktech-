# Person 2 source

## Current evidence

Latest verified run: `p2-smoke-20261112T070404Z-86ad7e08`. Angled cameras and
detector warm-up before capture reduced publication age to 0.523–0.617 simulation
seconds; all four observations were fresh under the two-second threshold. YOLO
reported two cars in cam_g3 and three in cam_g5. Visual review confirmed car boxes
on parked-looking vehicles but also found missed cars; lane queues remain null.
The views differ by up to 0.094058 simulation seconds. The run reported no cleanup
errors, and subsequent map preparation found zero remaining RGB sensors.

On 12 November 2026, the live Town10HD_Opt run produced four distinct 960x540
images at CARLA frame 525290 and simulation time 5521.550834 s. All image hashes
matched after download. The run reported no cleanup errors for owned sensors
25–28. It did not establish continuous synchronization or SUMO integration.

YOLO detected no vehicles despite one visible parked-looking car in cam_g3 and
three in cam_g5. Single images do not establish motion or static/dynamic actor
status. Tree canopy partly obscures cam_g4. Lane counts and queue estimates
remain unavailable.

Publication age was 5.277667 simulation seconds, exceeding the 2-second limit.
The first prediction call took 2638 ms; later calls took 17–19 ms. The original
pipeline loaded the detector after capture. The current code loads and warms it
before creating any sensors, and measures initialization, capture/cleanup,
encoding, and receive-to-inference delay separately. The latest live run above
verified the improvement in observation age; total process startup still includes
the detector warm-up.

A local CPU replay used an official checkpoint with exactly the same SHA256 as
the cloud model. Five profiles (640/960/1280 input, 180-degree rotation, and
overlapping crops) still detected no vehicles. Local Ultralytics 8.4.60 and
PyTorch 2.12.0+cpu differ from the cloud runtime, so this is a diagnostic rather
than a controlled accuracy comparison or GPU benchmark. Confidence stayed 0.25.

## Tools

- `live_feed.py`: continuous four-camera/YOLO worker and read-only loopback frame
  adapter. The first ten-minute cloud test exposed /health, /api/v1/snapshot,
  /api/v1/frames/{id} and /api/v1/events through an authenticated SSH tunnel.
  Four actual JPEG fetches and increasing revisions were verified, with sampled
  source ages 0.13–0.25 simulation seconds. This does not complete P4's frontend
  integration: their viewer still needs image loading and a nullable schema adapter.
  Start from a cloud checkout with `venv-sim/bin/python -m p2.live_feed --config
  p2/camera_sites.oblique.json --execute --duration 600`. Use the absolute existing
  venv interpreter, bind only loopback, and forward port 8765 through SSH. The
  process expires after the chosen duration and attempts owned-sensor cleanup.
  Stop this standalone asynchronous worker before introducing a synchronous
  coordinator; it never takes ownership of the simulation clock.
- `capture_four.py`: requires `--execute`; otherwise describes configuration
  without cloud contact. Refuses synchronous worlds, unexpected maps/versions,
  missing weights, unavailable CUDA, and pre-existing RGB sensors. Retains one
  latest image per owned sensor, bounds waiting, and records cleanup failures.
- `camera_sites.candidate.json`: original overhead smoke positions.
- `camera_sites.oblique.json`: unreviewed 9–12 m angled approach positions with
  an 80-degree field of view. These cover partial approaches, not all lanes.
- `replay_compare.py`: CPU comparison on hash-verified saved images; no CARLA or
  TraCI connection. Checkpoint download and package auto-install are disabled.
- `observations.py`: produces an allowlisted observation-only JSON handoff for
  P3/P4. Saved data is always `REPLAY`, never made fresh by changing wall time.
- `build_runner.py`: packages the capture source and config into a Bash runner
  that can be streamed over SSH without copying source into the simulator tree.

Examples from the repository root (replace the paths with your actual local files):

```powershell
py -3.14 -B -m p2.capture_four --config p2/camera_sites.oblique.json
py -3.14 -B -m p2.replay_compare --run-dir C:/path/to/saved-run --weights C:/path/to/yolov10n.pt --output-root C:/path/to/replays
py -3.14 -B -m p2.observations --manifest C:/path/to/saved-run/observations.json --out C:/path/to/snapshot.replay.json
py -3.14 -B -m p2.build_runner --config p2/camera_sites.oblique.json --out C:/path/to/run_capture_oblique.sh
```

The runner requires `AEGIS_APPROVE_FOUR_CAMERA_CAPTURE=yes`. It never calls a
simulator tick, changes world settings, loads a map, starts SUMO, or installs a
package. It does create temporary camera actors, use the GPU, and write a new
evidence run. Cleanup is attempted only for its own actors; interrupted/network
failure cases still require checking for reported cleanup issues before retrying.
Do not run it without authorization to perform that bounded live test.

## Draft P3/P4 interface

`aegis.p2.camera-observations.v1-draft` is a proposal, not a replacement for the
shared API contract. P3 owns estimation/control; P4 owns the application/API.
Existing endpoint names in `docs/API_and_Data_Contracts.md` stay unchanged.

The replay snapshot carries the run ID, original simulation and wall timestamps,
camera/frame IDs, recomputed age, stale/missing flags, and nullable whole-image
vehicle counts. A stale/failed/missing observation has a null usable count.
Lane counts and queue estimates are always null until their real implementations
exist. No simulator truth or control proposals are allowed through the validator.
`ready_for_live_policy` is false. Continuous publication and a jointly agreed
production schema remain to be implemented.

## SUMO gate

Static demand is now prepared at
`/workspace/aegis/scenarios/town10-demand-20261112T080350Z-bacdddb4/scenario.sumocfg`.
It contains 12 passenger routes between all 12 directed pairs of the selected
four signal systems and 48 scheduled vehicles with seed 42. These are generated
scenario inputs, not simulated or evaluated traffic results. `prepare_demand.py`
checks network hashes and lane permissions without starting a simulator.

`cosim_smoke.sh` is a prepared 30-second fixed-time bridge test. It is blocked
unless `AEGIS_APPROVE_LIVE_COSIM=yes`; it changes synchronization settings and
advances the live clocks. It has NOT been executed. It reuses the existing CARLA
server/map and refuses an existing synchronous owner or active RGB sensors.

The original system SUMO 1.4.0 remains at /usr/bin. With explicit user approval,
eclipse-sumo/traci/sumolib 1.20.0 and lxml 5.3.0 were added to the existing venv-sim
using pinned hashes and --no-deps. Native version checks, required TraCI API/Logic
getters and lxml import passed. Protected perception package versions were unchanged.
Use the explicit venv-sim/bin/sumo and netconvert executables; do not mix them with
the old /usr/share/sumo/tools modules. The new SUMO_HOME is
`/workspace/aegis/venv-sim/lib/python3.10/site-packages/sumo`.

The current map was exported and converted with the hash-verified official CARLA
0.9.15 static converter. Bundle:
`/workspace/aegis/maps/town10-map-20261112T071329Z-dff47bc2`.
Five SUMO traffic-light programs were created. All selected camera landmarks map
without missing IDs: cam_g1→719, cam_g3→23, cam_g4→189, cam_g5→468.

Before starting a bridge: review network connectivity and phase paths, add demand,
and run a bounded synchronized test. No live co-simulation has run. P2 remains the
only live clock owner. Bridge starts and live clock advancement still require the
user's explicit go-ahead.

## Verification

The higher-rate MJPEG experiment was not validated through the SSH transport;
the connection timed out. It was retained locally outside the published source.
The published feed retains the verified JPEG/telemetry approach. No high-FPS
delivery or browser-rendering rate is claimed.

Tests use local fakes and temporary fixtures, never the cloud. They cover bounded
capture, owned-actor cleanup, failure before sensor creation, detector warm-up
ordering, missing/stale counts, timestamp preservation, simulator-truth rejection,
crop coordinates, and duplicate suppression. Do not populate benchmark CSVs from
these tests or the four-image replay.
