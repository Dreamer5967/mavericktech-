#!/usr/bin/env bash
# Collect evidence only; never delete the instance or source data.
set -euo pipefail
OUT="${1:-aegis_evidence.tar.gz}"
items=()
for d in results checkpoints configs manifests presentation; do
  if [ -d "$d" ]; then items+=("$d"); fi
done
if [ "${#items[@]}" -eq 0 ]; then echo 'No evidence folders found. Run from your project root.' >&2; exit 1; fi
tar --exclude='.env' --exclude='*.key' --exclude='*.pem' --exclude='raw_frames' -czf "$OUT" "${items[@]}"
echo "Created $OUT. Check contents for credentials before sharing. Copy off the instance before destruction."
