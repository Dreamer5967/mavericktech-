"""Draft observation-only handoff for P3/P4; saved captures are always REPLAY."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path


ROOT_FIELDS = {'schema_version','mode','source_mode','source_run_id','state_revision',
               'source_published_at_utc','as_of_sim_time_s','generated_at_utc',
               'ready_for_live_policy','stale_after_sim_s','cameras'}
CAMERA_FIELDS = {'camera_id','frame_id','observed_at_sim_s','age_sim_s','missing','stale',
                 'status','observed_vehicle_count','lane_counts','queue_estimate'}


def finite_nonnegative(value):
    return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value) and value >= 0


def validate_snapshot(snapshot):
    if set(snapshot) != ROOT_FIELDS:
        raise ValueError('Unexpected or missing snapshot fields; simulator truth/control data is forbidden.')
    if snapshot['schema_version'] != 'aegis.p2.camera-observations.v1-draft' or snapshot['mode'] != 'REPLAY':
        raise ValueError('This adapter only publishes explicitly labeled recorded data.')
    if snapshot['ready_for_live_policy'] is not False:
        raise ValueError('Recorded uncalibrated frames are not ready for live control.')
    if not finite_nonnegative(snapshot['as_of_sim_time_s']):
        raise ValueError('Invalid simulation clock.')
    if not finite_nonnegative(snapshot['stale_after_sim_s']):
        raise ValueError('Invalid stale threshold.')
    if snapshot['source_mode'] != 'LIVE':
        raise ValueError('Expected provenance from a real capture, not fixture measurements.')
    for name in ('generated_at_utc','source_published_at_utc'):
        parsed = datetime.fromisoformat(snapshot[name])
        if parsed.tzinfo is None:
            raise ValueError('Wall timestamps must have a timezone.')
    if not isinstance(snapshot['source_run_id'],str) or not snapshot['source_run_id']:
        raise ValueError('Source run ID is required.')
    revision = snapshot['state_revision']
    if isinstance(revision,bool) or not isinstance(revision,int) or revision < 1:
        raise ValueError('Invalid revision.')
    if not isinstance(snapshot['cameras'],list) or not snapshot['cameras']:
        raise ValueError('Camera observations are required.')
    seen = set()
    for row in snapshot['cameras']:
        if set(row) != CAMERA_FIELDS:
            raise ValueError('Unexpected camera field; policy-boundary fields are allowlisted.')
        if not isinstance(row['camera_id'],str) or not row['camera_id'] or row['camera_id'] in seen:
            raise ValueError('Camera IDs must be nonempty and unique.')
        seen.add(row['camera_id'])
        if not isinstance(row['missing'],bool) or (row['stale'] is not None and not isinstance(row['stale'],bool)):
            raise ValueError('Invalid availability flags.')
        for field in ('observed_at_sim_s','age_sim_s'):
            if row[field] is not None and not finite_nonnegative(row[field]):
                raise ValueError('Invalid observation time/age.')
        captured = row['observed_at_sim_s']
        expected_age = snapshot['as_of_sim_time_s']-captured if captured is not None and captured <= snapshot['as_of_sim_time_s'] else None
        if (expected_age is None) != (row['age_sim_s'] is None):
            raise ValueError('Observation age is inconsistent with source time.')
        if expected_age is not None and not math.isclose(expected_age,row['age_sim_s'],abs_tol=1e-6):
            raise ValueError('Observation age is inconsistent with source time.')
        expected_stale = expected_age > snapshot['stale_after_sim_s'] if expected_age is not None else None
        if row['stale'] is not expected_stale:
            raise ValueError('Stale flag does not match observation age.')
        frame_id = row['frame_id']
        if frame_id is not None and (isinstance(frame_id,bool) or not isinstance(frame_id,int) or frame_id < 0):
            raise ValueError('Invalid frame ID.')
        count = row['observed_vehicle_count']
        if count is not None and (isinstance(count,bool) or not isinstance(count,int) or count < 0):
            raise ValueError('Vehicle count must be an integer or null.')
        if row['status'] not in {'missing','detector_error','clock_unknown','stale','recorded'}:
            raise ValueError('Invalid camera status.')
        if row['status'] != 'recorded' and count is not None:
            raise ValueError('Unavailable, failed, or stale measurements must have a null count.')
        if (row['missing'] or row['stale'] is not False) and count is not None:
            raise ValueError('Missing/stale/unknown observations cannot imply an empty lane.')
        if row['missing'] != (row['status']=='missing'):
            raise ValueError('Availability status is inconsistent.')
        if row['status']=='recorded' and (count is None or frame_id is None):
            raise ValueError('A recorded usable measurement requires a count and frame ID.')
        if row['lane_counts'] is not None or row['queue_estimate'] is not None:
            raise ValueError('No calibrated lane counts or P3 queue estimates exist in this adapter.')
    return snapshot


def build_snapshot(manifest):
    sim_now = manifest['published_sim_time_s']
    if not finite_nonnegative(sim_now):
        raise ValueError('Source publication time is invalid.')
    threshold = manifest['camera_config']['stale_after_sim_s']
    if not finite_nonnegative(threshold):
        raise ValueError('Invalid stale threshold.')
    cameras = []
    for original in manifest['observations']:
        captured = original['source_sim_time_s']
        if captured is not None and not finite_nonnegative(captured):
            raise ValueError('Invalid source capture timestamp.')
        age = sim_now-captured if captured is not None and captured <= sim_now else None
        stale = age > threshold if age is not None else None
        missing = original['missing']
        status = ('missing' if missing else 'detector_error' if original['status'] != 'detected'
                  else 'clock_unknown' if age is None else 'stale' if stale else 'recorded')
        cameras.append({'camera_id':original['camera_id'],'frame_id':original['frame_id'],
                        'observed_at_sim_s':captured,'age_sim_s':age,'missing':missing,'stale':stale,
                        'status':status,'observed_vehicle_count':original['whole_image_vehicle_count'] if status=='recorded' else None,
                        'lane_counts':None,'queue_estimate':None})
    snapshot = {'schema_version':'aegis.p2.camera-observations.v1-draft','mode':'REPLAY',
                'source_mode':manifest['mode'],'source_run_id':manifest['run_id'],'state_revision':1,
                'source_published_at_utc':manifest['published_at_utc'],'as_of_sim_time_s':sim_now,
                'generated_at_utc':datetime.now(timezone.utc).isoformat(),
                'ready_for_live_policy':False,'stale_after_sim_s':threshold,'cameras':cameras}
    return validate_snapshot(snapshot)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    snapshot=build_snapshot(json.loads(args.manifest.read_text(encoding='utf-8')))
    with args.out.open('x',encoding='utf-8') as stream:
        json.dump(snapshot,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print('Recorded observation-only handoff:',args.out)


if __name__=='__main__':
    main()
