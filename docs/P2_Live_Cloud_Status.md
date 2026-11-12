# AEGIS P2 - live Vast.ai state and exact setup handoff

## Latest verified additions: 12 November 2026, 07:13 UTC

Continuous-feed addition at 07:30 UTC: a ten-minute four-camera/YOLO worker was
started without simulator ticks or map changes. The read-only API on cloud
loopback port 8765 was tunneled to the laptop. Increasing revisions and actual
JPEGs from all four cameras were verified; sampled image ages were 0.13–0.25
simulation seconds. This is a temporary integration test, not an always-on
deployment. P4's existing dashboard still needs its frame/schema adapter.

- Four angled cameras plus warmed YOLO completed run `p2-smoke-20261112T070404Z-86ad7e08`.
  All observations were fresh at publication (0.523–0.617 simulation seconds old).
  Vehicle detections were 0, 2, 0 and 3 for cam_g1/g3/g4/g5. These include parked-looking
  vehicles and are not lane occupancy or queue measurements. Inter-camera skew was 94 ms.
- With explicit user approval, eclipse-sumo/traci/sumolib 1.20.0 and lxml 5.3.0 were added
  to the existing venv-sim, with hashes and dependency resolution disabled. Version/API
  checks passed and protected CARLA/YOLO/PyTorch/NumPy/OpenCV versions were unchanged.
- Explicit new binaries: `/workspace/aegis/venv-sim/bin/sumo` and `netconvert`.
  New SUMO_HOME: `/workspace/aegis/venv-sim/lib/python3.10/site-packages/sumo`.
  System `/usr/bin/sumo` remains 1.4.0; do not mix its tools with the new binaries.
- The current Town10HD_Opt map was exported and statically converted into
  `/workspace/aegis/maps/town10-map-20261112T071329Z-dff47bc2`.
  Five SUMO signal programs were created. Camera mappings: g1→719, g3→23, g4→189, g5→468,
  with no selected landmark IDs missing. Static conversion found no remaining RGB sensors.
- CARLA was not restarted, maps/settings were not changed, and no live simulation was
  manually stepped. Live synchronization, moving traffic demand, lane calibration and
  continuous publication remain unfinished. See `p2/README.md` for the current source.

The original setup record below is retained as historical evidence.

**As of user-reported console outputs on 12 November 2026, around 05:17 UTC.** This is an evidence-grounded status note, **not** an assertion that the instance is still running at time of reading. Codex must recheck the runtime.

## 1. Hardware / OS confirmed

- Cloud instance: NVIDIA GeForce RTX 3090 Ti, 24,564 MiB VRAM (24 GB class).
- NVIDIA host driver `595.112.07`, `nvidia-smi` reported driver-supported CUDA version `13.2` (this is not proof that the local CUDA toolkit is installed).
- OS: Ubuntu `20.04.6 LTS` / `x86_64`; Python `3.10.13`.
- Total root overlay disk 70 GB; approximately 43 GB was free after CARLA extraction. Recheck before installing anything.
- `NVIDIA_DRIVER_CAPABILITIES=all`.
- Initially NVIDIA Vulkan failed and only `llvmpipe` appeared. After `apt-get install -y --no-install-recommends libegl1`, `vulkaninfo` showed `NVIDIA GeForce RTX 3090 Ti` as `PHYSICAL_DEVICE_TYPE_DISCRETE_GPU` (plus CPU llvmpipe).
- Network connection to Vast from a Windows laptop was verified using SSH. Keys and private connection details are intentionally omitted from this handoff.

## 2. Paths on the actual cloud instance

| Path | Meaning / state |
|---|---|
| `/workspace/aegis/carla/` | Extracted CARLA 0.9.15 server (contains executable `CarlaUE4.sh`) |
| `/workspace/aegis/downloads/CARLA_0.9.15.tar.gz` | Original 8,386,636,048-byte archive; `gzip -t` returned `ARCHIVE OK` |
| `/workspace/aegis/downloads/carla.log` | Server stdout/stderr on launch |
| `/workspace/aegis/venv-sim/` | Python 3.10 virtual environment; CARLA client and Ultralytics/OpenCV dependencies installed |
| `/workspace/aegis/evidence/carla_camera_smoke.png` | 960 x 540 raw CARLA RGB frame, 974,804 bytes at time of test |
| `/workspace/aegis/evidence/carla_camera_smoke_yolo.jpg` | YOLO annotated image, 222,676 bytes at time of test |
| `/workspace/aegis/camera_four_smoke.py` | User was instructed to create and execute this script; creation and execution are **not yet confirmed** |
| `/workspace/aegis/evidence/multicam/observations.json` | Expected output from unverified four-camera script, **not yet confirmed** |
| `/workspace/aegis/repo/` | **Suggested new Git checkout location; not claimed to exist** |

CARLA was launched under existing non-root user `aegisrun`; cloud SSH shell used `root`. Do not change ownership casually. There are no confirmed completed `venv-vqa`, SUMO integration, MARL checkpoint, fault-injection evaluation, or 4-camera JSON results.

