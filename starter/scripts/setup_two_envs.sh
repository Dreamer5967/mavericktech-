#!/usr/bin/env bash
# Creates two virtual environments only. No rental, package downloads, model
# downloads, service launch, account changes, or billing actions occur here.
set -euo pipefail
AEGIS_ENV_ROOT="${1:-${AEGIS_HOME:-/workspace/aegis}}"
AEGIS_PYTHON_BIN="${AEGIS_PYTHON_BIN:-python3.10}"
if ! command -v "$AEGIS_PYTHON_BIN" >/dev/null 2>&1; then
  echo 'Python 3.10 is required. Select an image with Python 3.10 and its venv support.' >&2
  exit 1
fi
"$AEGIS_PYTHON_BIN" - <<'PY'
import sys
if sys.version_info[:2] != (3, 10):
    raise SystemExit('Expected Python 3.10; do not alias another Python version.')
PY
AEGIS_ENV_ROOT="$("$AEGIS_PYTHON_BIN" -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "$AEGIS_ENV_ROOT")"
mkdir -p "$AEGIS_ENV_ROOT"
for AEGIS_ENV_NAME in venv-sim venv-vqa; do
  AEGIS_ENV_PATH="$AEGIS_ENV_ROOT/$AEGIS_ENV_NAME"
  if [ -e "$AEGIS_ENV_PATH" ]; then
    if [ ! -x "$AEGIS_ENV_PATH/bin/python" ]; then
      echo "Existing path is not a usable environment: $AEGIS_ENV_PATH" >&2
      exit 1
    fi
  else
    "$AEGIS_PYTHON_BIN" -m venv "$AEGIS_ENV_PATH"
  fi
  "$AEGIS_ENV_PATH/bin/python" -c 'import sys; assert sys.version_info[:2] == (3, 10), "Existing environment is not Python 3.10"'
  printf 'Ready: %s/bin/python\n' "$AEGIS_ENV_PATH"
done
echo 'Next: follow CLEAN_COMMANDS.md for PyTorch, dependencies and probes.'
echo 'Keep coordinator, inference and API in separate processes; only the coordinator ticks CARLA.'
