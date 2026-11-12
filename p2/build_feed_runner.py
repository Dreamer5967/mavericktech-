"""Package P2 source for SSH stdin; does not contact or modify a cloud host."""
import argparse
import ast
import base64
import json
from pathlib import Path
from p2.capture_four import validate_config
from p2.lane_counts import validate_regions


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--duration',type=int,default=600)
    parser.add_argument('--lane-regions',type=Path)
    args=parser.parse_args()
    if not 10<=args.duration<=3600:
        parser.error('Duration must be 10–3600 seconds.')
    config=args.config.read_bytes()
    validate_config(json.loads(config))
    root=Path(__file__).resolve().parent.parent
    names=('p2/__init__.py','p2/capture_four.py','p2/live_feed.py','p2/lane_counts.py','p2/tiled_detector.py')
    sources={name:(root/name).read_text(encoding='utf-8') for name in names}
    for source in sources.values():
        ast.parse(source,feature_version=(3,10))
    bundle=base64.b64encode(json.dumps(sources).encode()).decode()
    encoded=base64.b64encode(config).decode()
    region_bootstrap=''
    region_args=''
    if args.lane_regions:
        regions=args.lane_regions.read_text(encoding='utf-8')
        validate_regions(json.loads(regions),json.loads(config))
        region_bootstrap="(root/'lane_regions.json').write_text("+repr(regions)+",encoding='utf-8')\n"
        region_args=",'--lane-regions',str(root/'lane_regions.json')"
    bootstrap=f'''import base64,json,runpy,sys,uuid
from pathlib import Path
root=Path('/workspace/aegis/runtime')/('p2-feed-source-'+uuid.uuid4().hex)
root.mkdir(parents=True,exist_ok=False)
sources=json.loads(base64.b64decode('{bundle}'))
assert set(sources)==set({names!r})
for name,text in sources.items():
 path=root/name
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(text,encoding='utf-8')
sys.path.insert(0,str(root))
{region_bootstrap}sys.argv=['p2.live_feed','--execute','--config-base64','{encoded}','--duration','{args.duration}','--port','8765'{region_args}]
runpy.run_module('p2.live_feed',run_name='__main__')
'''
    script='#!/usr/bin/env bash\nset -eu\n'
    script+='if [ "${AEGIS_APPROVE_LIVE_CAMERA_FEED:-}" != "yes" ]; then exit 2; fi\n'
    script+=f"timeout --signal=TERM --kill-after=30s {args.duration+60}s /workspace/aegis/venv-sim/bin/python -B -u - <<'AEGIS_FEED'\n"
    script+=bootstrap+'\nAEGIS_FEED\n'
    with args.out.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(script)
    print('Prepared runner:',args.out)


if __name__=='__main__':
    main()
