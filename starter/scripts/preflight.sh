#!/usr/bin/env bash
# Read-only diagnostics. Does not rent, stop or destroy anything.
set -u
printf '\n== OS / user / architecture ==\n'
whoami; uname -m; cat /etc/os-release 2>/dev/null || true
printf '\n== CPU / memory / disk ==\n'
nproc 2>/dev/null || true; free -h 2>/dev/null || true; df -h .
printf '\n== GPU ==\n'
nvidia-smi || true
printf '\n== Vulkan ==\n'
if command -v vulkaninfo >/dev/null; then vulkaninfo --summary 2>&1 | head -70; else echo 'vulkaninfo not installed'; fi
printf '\n== Executables ==\n'
for x in python3 python3.10 git sumo docker tmux; do command -v "$x" || true; done
printf '\n== Two-environment profile ==\n'
AEGIS_ENV_ROOT="${AEGIS_HOME:-/workspace/aegis}"
for AEGIS_ENV_NAME in venv-sim venv-vqa; do
  AEGIS_ENV_PYTHON="$AEGIS_ENV_ROOT/$AEGIS_ENV_NAME/bin/python"
  if [ -x "$AEGIS_ENV_PYTHON" ]; then
    "$AEGIS_ENV_PYTHON" -c 'import sys; print(sys.executable, sys.version.split()[0])'
  else
    printf 'Not created: %s\n' "$AEGIS_ENV_PYTHON"
  fi
done
echo 'A successful nvidia-smi or CUDA import does not validate Vulkan or CARLA RGB rendering.'
printf '\n== Billing ==\nCheck the Vast console manually. This script does not read your balance.\n'
