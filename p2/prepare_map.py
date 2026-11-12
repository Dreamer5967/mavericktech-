"""Export the current map and convert static files. Never starts or steps a simulator."""
import argparse
import base64
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET


OFFICIAL_CONVERTER_SHA256='936b3f6a41c23ae8eb12821922ea746fd06cc05e381c863cd3c60f61ccb90b56'


def inventory_network(root):
    lanes={}
    for edge in root.findall('edge'):
        for lane in edge.findall('lane'):
            lanes[(edge.get('id'),lane.get('index'))]=lane.get('id')
    controls=defaultdict(list)
    for connection in root.findall('connection'):
        tls=connection.get('tl')
        if tls:
            controls[tls].append({'link_index':int(connection.get('linkIndex')),
                                 'from_lane_id':lanes.get((connection.get('from'),connection.get('fromLane'))),
                                 'to_lane_id':lanes.get((connection.get('to'),connection.get('toLane')))})
    signals=defaultdict(set)
    programs=[]
    for logic in root.findall('tlLogic'):
        parameters={p.get('key'):p.get('value') for p in logic.findall('param')}
        landmark_ids=sorted(set(value for key,value in parameters.items() if key.startswith('linkSignalID:')))
        for landmark in landmark_ids:
            signals[landmark].add(logic.get('id'))
        programs.append({'tls_id':logic.get('id'),'program_id':logic.get('programID'),
                         'opendrive_signal_ids':landmark_ids,
                         'phases':[{'duration_s':float(p.get('duration')),'state':p.get('state')} for p in logic.findall('phase')],
                         'controlled_links':sorted(controls[logic.get('id')],key=lambda row:row['link_index'])})
    return programs,{key:sorted(value) for key,value in signals.items()}


def prepare(config):
    import carla
    prefix=Path('/workspace/aegis/venv-sim')
    converter=Path('/workspace/aegis/carla/Co-Simulation/Sumo/util/netconvert_carla.py')
    if hashlib.sha256(converter.read_bytes()).hexdigest()!=OFFICIAL_CONVERTER_SHA256:
        raise RuntimeError('Bundled converter differs from the reviewed official 0.9.15 source; stopped.')
    sumo_home=prefix/'lib/python3.10/site-packages/sumo'
    if not (sumo_home/'data').is_dir():
        raise RuntimeError('The approved bundled SUMO data directory is unavailable.')
    client=carla.Client('127.0.0.1',2000)
    client.set_timeout(10)
    if (client.get_client_version(),client.get_server_version())!=('0.9.15','0.9.15'):
        raise RuntimeError('CARLA versions do not match the reviewed profile.')
    world=client.get_world()
    current_map=world.get_map()
    if current_map.name!=config['map']:
        raise RuntimeError('Current map differs from the camera configuration.')
    identifier=datetime.now(timezone.utc).strftime('town10-map-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    output=Path('/workspace/aegis/maps')/identifier
    output.mkdir(parents=True,exist_ok=False)
    print('Static map bundle:',output,flush=True)
    xodr=output/'Town10HD_Opt.xodr'
    network=output/'Town10HD_Opt.net.xml'
    xodr.write_text(current_map.to_opendrive(),encoding='utf-8')
    environment=os.environ.copy()
    environment['SUMO_HOME']=str(sumo_home)
    environment['PATH']=str(prefix/'bin')+os.pathsep+environment.get('PATH','')
    # Do not inherit the old distribution's Python tools through PYTHONPATH.
    environment.pop('PYTHONPATH',None)
    record={'map':current_map.name,'sumo_home':str(sumo_home),'converter_sha256':OFFICIAL_CONVERTER_SHA256,
            'xodr_sha256':hashlib.sha256(xodr.read_bytes()).hexdigest(),
            'simulation_started':False,'manual_ticks':False,'connected_topology_verified':False,
            'coverage_reviewed':False,'traffic_demand_created':False,'errors':[]}
    result_code=1
    try:
        with (output/'netconvert.log').open('x',encoding='utf-8') as log:
            result=subprocess.run([sys.executable,'-B',str(converter),str(xodr),'--output',str(network),'--guess-tls'],
                                  env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=150)
        if result.returncode!=0 or not network.is_file():
            raise RuntimeError('Static converter failed; inspect netconvert.log in the new bundle.')
        programs,signals=inventory_network(ET.parse(network).getroot())
        mapping=[]
        for camera in config['cameras']:
            expected=camera['opendrive_signal_ids']
            ids=sorted(set(tls for signal in expected for tls in signals.get(signal,[])))
            mapping.append({'camera_id':camera['camera_id'],'candidate_group':camera['candidate_group'],
                            'opendrive_signal_ids':expected,'sumo_tls_ids':ids,
                            'missing_signal_ids':[signal for signal in expected if signal not in signals]})
        record.update(status='STATIC_NETWORK_CREATED',network_sha256=hashlib.sha256(network.read_bytes()).hexdigest(),
                      programs=programs,camera_signal_mapping=mapping,
                      active_rgb_sensor_ids=[actor.id for actor in world.get_actors().filter('sensor.camera.rgb')])
        print('Static SUMO traffic-light programs:',len(programs),flush=True)
        for row in mapping:
            print('Mapping:',json.dumps(row),flush=True)
        print('Remaining RGB sensor IDs:',record['active_rgb_sensor_ids'],flush=True)
        result_code=0
    except Exception as exc:
        record.update(status='MAP_PREPARATION_FAILED')
        record['errors'].append(type(exc).__name__+': '+str(exc))
        print('Map preparation failed:',record['errors'][-1],flush=True)
    record['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    (output/'map_manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Map manifest:',output/'map_manifest.json',flush=True)
    print('Existing CARLA map/settings/actors were not changed. No simulation was started or stepped.',flush=True)
    return result_code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config-base64',required=True)
    parser.add_argument('--prepare-static-map',action='store_true')
    args=parser.parse_args()
    config=json.loads(base64.b64decode(args.config_base64,validate=True))
    if not args.prepare_static_map:
        print('Description only: would read current map and write a new static SUMO network bundle.')
        return 0
    return prepare(config)


if __name__=='__main__':
    raise SystemExit(main())
