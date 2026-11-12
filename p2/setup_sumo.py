"""Approved additive SUMO setup only; never starts a simulation or imports CARLA."""
import argparse
import base64
from datetime import datetime, timezone
from importlib import metadata
import importlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid


EXPECTED = {'eclipse-sumo':'1.20.0','traci':'1.20.0','sumolib':'1.20.0','lxml':'5.3.0'}
PROTECTED = ('carla','ultralytics','torch','torchvision','numpy','opencv-python','opencv-python-headless')


def package_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def validate_plan(plan):
    packages=plan['packages']
    if len(packages)!=4 or {row['name']:row['version'] for row in packages}!=EXPECTED:
        raise ValueError('Only the four explicitly approved packages/versions are permitted.')
    for row in packages:
        if not re.fullmatch('[0-9a-f]{64}',row['sha256']):
            raise ValueError('Each package must have a pinned wheel SHA256.')
    return packages


def install(plan):
    packages=validate_plan(plan)
    if os.environ.get('AEGIS_APPROVE_SUMO_PACKAGES')!='yes':
        raise RuntimeError('Explicit package-install approval is required.')
    if sys.version_info[:2]!=(3,10) or platform.system()!='Linux' or platform.machine()!='x86_64':
        raise RuntimeError('This plan targets cloud Python 3.10 / Linux x86_64 only.')
    prefix=Path('/workspace/aegis/venv-sim')
    if Path(sys.prefix).resolve()!=prefix.resolve():
        raise RuntimeError('Refusing to install outside the existing venv-sim.')
    for row in packages:
        current=package_version(row['name'])
        if current is not None and current!=row['version']:
            raise RuntimeError('Existing different version found; will not silently replace '+row['name'])
    if shutil.disk_usage('/workspace/aegis').free < 1024**3:
        raise RuntimeError('Less than 1 GiB free; installation stopped before changes.')
    before={name:package_version(name) for name in PROTECTED}
    identifier=datetime.now(timezone.utc).strftime('sumo-setup-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    output=Path('/workspace/aegis/manifests')/identifier
    output.mkdir(parents=True,exist_ok=False)
    record={'status':'STARTED','protected_versions_before':before,'packages':packages,
            'simulation_started':False,'manual_ticks':False}
    (output/'before.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    requirements=output/'requirements-sumo.txt'
    requirements.write_text('\n'.join(f"{p['name']}=={p['version']} --hash=sha256:{p['sha256']}" for p in packages)+'\n',encoding='utf-8')
    print('SUMO setup manifest:',output,flush=True)
    try:
        subprocess.run([sys.executable,'-m','pip','--isolated','install','--no-deps','--only-binary=:all:',
                        '--require-hashes','--no-cache-dir','--index-url','https://pypi.org/simple',
                        '-r',str(requirements)],check=True,timeout=240)
        importlib.invalidate_caches()
        after={name:package_version(name) for name in PROTECTED}
        record['protected_versions_after']=after
        if before!=after:
            raise RuntimeError('Protected perception package versions changed; inspect before continuing.')
        installed={name:package_version(name) for name in EXPECTED}
        if installed!=EXPECTED:
            raise RuntimeError('Installed package versions do not match the approved plan.')
        import traci
        import sumolib
        from lxml import etree
        if not callable(getattr(traci.trafficlight,'getAllProgramLogics',None)):
            raise RuntimeError('Required TraCI API is still unavailable.')
        logic=traci.trafficlight.Logic('local-api-check',0,0,[],{})
        logic.getPhases()
        logic.getParameters()
        binaries={}
        for name in ('sumo','netconvert'):
            binary=prefix/'bin'/name
            result=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=15,check=True)
            first_line=result.stdout.splitlines()[0]
            if '1.20.0' not in first_line:
                raise RuntimeError('Unexpected native binary version: '+first_line)
            binaries[name]={'path':str(binary),'version_line':first_line}
            print(name+':',first_line,flush=True)
        distribution=metadata.distribution('eclipse-sumo')
        roots=[]
        for file in distribution.files or []:
            if str(file).replace('\\','/').endswith('bin/sumo'):
                candidate=Path(distribution.locate_file(file)).resolve().parent.parent
                if (candidate/'data').is_dir():
                    roots.append(str(candidate))
        record.update(status='INSTALLED_AND_READ_ONLY_PREFLIGHT_PASSED',installed_versions=installed,
                      binaries=binaries,sumo_home_candidates=sorted(set(roots)),
                      traci_module=traci.__file__,sumolib_module=sumolib.__file__,lxml_version=etree.LXML_VERSION)
        print('TraCI getAllProgramLogics, Logic getters and lxml import: PASS',flush=True)
        print('Protected perception package versions: UNCHANGED',flush=True)
        print('SUMO_HOME candidates:',record['sumo_home_candidates'],flush=True)
        return_code=0
    except Exception as exc:
        record.update(status='FAILED_REVIEW_REQUIRED',error=type(exc).__name__+': '+str(exc))
        print('SUMO SETUP FAILED:',record['error'],flush=True)
        return_code=1
    record['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    (output/'result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('SUMO setup result:',output/'result.json',flush=True)
    print('No simulator was started, restarted, loaded or manually stepped.',flush=True)
    return return_code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan-base64',required=True)
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    plan=json.loads(base64.b64decode(args.plan_base64,validate=True))
    validate_plan(plan)
    if not args.install:
        print(json.dumps(plan,indent=2))
        return 0
    return install(plan)


if __name__=='__main__':
    raise SystemExit(main())
