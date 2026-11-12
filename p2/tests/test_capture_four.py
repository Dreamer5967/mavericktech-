"""Offline failure-path tests. No CARLA, GPU, model, SSH, or SUMO access."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from p2 import capture_four as capture


HERE = Path(__file__).resolve().parent.parent
BASE_CONFIG = json.loads((HERE / 'camera_sites.candidate.json').read_text(encoding='utf-8'))


class Blueprint:
    def set_attribute(self, *args):
        pass


class Sensor:
    def __init__(self, actor_id, mode):
        self.id = actor_id
        self.mode = mode
        self.stopped = False
        self.destroyed = False

    def listen(self, callback):
        if self.mode == 'listen_error':
            raise RuntimeError('injected listen failure')
        if self.mode == 'missing':
            return
        for frame in (100, 101):
            callback(NS(frame=frame, timestamp=1.0 + (frame - 100) * 0.1,
                        width=2, height=2, raw_data=bytes(16)))

    def stop(self):
        self.stopped = True
        if self.mode == 'stop_error':
            raise RuntimeError('injected stop failure')

    def destroy(self):
        self.destroyed = True
        return self.mode != 'destroy_false'


class World:
    def __init__(self, modes=None, synchronous=False, switch_after=None):
        self.modes = modes or ['ok'] * 4
        self.synchronous = synchronous
        self.switch_after = switch_after
        self.owned = []
        self.unrelated = Sensor(9999, 'ok')

    def get_settings(self):
        switched = self.switch_after is not None and len(self.owned) >= self.switch_after
        return NS(synchronous_mode=self.synchronous or switched)

    def get_blueprint_library(self):
        return NS(find=lambda _: Blueprint())

    def spawn_actor(self, blueprint, transform):
        mode = self.modes[len(self.owned)]
        if mode == 'spawn_error':
            raise RuntimeError('injected spawn failure')
        sensor = Sensor(len(self.owned) + 1, mode)
        self.owned.append(sensor)
        return sensor

    def get_map(self):
        return NS(name=BASE_CONFIG['map'])

    def get_actors(self):
        return NS(filter=lambda _: [])

    def get_snapshot(self):
        return NS(timestamp=NS(elapsed_seconds=5.0))


def carla_fake(world):
    client = NS(set_timeout=lambda _: None,
                get_client_version=lambda: '0.9.15', get_server_version=lambda: '0.9.15',
                get_world=lambda: world)
    return NS(Client=lambda *_: client, Location=NS, Rotation=NS,
              Transform=lambda location, rotation: NS(location=location, rotation=rotation))


class Pixels:
    def reshape(self, *args):
        return self

    def __getitem__(self, item):
        return self

    def copy(self):
        return self


class Tensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.value


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(BASE_CONFIG)
        self.config['capture_timeout_s'] = 0.02  # Short unit-test deadline only.

    def collect(self, world):
        with contextlib.redirect_stdout(io.StringIO()):
            return capture.capture_frames(world, carla_fake(world), self.config)

    def test_synchronous_world_rejected_before_any_spawn(self):
        world = World(synchronous=True)
        with self.assertRaises(RuntimeError):
            self.collect(world)
        self.assertEqual(world.owned, [])

    def test_newest_frames_retained_and_only_owned_sensors_cleaned(self):
        world = World()
        shots, errors, cleanup, ids = self.collect(world)
        self.assertEqual(len(shots), 4)
        self.assertTrue(all(shot[0].frame == 101 for shot in shots.values()))
        self.assertEqual(errors, {})
        self.assertEqual(cleanup, [])
        self.assertEqual(ids, [1, 2, 3, 4])
        self.assertTrue(all(s.stopped and s.destroyed for s in world.owned))
        self.assertFalse(world.unrelated.destroyed)

    def test_listen_failure_still_destroys_allocated_sensor(self):
        world = World(['ok', 'listen_error', 'ok', 'ok'])
        shots, errors, _, _ = self.collect(world)
        self.assertEqual(len(shots), 3)
        self.assertIn('cam_g3', errors)
        self.assertTrue(all(s.destroyed for s in world.owned))

    def test_missing_camera_has_bounded_timeout_and_others_survive(self):
        world = World(['ok', 'missing', 'ok', 'ok'])
        shots, errors, _, _ = self.collect(world)
        self.assertEqual(len(shots), 3)
        self.assertEqual(errors['cam_g3'], 'frame_timeout')
        self.assertTrue(all(s.destroyed for s in world.owned))

    def test_mode_change_aborts_further_spawns_and_retains_cleanup_record(self):
        world = World(switch_after=1)
        _, errors, _, ids = self.collect(world)
        self.assertIn('_capture', errors)
        self.assertEqual(ids, [1])
        self.assertTrue(world.owned[0].destroyed)

    def test_stop_failure_does_not_prevent_destruction(self):
        world = World(['stop_error', 'ok', 'ok', 'ok'])
        _, _, issues, _ = self.collect(world)
        self.assertTrue(all(s.destroyed for s in world.owned))
        self.assertEqual(issues[0]['operation'], 'stop')

    def test_failed_destruction_is_reported(self):
        _, _, issues, _ = self.collect(World(['destroy_false', 'ok', 'ok', 'ok']))
        self.assertEqual(issues[0]['operation'], 'destroy')

    def test_stale_timestamp_is_preserved_and_unknown_clock_is_not_fresh(self):
        row = capture.empty_observation('cam_g1')
        row['source_sim_time_s'] = 1.0
        capture.stamp_freshness(row, 5.0, 2.0)
        self.assertTrue(row['stale'])
        self.assertEqual(row['source_sim_time_s'], 1.0)
        capture.stamp_freshness(row, 0.5, 2.0)
        self.assertIsNone(row['stale'])

    def test_default_cli_describes_without_cloud_or_heavy_dependencies(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'capture_four.py'),
                                 '--config', str(HERE / 'camera_sites.candidate.json')],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['cloud_contacted'])

    def test_end_to_end_partial_capture_keeps_missing_count_null(self):
        world = World(['ok', 'missing', 'ok', 'ok'])
        events = []
        spawn = world.spawn_actor

        def tracked_spawn(*args):
            self.assertIn('predict', events, 'Detector must be warmed before any camera is spawned.')
            events.append('spawn')
            return spawn(*args)

        world.spawn_actor = tracked_spawn
        box = NS(xyxy=Tensor([[0.0, 0.0, 1.0, 1.0]]), cls=Tensor([2.0]), conf=Tensor([0.8]))

        def predict(**kwargs):
            events.append('predict')
            return [NS(boxes=box, names={2: 'car'})]

        model = NS(predict=predict)

        def write_image(path, pixels):
            Path(path).write_bytes(b'unit-test-image-placeholder')
            return True

        modules = {
            'carla': carla_fake(world),
            'cv2': NS(imwrite=write_image, rectangle=lambda *_: None, putText=lambda *_: None,
                      FONT_HERSHEY_SIMPLEX=0, LINE_AA=0),
            'numpy': NS(frombuffer=lambda *args, **kwargs: Pixels(), zeros=lambda *args, **kwargs: Pixels(), uint8='uint8'),
            'torch': NS(cuda=NS(is_available=lambda: True, synchronize=lambda: None)),
            'ultralytics': NS(YOLO=lambda _: model, utils=NS(AUTOINSTALL=False, ONLINE=False)),
        }
        with tempfile.TemporaryDirectory(prefix='aegis-p2-test-') as directory:
            root = Path(directory)
            weights = root / 'test.pt'
            weights.write_bytes(b'unit-test-placeholder-not-real-weights')
            self.config['weights_path'] = str(weights)
            with patch.dict(sys.modules, modules), patch.dict(os.environ), contextlib.redirect_stdout(io.StringIO()):
                status = capture.execute(self.config, root / 'evidence')
            self.assertEqual(status, 1)
            files = list((root / 'evidence').glob('*/observations.json'))
            self.assertEqual(len(files), 1)
            document = json.loads(files[0].read_text(encoding='utf-8'))
            self.assertFalse(document['smoke_success'])
            rows = {row['camera_id']: row for row in document['observations']}
            self.assertTrue(rows['cam_g3']['missing'])
            self.assertIsNone(rows['cam_g3']['whole_image_vehicle_count'])
            self.assertIsNone(rows['cam_g3']['detections'])
            self.assertEqual(rows['cam_g1']['whole_image_vehicle_count'], 1)
            self.assertIsNone(rows['cam_g1']['lane_counts'])
            self.assertTrue(rows['cam_g1']['stale'])
            self.assertEqual(document['owned_actor_ids'], [1, 2, 3, 4])
            self.assertFalse(world.unrelated.destroyed)
            self.assertEqual(events[:5],['predict','spawn','spawn','spawn','spawn'])

    def test_detector_warmup_precedes_capture_and_failure_prevents_spawns(self):
        # Use the existing end-to-end test's fake dependency setup through an
        # intercepted warm-up; ordering is asserted at the capture boundary.
        events = []
        world = World()
        real_collect = capture.capture_frames

        def load(*args):
            events.append('warm')
            raise RuntimeError('injected model initialization failure')

        with tempfile.TemporaryDirectory(prefix='aegis-p2-test-') as directory:
            root = Path(directory)
            weights = root/'test.pt'
            weights.write_bytes(b'test-only')
            self.config['weights_path'] = str(weights)
            modules = {'carla':carla_fake(world), 'cv2':NS(), 'numpy':NS()}
            with patch.dict(sys.modules, modules), patch.object(capture,'load_warmed_model',side_effect=load), \
                 patch.object(capture,'capture_frames',wraps=real_collect) as collector, \
                 contextlib.redirect_stdout(io.StringIO()):
                result = capture.execute(self.config,root/'evidence')
            self.assertEqual(result,1)
            collector.assert_not_called()
            self.assertEqual(world.owned,[])
            self.assertEqual(events,['warm'])


if __name__ == '__main__':
    unittest.main()
