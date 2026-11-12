#!/usr/bin/env bash
# Read-only P2 cloud check. Never starts/stops CARLA or advances simulation ticks.
set -u
printf '\n===== P2 HOST =====\n'
uname -m || true
cat /etc/os-release 2>/dev/null | head -6 || true
printf '\n===== NVIDIA GPU =====\n'
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader 2>&1 || true
printf '\n===== CARLA PROCESSES =====\n'
pgrep -af 'CarlaUE4|UE4Game' || true
printf '\n===== ENVIRONMENT AND LAUNCHER =====\n'
ls -lh /workspace/aegis/carla/CarlaUE4.sh /workspace/aegis/venv-sim/bin/python 2>&1 || true
printf '\n===== EVIDENCE =====\n'
ls -lh /workspace/aegis/evidence/carla_camera_smoke* 2>&1 || true
printf '\n===== DISK =====\n'
df -h /workspace 2>&1 || true
printf '\n===== CARLA CLIENT READ-ONLY CONNECTION =====\n'
if [ -x /workspace/aegis/venv-sim/bin/python ]; then
  timeout 20s /workspace/aegis/venv-sim/bin/python - <<'PY'
try:
    import carla
    c = carla.Client('127.0.0.1', 2000)
    c.set_timeout(8)
    w = c.get_world()
    print('Server:', c.get_server_version())
    print('Map:', w.get_map().name)
    print('Synchronous:', w.get_settings().synchronous_mode)
except Exception as exc:
    print('Client check failed:', type(exc).__name__, str(exc))
PY
else
  echo 'venv-sim Python unavailable'
fi
printf '\n===== P2 CHECK FINISHED (NO CHANGES MADE) =====\n'
