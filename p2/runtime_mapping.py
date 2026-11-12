"""Build lane geometry and signal inventories offline from verified map evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from p2.lane_calibration import project_polygon
from p2.prepare_map import inventory_network


def along(points, distance):
    for a, b in zip(points, points[1:]):
        length = math.dist(a, b)
        if distance <= length and length:
            return [a[i] + (b[i] - a[i]) * distance / length for i in range(2)]
        distance -= length
    return list(points[-1])


def nearest_distance(points, target):
    walked = 0.0
    best = (float('inf'), 0.0)
    for a, b in zip(points, points[1:]):
        delta = [b[i] - a[i] for i in range(2)]
        length = math.dist(a, b)
        if not length:
            continue
        t = max(0, min(1, sum((target[i] - a[i]) * delta[i] for i in range(2)) / length**2))
        gap = math.dist(target, [a[i] + t * delta[i] for i in range(2)])
        best = min(best, (gap, walked + t * length))
        walked += length
    return best


def corridor(points, stop, width):
    gap, end = nearest_distance(points, [stop['x'], stop['y']])
    if gap > 1:
        raise ValueError('CARLA stop point is more than 1m from the mapped SUMO lane.')
    start = max(0, end - 25)
    distances = [start + i for i in range(int(end - start) + 1)] + [end]
    centers = [along(points, d) for d in distances]
    left, right = [], []
    for index, point in enumerate(centers):
        a, b = centers[max(0, index - 1)], centers[min(len(centers) - 1, index + 1)]
        length = math.dist(a, b)
        if length < 1e-6:
            continue
        normal = [-(b[1] - a[1]) / length, (b[0] - a[0]) / length]
        left.append([point[0] + width / 2 * normal[0], point[1] + width / 2 * normal[1], stop['z'] + 0.05])
        right.append([point[0] - width / 2 * normal[0], point[1] - width / 2 * normal[1], stop['z'] + 0.05])
    return left + right[::-1], gap, end - start


def area(polygon):
    return abs(sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2 if polygon else 0


def build(network, manifest, geometry, cameras, policy):
    network_hash = hashlib.sha256(network).hexdigest()
    if network_hash != manifest['network_sha256'] or geometry['live_xodr_sha256'] != manifest['xodr_sha256']:
        raise ValueError('Network or live-map hash mismatch; calibration stopped.')
    if manifest['map'] != cameras['map'] or geometry['map'] != cameras['map']:
        raise ValueError('Map name mismatch.')
    root = ET.fromstring(network)
    offset = list(map(float, root.find('location').get('netOffset').split(',')))
    programs, _ = inventory_network(root)
    by_tls = {p['tls_id']: p for p in programs}
    lane_elements = {l.get('id'): l for e in root.findall('edge') for l in e.findall('lane')}
    by_camera = {c['camera_id']: c for c in geometry['cameras']}
    calibration = {'schema_version': 'aegis.lane-regions.v1', 'map': cameras['map'],
        'network_sha256': network_hash, 'xodr_sha256': manifest['xodr_sha256'],
        'camera_config_sha256': hashlib.sha256(json.dumps(cameras, sort_keys=True).encode()).hexdigest(),
        'status': 'GEOMETRY_VALIDATED_COVERAGE_UNREVIEWED', 'can_publish_lane_counts': False,
        'limitations': ['Ground plane uses the CARLA stop-point height.',
                         'Polygon projection does not establish visibility through occluders.',
                         'ROI vehicle occupancy is not stopped-queue length.'], 'cameras': []}
    runtime = {'schema_version': 'aegis.runtime-mapping.v1', 'map': cameras['map'],
        'network_sha256': network_hash,
        'programs': [by_tls[str(j['sumo_tls_id'])] for j in policy['junctions']],
        'policy_action_semantics_reviewed': False, 'actuation_permitted': False, 'junctions': []}
    for junction in policy['junctions']:
        camera = next(c for c in cameras['cameras'] if c['camera_id'] == junction['camera_id'])
        program = by_tls[str(junction['sumo_tls_id'])]
        incoming = sorted({link['from_lane_id'] for link in program['controlled_links']})
        regions = []
        for source in by_camera[camera['camera_id']]['lanes']:
            if not source['matched'] or not source['samples']:
                raise ValueError('Missing matched CARLA stop-lane geometry.')
            origin = f"{source['road_id']}_{source['lane_id']}"
            matches = [lid for lid in incoming if origin in ' '.join(
                p.get('value', '') for p in lane_elements[lid].findall("param[@key='origId']")).split()]
            if len(matches) != 1:
                raise ValueError('Stop lane does not map uniquely to a controlled SUMO incoming lane: ' + origin)
            lane_id = matches[0]
            points = [[float(pair.split(',')[0]) - offset[0],
                       -(float(pair.split(',')[1]) - offset[1])]
                      for pair in lane_elements[lane_id].get('shape').split()]
            stop = source['samples'][0]
            ground, gap, length = corridor(points, stop, stop['width_m'])
            polygon = project_polygon(ground, camera['transform'], cameras['image_width'],
                                      cameras['image_height'], cameras['fov'])
            regions.append({'lane_id': lane_id, 'opendrive_road_id': source['road_id'],
                'opendrive_lane_id': source['lane_id'], 'mapping_verified': True,
                'stop_to_centerline_error_m': round(gap, 4), 'upstream_region_m': round(length, 2),
                'width_m': stop['width_m'], 'polygon_pixels': polygon,
                'ground_polygon_world': ground,
                'projected_area_pixels': round(area(polygon), 2),
                'geometrically_visible': area(polygon) >= 100,
                'coverage_reviewed': False, 'occlusion_reviewed': False, 'usable_for_counts': False})
        if {r['lane_id'] for r in regions} != set(incoming):
            raise ValueError('Stop geometry does not cover the full incoming lane inventory.')
        calibration['cameras'].append({'camera_id': camera['camera_id'], 'junction_id': junction['alias'],
            'sumo_tls_id': program['tls_id'], 'regions': regions})
        green = []
        for index, phase in enumerate(program['phases']):
            state = phase['state']
            if not any(c in state for c in 'gG') or any(c in state for c in 'yY'):
                continue
            served = sorted({link['from_lane_id'] for link in program['controlled_links']
                             if state[link['link_index']] in 'gG'})
            green.append({'sumo_phase_index': index, 'state': state, 'served_lane_ids': served})
        runtime['junctions'].append({'alias': junction['alias'], 'camera_id': camera['camera_id'],
            'sumo_tls_id': program['tls_id'], 'incoming_lane_ids': incoming, 'green_phases': green,
            'model_lane_slots': 4, 'model_action_slots': junction['num_phases'],
            'policy_lane_slot_mapping': None, 'policy_action_phase_mapping': None,
            'ready_for_live_policy': False})
    return calibration, runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    calibration, runtime = build((args.inventory / 'Town10HD_Opt.net.xml').read_bytes(),
        read(args.inventory / 'map_manifest.json'), read(args.inventory / 'lane_geometry.json'),
        read(repository / 'p2/camera_sites.oblique.json'), read(repository / 'configs/action_mapping.json'))
    args.out.mkdir(parents=True, exist_ok=False)
    for name, value in [('lane_regions.json', calibration), ('runtime_mapping.json', runtime)]:
        (args.out / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    for camera in calibration['cameras']:
        print(camera['camera_id'], 'mapped lanes', len(camera['regions']), 'projected visible',
              sum(r['geometrically_visible'] for r in camera['regions']))


if __name__ == '__main__':
    main()
