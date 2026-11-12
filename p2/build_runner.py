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
    sources={'p2/__init__.py':'','p2/capture_four.py':source,
             'p2/tiled_detector.py':(Path(__file__).parent/'tiled_detector.py').read_text(encoding='utf-8')}
    bundle=base64.b64encode(json.dumps(sources).encode()).decode('ascii')
    wrapper = f'''#!/usr/bin/env bash
# Source SHA256: {hashlib.sha256(source.encode('utf-8')).hexdigest()}
# Config SHA256: {hashlib.sha256(config).hexdigest()}
# Creates four temporary cameras only when explicitly enabled by the operator.
set -eu
if [ "${{AEGIS_APPROVE_FOUR_CAMERA_CAPTURE:-}}" != "yes" ]; then
  printf 'STOP: temporary camera creation and GPU inference require explicit approval.\\n' >&2
  exit 2
fi
timeout --signal=INT --kill-after=30s 180s /workspace/aegis/venv-sim/bin/python -B -u - <<'AEGIS_CAPTURE_PY'
import base64,json,runpy,sys,uuid
from pathlib import Path
root=Path('/workspace/aegis/runtime')/('p2-capture-source-'+uuid.uuid4().hex)
root.mkdir(parents=True,exist_ok=False)
for name,text in json.loads(base64.b64decode('{bundle}')).items():
 path=root/name
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(text,encoding='utf-8')
sys.path.insert(0,str(root))
sys.argv=['p2.capture_four','--execute','--config-base64','{encoded}']
runpy.run_module('p2.capture_four',run_name='__main__')
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
