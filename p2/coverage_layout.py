"""Fit bounded overhead camera views to real lane corridors, without cloud contact."""
import argparse
import copy
import json
import math
from pathlib import Path
from p2.runtime_mapping import build


def fit_view(points, margin=0.10):
    candidates=[]
    for yaw in range(0,180,5):
        angle=math.radians(yaw)
        right=(-math.sin(angle),math.cos(angle))
        up=(math.cos(angle),math.sin(angle))
        xs=[p[0]*right[0]+p[1]*right[1] for p in points]
        ys=[p[0]*up[0]+p[1]*up[1] for p in points]
        half=max(max(xs)-min(xs),max(ys)-min(ys))/2
        height=max(30,half/(1-2*margin))
        cx,cy=(max(xs)+min(xs))/2,(max(ys)+min(ys))/2
        candidates.append((height,yaw,cx*right[0]+cy*up[0],cx*right[1]+cy*up[1]))
    height,yaw,x,y=min(candidates)
    if height>75:
        raise ValueError('Lane extent exceeds the bounded overhead camera profile.')
    return {'x':round(x,4),'y':round(y,4),'z':round(height+max(p[2] for p in points),4),
            'pitch':-90,'yaw':yaw,'roll':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--out-config',type=Path,required=True)
    parser.add_argument('--out-regions',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    network=(args.inventory/'Town10HD_Opt.net.xml').read_bytes()
    manifest=read(args.inventory/'map_manifest.json');geometry=read(args.inventory/'lane_geometry.json')
    policy=read(root/'configs/action_mapping.json')
    config=copy.deepcopy(read(root/'p2/camera_sites.oblique.json'))
    previous,_=build(network,manifest,geometry,config,policy)
    for camera,cal in zip(config['cameras'],previous['cameras']):
        camera['transform']=fit_view([p for lane in cal['regions'] for p in lane['ground_polygon_world']])
    config.update(status='OVERHEAD_COVERAGE_CANDIDATE',image_width=1280,image_height=1280,
                  fov=90,inference_imgsz=1280,sensor_tick_s=0.5,confidence=0.2)
    regions,_=build(network,manifest,geometry,config,policy)
    for camera in regions['cameras']:
        if not all(r['geometrically_visible'] for r in camera['regions']):
            raise ValueError('Layout still contains unprojected lanes.')
        print(camera['camera_id'],'projected regions',len(camera['regions']))
        for region in camera['regions']:
            region.pop('ground_polygon_world',None)  # Runtime needs image polygons only.
    for path,data in [(args.out_config,config),(args.out_regions,regions)]:
        with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2);stream.write('\n')


if __name__=='__main__':
    main()
