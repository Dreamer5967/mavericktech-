"""Build an SSH-streamed bounded MAPPO policy runner.

The generated shell file is a local artifact. It carries source and an external
checkpoint to a unique remote runtime directory, never to Git.
"""
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
SOURCE_FILES=(
    'p2/__init__.py','p2/capture_four.py','p2/live_feed.py','p2/lane_counts.py',
    'p2/tiled_detector.py','p2/controller_gate.py','p2/bridge_validation.py',
    'p2/validate_pipeline.py','services/control/contracts.py',
    'services/control/estimator.py','services/control/inference_entrypoint.py',
    'services/control/live_proposals.py','services/planner/candidates.py',
    'services/planner/coordinator.py','services/planner/rollout_worker.py',
    'training/__init__.py','training/mappo/__init__.py','training/mappo/actor.py',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=ROOT/'p2/camera_sites.coverage.json')
    parser.add_argument('--lane-regions',type=Path,default=ROOT/'configs/lane_regions.coverage.json')
    parser.add_argument('--scenario',type=Path,required=True,
                        help='Existing remote scenario path; it is never copied or changed.')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=30)
    parser.add_argument('--enable-policy',action='store_true',
                        help='Generate a bounded learned-policy actuation test runner.')
    args=parser.parse_args()
    if not args.checkpoint.is_file():parser.error('Verified external checkpoint is required.')
    if not 1<=args.seconds<=30:parser.error('Bounded run must be 1–30 seconds.')
    if args.out.exists():parser.error('Refusing to overwrite an existing runner.')
    sources={name:(ROOT/name).read_text(encoding='utf-8') for name in SOURCE_FILES}
    files={**sources,'camera_config.json':args.config.read_text(encoding='utf-8'),
           'lane_regions.json':args.lane_regions.read_text(encoding='utf-8'),
           'action_mapping.json':(ROOT/'configs/action_mapping.json').read_text(encoding='utf-8'),
           'observation_schema.json':(ROOT/'configs/observation_schema.json').read_text(encoding='utf-8'),
           'runtime_mapping.json':(ROOT/'configs/runtime_mapping.json').read_text(encoding='utf-8')}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    provenance={'commit':commit,'source_sha256':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()},
                'mode':'bounded_mappo_cosim_test' if args.enable_policy else 'fixed_time_cosim_with_read_only_camera_policy_proposals'}
    encoded_files=base64.b64encode(json.dumps(files).encode()).decode()
    encoded_model=base64.b64encode(args.checkpoint.read_bytes()).decode()
    sha=digest(args.checkpoint)
    remote_scenario=str(args.scenario).replace('\\','/')
    bootstrap=f'''import base64,hashlib,io,json,runpy,sys,tarfile,uuid
from pathlib import Path
root=Path('/workspace/aegis/runtime')/('p2-policy-diagnostics-'+uuid.uuid4().hex)
root.mkdir(parents=True,exist_ok=False)
files=json.loads(base64.b64decode('{encoded_files}'))
for name,text in files.items():
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
for name in ('action_mapping.json','observation_schema.json','runtime_mapping.json'):
 target=root/'configs'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(files[name],encoding='utf-8')
model_dir=Path('/workspace/aegis/models');model_dir.mkdir(parents=True,exist_ok=True)
checkpoint=model_dir/('mappo-'+'{sha}'+'.pt')
if not checkpoint.exists():checkpoint.write_bytes(base64.b64decode('{encoded_model}'))
if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!='{sha}':raise RuntimeError('External checkpoint hash mismatch.')
provenance={json.dumps(provenance)}
(root/'source_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
sys.path.insert(0,str(root))
output=Path('/workspace/aegis/evidence/pipeline-validation')/root.name
output.mkdir(parents=True,exist_ok=False)
(output/'source_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
sys.argv=['p2.validate_pipeline','--execute','--seconds','{args.seconds}','--config',str(root/'camera_config.json'),'--lane-regions',str(root/'lane_regions.json'),'--scenario',{remote_scenario!r},'--output-root',str(output),'--policy-checkpoint',str(checkpoint),'--policy-sha256','{sha}']+({['--enable-policy']!r} if {args.enable_policy!r} else [])
try:runpy.run_module('p2.validate_pipeline',run_name='__main__')
finally:
 buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
  for path in output.rglob('*'):
   if path.is_file():archive.add(path,arcname=str(path.relative_to(output)))
 print('AEGIS_EVIDENCE_B64 '+base64.b64encode(buffer.getvalue()).decode(),flush=True)
'''
    script='#!/usr/bin/env bash\nset -eu\n'
    script+='export SUMO_HOME=/workspace/aegis/venv-sim/lib/python3.10/site-packages/sumo\n'
    script+='export PATH=/workspace/aegis/venv-sim/bin:$PATH\nunset PYTHONPATH\n'
    script+='if [ "${AEGIS_APPROVE_LIVE_COSIM:-}" != "yes" ]; then exit 2; fi\n'
    if args.enable_policy:
        script+='if [ "${AEGIS_APPROVE_LEARNED_POLICY:-}" != "yes" ]; then exit 3; fi\n'
    script+=f"timeout --signal=INT --kill-after=30s {args.seconds+120}s /workspace/aegis/venv-sim/bin/python -B -u - <<'AEGIS_POLICY'\n{bootstrap}\nAEGIS_POLICY\n"
    args.out.write_text(script,encoding='utf-8',newline='\n')
    print('Prepared read-only policy diagnostics runner:',args.out)


if __name__=='__main__':main()
