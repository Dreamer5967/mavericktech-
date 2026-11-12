export type ConnectionStatus = 'CONNECTED' | 'STALE' | 'DISCONNECTED';

export type OperatingMode = 'MOCK' | 'LIVE' | 'REPLAY' | 'RESETTING' | string;

export type CameraStatus = 'AVAILABLE' | 'MISSING' | string;

export type JunctionId = 'J1' | 'J2' | 'J3' | 'J4';

export interface JunctionData {
  junction_id: string;
  camera_id: string;
  phase: string;
  camera_status: CameraStatus;
  observed_count: number | null;
  lane_counts: Record<string, number | null> | null;
  estimated_queue: number | null;
  queue_interval: [number, number] | null;
  frame_url: string | null;
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
  request_id?: string;
}

export interface ResetRequestPayload {
  request_id?: string;
}

export interface IncidentLogEntry {
  id: string;
  request_id: string;
  timestamp: string;
  type: 'FAULT_INJECTION' | 'FAULT_CLEAR' | 'SCENARIO_RESET';
  junction_id?: JunctionId | 'ALL';
  status: 'PENDING' | 'APPLIED' | 'REJECTED';
  state_revision?: number;
  message?: string;
}

// ---------------------------------------------------------------------------
// P4-04: AI Assistant / VQA types
// ---------------------------------------------------------------------------

export interface QuestionRequest {
  question: string;
  junction_id?: JunctionId | null;
  session_id?: string;
}

export interface VQARequest {
  image_b64?: string;
  question: string;
  junction_id?: JunctionId | null;
  session_id?: string;
}

export interface QuestionResponse {
  session_id: string;
  question: string;
  answer: string;
  /** 'snapshot' = answered from structured data; 'vqa_model' = ViLT; 'gemini' = Google Gemini; 'degraded' = service unavailable */
  source: 'snapshot' | 'vqa_model' | 'gemini' | 'degraded';
  junction_id?: string | null;
  data_quality?: string;
  model?: string | null;
  status: string;
  latency_ms?: number;
  timestamp: string;
  references?: string[];
}

export type ChatMessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  timestamp: string;
  source?: QuestionResponse['source'];
  junction_id?: string | null;
  status?: string;
  data_quality?: string;
}