## 3. Confirmed run results

1. `gzip -t` on the official CARLA 0.9.15 Linux archive returned `ARCHIVE OK`.
2. Extracted successfully with `runuser -u aegisrun -- tar -xzf ...`; extraction log showed `EXTRACTION OK`.
3. CARLA server launched with `-RenderOffScreen -quality-level=Low -carla-port=2000` and NVIDIA Vulkan ICD. `nvidia-smi` showed `CarlaUE4-Linux-Shipping` using ~4.9 GiB VRAM and GPU graphics (`C+G`), not CPU llvmpipe.
4. `/workspace/aegis/venv-sim/bin/python` imported `carla`; `carla.Client('127.0.0.1', 2000)` connected. Server `0.9.15`; world map `Carla/Maps/Town10HD_Opt`; 155 spawn points.
5. Temporary RGB camera captured and saved a valid 960x540 image from CARLA; camera actor was destroyed in `finally`. Frame reported `34538`.
6. Ultralytics `YOLO('yolov10n.pt')` running `model.predict(..., device=0, conf=0.25)` on that image reported **1 car (confidence 0.612)** and **1 person (confidence 0.251)**. Annotated image file was saved.

These are smoke-test observations, **not** traffic-control benchmark values. Per-lane attribution, frame latency, false-positive rate and multi-camera real-time throughput have not been measured.

## 4. Read-only commands to check current instance

These commands run **inside the cloud SSH shell**, not PowerShell:

```bash
nvidia-smi
pgrep -af 'CarlaUE4|UE4Game' || true
ls -lh /workspace/aegis/carla/CarlaUE4.sh
ls -lh /workspace/aegis/evidence/carla_camera_smoke* 2>/dev/null || true
df -h /workspace
/workspace/aegis/venv-sim/bin/python - <<'PY'
import carla
c = carla.Client('127.0.0.1', 2000)
c.set_timeout(10)
w = c.get_world()
print('CARLA server:', c.get_server_version())
print('Map:', w.get_map().name)
print('Synchronous:', w.get_settings().synchronous_mode)
PY
```

To run the included read-only preflight after cloning the repo to `/workspace/aegis/repo`:

```bash
cd /workspace/aegis/repo
bash scripts/p2_check_instance.sh
```

**No clock advancement** in either read-only probe. The `client.get_world()` call just requests current state.

## 5. Documented CARLA launch (ONLY if not running)

Original working command, reproduced for recovery reference. Do **not** paste it while the CARLA server is already running.

```bash
mkdir -p /tmp/runtime-aegisrun
chown aegisrun:aegisrun /tmp/runtime-aegisrun
chmod 700 /tmp/runtime-aegisrun
nohup runuser -u aegisrun -- env \
  XDG_RUNTIME_DIR=/tmp/runtime-aegisrun \
  VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json \
  bash -c '
    cd /workspace/aegis/carla
    exec ./CarlaUE4.sh -RenderOffScreen -quality-level=Low -carla-port=2000
  ' > /workspace/aegis/downloads/carla.log 2>&1 < /dev/null &
```

If CARLA unexpectedly exits, first inspect `/workspace/aegis/downloads/carla.log`; do not blindly restart it or launch a second instance.

## 6. P2 next work, not yet verified

- Verify the supplied four-camera smoke script completes, stores four RGB images and annotated images, and writes `observations.json`. Validate whether camera sites cover four genuinely distinct intersections and whether objects are actually visible. A vehicle count of 0 may be a real empty scene.
- Decide camera transforms and per-lane polygons with P3. Raw whole-image detection counts are **not** lane occupancy or queues.
- Install and validate SUMO/co-simulation example for CARLA 0.9.15, with one clock owner only. Any controller integration comes after the basic synchronized simulator works.
- Add bounded frame/telemetry streaming, dropout/stale flags, measured latency, and evidence logging. Do not fake results or mix mock data with real runs.
- Use `venv-sim` for CARLA client/SUMO tools/YOLO/API and add `venv-vqa` for ViLT/Transformers/Langfuse only when P4/P2 work requires it. **Only two cloud Python environments** planned.
- The 4-team assignment is UNCHANGED: P1 PPT+light coding/tests; P2 cloud/simulation/YOLO; P3 MAPPO+planner+evaluation; P4 dashboard/VQA/security+speech.

## 7. Security and handoff boundaries

- A P2 SSH key pair was created locally on Windows; the **private key must stay on that laptop**. Never upload it to this ZIP, GitHub, or a Codex chat.
- Avoid recording publicly accessible host/port and tokens in a public GitHub repository. Obtain the current Vast SSH command from the instance UI when needed; do not rely on stale ports.
- Codex can help edit files in a VS Code Remote-SSH workspace **after the user has connected the workspace**. Giving Codex a ZIP or key text alone does not grant it access to the server.
- Do not expose CARLA port 2000/2001 publicly. Use an authenticated tunnel for loopback APIs.
- Stop the rented instance in the Vast dashboard when not needed; background SSH process termination alone does not stop billing.
