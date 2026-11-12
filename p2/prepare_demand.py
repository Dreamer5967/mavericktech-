"""Create deterministic route/config files from the static P2 map; no simulation starts."""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET


def route_candidates(net, mapping, programs):
    program_by_id={row['tls_id']:row for row in programs}
    incoming={}
    for camera in mapping:
        if camera['missing_signal_ids'] or len(camera['sumo_tls_ids'])!=1:
            raise ValueError('Each camera must map to exactly one fully identified signal system.')
        tls=camera['sumo_tls_ids'][0]
        lane_ids=sorted({link['from_lane_id'] for link in program_by_id[tls]['controlled_links']})
        edges={net.getLane(lane).getEdge().getID():net.getLane(lane).getEdge() for lane in lane_ids if lane}
        incoming[tls]=[edge for edge in edges.values() if edge.allows('passenger')]
    routes=[]
    connectivity=[]
    seen=set()
    for source in sorted(incoming):
        for target in sorted(incoming):
            if source==target:
                continue
            found=None
            for start in incoming[source]:
                for finish in incoming[target]:
                    path,cost=net.getShortestPath(start,finish,vClass='passenger')
                    if path and len(path)>=2:
                        found=tuple(edge.getID() for edge in path)
                        break
                if found:
                    break
            connectivity.append({'from_tls':source,'to_tls':target,'path_found':found is not None})
            if found and found not in seen:
                seen.add(found)
                routes.append({'id':'p2_route_'+str(len(routes)+1),'edges':list(found),
                               'from_tls':source,'to_tls':target})
    return routes,connectivity


def prepare(bundle, output_root):
    manifest=json.loads((bundle/'map_manifest.json').read_text(encoding='utf-8'))
    network=bundle/'Town10HD_Opt.net.xml'
    if hashlib.sha256(network.read_bytes()).hexdigest()!=manifest['network_sha256']:
        raise ValueError('Static network hash changed; regenerate/review mapping first.')
    routes,connectivity=xml_route_candidates(ET.parse(network).getroot(),manifest['camera_signal_mapping'],manifest['programs'])
    if not routes or not all(row['path_found'] for row in connectivity):
        raise RuntimeError('Selected signals are not mutually reachable for passenger traffic.')
    run_id=datetime.now(timezone.utc).strftime('town10-demand-%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
    output=output_root/run_id
    output.mkdir(parents=True,exist_ok=False)
    demand=ET.Element('routes')
    ET.SubElement(demand,'vType',id='vehicle.tesla.model3',vClass='passenger',length='4.69',width='1.85',
                  accel='2.6',decel='4.5',sigma='0.5',maxSpeed='13.9',minGap='2.5')
    for route in routes:
        ET.SubElement(demand,'route',id=route['id'],edges=' '.join(route['edges']))
    for index in range(48):
        ET.SubElement(demand,'vehicle',id='p2_vehicle_'+str(index),type='vehicle.tesla.model3',
                      route=routes[index%len(routes)]['id'],depart=str(index*1.5),departLane='best',departSpeed='0')
    route_file=output/'traffic.rou.xml'
    ET.ElementTree(demand).write(route_file,encoding='utf-8',xml_declaration=True)
    cfg=ET.Element('configuration')
    inputs=ET.SubElement(cfg,'input')
    ET.SubElement(inputs,'net-file',value=str(network))
    ET.SubElement(inputs,'route-files',value=route_file.name)
    times=ET.SubElement(cfg,'time')
    ET.SubElement(times,'begin',value='0')
    ET.SubElement(times,'end',value='180')
    ET.SubElement(times,'step-length',value='0.05')
    random=ET.SubElement(cfg,'random_number')
    ET.SubElement(random,'seed',value='42')
    ET.ElementTree(cfg).write(output/'scenario.sumocfg',encoding='utf-8',xml_declaration=True)
    result={'status':'STATIC_DEMAND_PREPARED_NOT_SIMULATED','scenario_file':str(output/'scenario.sumocfg'),
            'network_sha256':manifest['network_sha256'],'routes':routes,'connectivity':connectivity,
            'scheduled_vehicles':48,'seed':42,'simulation_started':False,'manual_ticks':False,
            'phase_safety_reviewed':False,'lane_calibration_complete':False,
            'route_file_sha256':hashlib.sha256(route_file.read_bytes()).hexdigest()}
    (output/'demand_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('STATIC_DEMAND_OUTPUT',output,flush=True)
    print('Passenger routes:',len(routes),'Connected directed signal pairs:',len(connectivity),flush=True)
    print('Scheduled vehicles: 48; seed: 42. Files only; no simulator was started or stepped.',flush=True)
    return result


def xml_route_candidates(root, mapping, programs):
    """Use explicit lane connections, avoiding version-sensitive program parsing."""
    lane_edges={}
    passenger=set()
    for edge in root.findall('edge'):
        if edge.get('function')=='internal':
            continue
        for lane in edge.findall('lane'):
            lane_edges[lane.get('id')]=edge.get('id')
            allowed=lane.get('allow','').split()
            denied=lane.get('disallow','').split()
            if (not allowed or 'all' in allowed or 'passenger' in allowed) and not {'all','passenger'}.intersection(denied):
                passenger.add((edge.get('id'),lane.get('index')))
    graph={edge:set() for edge,_ in passenger}
    for link in root.findall('connection'):
        if (link.get('from'),link.get('fromLane')) in passenger and (link.get('to'),link.get('toLane')) in passenger:
            graph[link.get('from')].add(link.get('to'))
    programs={row['tls_id']:row for row in programs}
    incoming={}
    for row in mapping:
        if row['missing_signal_ids'] or len(row['sumo_tls_ids'])!=1:
            raise ValueError('Incomplete camera/signal mapping.')
        tls=row['sumo_tls_ids'][0]
        incoming[tls]=sorted({lane_edges[link['from_lane_id']] for link in programs[tls]['controlled_links']
                              if link['from_lane_id'] in lane_edges and lane_edges[link['from_lane_id']] in graph})
    routes=[]
    connectivity=[]
    seen=set()
    for source in sorted(incoming):
        for target in sorted(incoming):
            if source==target:
                continue
            found=None
            for start in incoming[source]:
                queue=deque([(start,[start])]);visited={start}
                while queue and found is None:
                    current,path=queue.popleft()
                    if current in incoming[target] and len(path)>1:
                        found=tuple(path);break
                    for neighbor in sorted(graph[current]):
                        if neighbor not in visited:
                            visited.add(neighbor);queue.append((neighbor,path+[neighbor]))
                if found:
                    break
            connectivity.append({'from_tls':source,'to_tls':target,'path_found':found is not None})
            if found and found not in seen:
                seen.add(found)
                routes.append({'id':'p2_route_'+str(len(routes)+1),'edges':list(found),'from_tls':source,'to_tls':target})
    return routes,connectivity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-bundle',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,default=Path('/workspace/aegis/scenarios'))
    args=parser.parse_args()
    prepare(args.map_bundle,args.output_root)


if __name__=='__main__':
    main()
