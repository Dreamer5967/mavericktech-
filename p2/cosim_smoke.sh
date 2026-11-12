#!/usr/bin/env bash
# Bounded fixed-time bridge test. This DOES advance both live simulator clocks.
# Never run without the user's explicit approval for clock advancement.
set -eu
if [ "${AEGIS_APPROVE_LIVE_COSIM:-}" != "yes" ]; then
  printf 'STOP: explicit approval to advance the live CARLA/SUMO clocks is required.\n' >&2
  exit 2
fi
scenario=${1:?Pass the reviewed scenario.sumocfg absolute path}
test -f "$scenario"
prefix=/workspace/aegis/venv-sim
export SUMO_HOME="$prefix/lib/python3.10/site-packages/sumo"
export PATH="$prefix/bin:$PATH"
unset PYTHONPATH
"$prefix/bin/python" -B - <<'PY'
import carla
from importlib import metadata
assert metadata.version('traci') == metadata.version('sumolib') == '1.20.0'
c=carla.Client('127.0.0.1',2000)
c.set_timeout(8)
assert (c.get_client_version(),c.get_server_version()) == ('0.9.15','0.9.15')
w=c.get_world()
assert w.get_map().name == 'Carla/Maps/Town10HD_Opt'
assert not w.get_settings().synchronous_mode, 'An existing synchronous owner may be active.'
assert not list(w.get_actors().filter('sensor.camera.rgb')), 'Stop/review the existing camera worker first.'
print('Approved co-simulation preflight passed. Existing server and map will be reused.',flush=True)
PY
cd /workspace/aegis/carla/Co-Simulation/Sumo
set +e
timeout --signal=INT --kill-after=20s 30s "$prefix/bin/python" -B -u - "$scenario" <<'P2_COMPAT_BRIDGE'
import runpy,sys,traci,sumolib
# Legacy bundled CARLA bridge expects this module attribute. Process-local only.
traci.sumolib=sumolib
scenario=sys.argv[1]
sys.argv=['run_synchronization.py',scenario,'--tls-manager','sumo','--step-length','0.05']
runpy.run_path('run_synchronization.py',run_name='__main__')
P2_COMPAT_BRIDGE
bridge_status=$?
set -e
printf 'Bridge exit status: %s (124 indicates the planned wall-time cutoff; review logs for errors).\n' "$bridge_status"
"$prefix/bin/python" -B - <<'PY'
import carla
c=carla.Client('127.0.0.1',2000)
c.set_timeout(8)
w=c.get_world()
print('Post-test map:',w.get_map().name)
print('Post-test synchronous mode:',w.get_settings().synchronous_mode)
assert not w.get_settings().synchronous_mode, 'Bridge cleanup needs review; do not start a second coordinator.'
PY
if [ "$bridge_status" != 0 ] && [ "$bridge_status" != 124 ]; then exit "$bridge_status"; fi
