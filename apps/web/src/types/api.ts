export type ConnectionStatus = 'CONNECTED' | 'STALE' | 'DISCONNECTED';

export type OperatingMode = 'MOCK' | 'LIVE' | 'REPLAY' | 'RESETTING' | string;

export type CameraStatus = 'AVAILABLE' | 'MISSING' | string;

export type JunctionId = 'J1' | 'J2' | 'J3' | 'J4';

export interface JunctionData {
  junction_id: string;
  phase: string;
  camera_status: CameraStatus;
  observed_count: number | null;
  estimated_queue: number;
  queue_interval: [number, number];
  source: string;
  data_quality: string;
}

export interface SnapshotResponse {
  schema_version: string;
  mode: OperatingMode;
  run_id: string;
  state_revision: number;
  sim_time_s: number;
  notice: string;
  junctions: JunctionData[];
  plans: unknown[];
  metrics: Record<string, unknown> | null;
}

export interface HealthResponse {
  ok: boolean;
  mode: OperatingMode;
}

export interface FaultRequestPayload {
  junction_id: JunctionId;
  enabled: boolean;
}
