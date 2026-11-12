"""Save one real CARLA RGB frame. Requires matching carla package.
Run while CARLA is asynchronous and no co-simulation coordinator is active.
This probe never advances the world itself.
"""
import argparse,queue
from pathlib import Path

def main():
    import carla
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=2000)
    p.add_argument('--output',default='smoke/camera.png');a=p.parse_args()
    c=carla.Client(a.host,a.port);c.set_timeout(30)
    print('client=',c.get_client_version(),'server=',c.get_server_version())
    w=c.get_world()
    if w.get_settings().synchronous_mode:
        raise SystemExit('Use this standalone probe before the synchronous coordinator starts.')
    sp=w.get_map().get_spawn_points()
    if not sp:raise SystemExit('Map has no spawn transforms; choose an explicit camera transform.')
    t=sp[0];t.location.z+=12;t.rotation.pitch=-55
    bp=w.get_blueprint_library().find('sensor.camera.rgb')
    bp.set_attribute('image_size_x','640');bp.set_attribute('image_size_y','360')
    bp.set_attribute('sensor_tick','0.5');bp.set_attribute('fov','90')
    sensor=w.spawn_actor(bp,t);q=queue.Queue(maxsize=2)
    def cb(im):
        try:q.put_nowait(im)
        except queue.Full:pass
    try:
        sensor.listen(cb);im=q.get(timeout=45)
        out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
        im.save_to_disk(str(out));print('Saved frame',im.frame,'at sim time',im.timestamp,'to',out)
        print('Open it and verify it contains the expected rendered scene.')
    finally:sensor.stop();sensor.destroy()
if __name__=='__main__':main()
