"""Build a self-contained SSH-stdin runner locally; does not contact the cloud."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path

from p2.capture_four import validate_config


def build(config_path, output):
    source = (Path(__file__).parent/'capture_four.py').read_text(encoding='utf-8')
    config = config_path.read_bytes()
    validate_config(json.loads(config))
    ast.parse(source, feature_version=(3,10))
    encoded = base64.b64encode(config).decode('ascii')
    wrapper = f'''#!/usr/bin/env bash
# Source SHA256: {hashlib.sha256(source.encode('utf-8')).hexdigest()}
# Config SHA256: {hashlib.sha256(config).hexdigest()}
# Creates four temporary cameras only when explicitly enabled by the operator.
set -eu
if [ "${{AEGIS_APPROVE_FOUR_CAMERA_CAPTURE:-}}" != "yes" ]; then
  printf 'STOP: temporary camera creation and GPU inference require explicit approval.\\n' >&2
  exit 2
fi
timeout --signal=INT --kill-after=30s 180s /workspace/aegis/venv-sim/bin/python -B -u - --execute --config-base64 '{encoded}' <<'AEGIS_CAPTURE_PY'
{source}
AEGIS_CAPTURE_PY
'''
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(wrapper)
    print('Prepared runner:',output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    build(args.config,args.out)


if __name__=='__main__':
    main()
