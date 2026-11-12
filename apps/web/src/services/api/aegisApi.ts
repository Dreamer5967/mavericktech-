import {
  FaultRequestPayload,
  HealthResponse,
  QuestionRequest,
  QuestionResponse,
  ResetRequestPayload,
  SnapshotResponse,
  VQARequest,
} from '../../types/api';

const CAMERA_BY_JUNCTION: Record<string, string> = { J1: 'cam_g1', J2: 'cam_g3', J3: 'cam_g4', J4: 'cam_g5' };

function signalPhase(trafficLights: Record<string, string> | undefined): string {
  const states = [...new Set(Object.values(trafficLights || {}).filter(Boolean).map((state) => state.toUpperCase()))].sort();
  if (states.length === 0 || (states.length === 1 && states[0] === 'UNAVAILABLE')) return 'NOT_AVAILABLE';
  return states.length === 1 ? states[0] : `MIXED (${states.join('/')})`;
}

function normalizeSnapshot(raw: any): SnapshotResponse {
  const cameras = new Map<string, any>((raw.cameras || []).map((camera: any) => [camera.camera_id, camera]));
  const junctions = Object.entries(CAMERA_BY_JUNCTION).map(([junction_id, camera_id]) => {
    const camera = cameras.get(camera_id) || {};
    const status = camera.status === 'fresh' ? 'AVAILABLE' : camera.status === 'stale' ? 'STALE' : 'MISSING';
    return {
      junction_id, camera_id, camera_status: status, traffic_lights: camera.traffic_lights || {}, phase: signalPhase(camera.traffic_lights),
      observed_count: camera.observed_vehicle_count ?? null,
      lane_counts: camera.lane_counts ?? null, estimated_queue: null, estimated_queue_status: 'not_published', queue_interval: null, queue_interval_status: 'not_published',
      frame_url: camera.frame_url ?? null, source: 'p2_camera_observation',
      data_quality: camera.lane_count_semantics || 'whole_image_detection',
    };
  });
  return { ...raw, notice: 'ROI occupancy is not a queue estimate.', junctions, plans: [], metrics: null } as SnapshotResponse;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function parseApiError(response: Response, defaultMessage: string): Promise<ApiError> {
  let errorMsg = defaultMessage;
  let errorCode: string | undefined;

  try {
    const errorBody = await response.json();
    if (errorBody && typeof errorBody.error === 'string') {
      errorCode = errorBody.error;
      switch (errorBody.error) {
        case 'unauthorized':
          errorMsg = 'Unauthorized: Invalid operator token (401)';
          break;
        case 'invalid_request':
          errorMsg = 'Invalid request: Check parameters and junction identifier (400)';
          break;
        case 'body_too_large':
          errorMsg = 'Payload too large: Request exceeded size limit (413)';
          break;
        case 'not_found':
          errorMsg = 'Endpoint not found (404)';
          break;
        case 'backend_unavailable':
          errorMsg = 'AI service cannot reach the backend (503)';
          break;
        default:
          errorMsg = `Server error: ${errorBody.error} (${response.status})`;
      }
    }
  } catch {
    errorMsg = `${defaultMessage} (${response.status} ${response.statusText})`;
  }

  return new ApiError(errorMsg, response.status, errorCode);
}

// ---------------------------------------------------------------------------
// Existing endpoints (P4-01 / P4-02 / P4-03)
// ---------------------------------------------------------------------------

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch('/health', {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Health check failed');
  }

  return response.json();
}

export async function fetchSnapshot(): Promise<SnapshotResponse> {
  const response = await fetch('/api/v1/snapshot', {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Snapshot fetch failed');
  }

  return normalizeSnapshot(await response.json());
}

export async function postFault(
  payload: FaultRequestPayload,
  operatorToken: string
): Promise<SnapshotResponse> {
  const response = await fetch('/api/v1/faults', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${operatorToken}`,
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Fault request rejected');
  }

  return response.json();
}

export async function postReset(
  operatorToken: string,
  payload?: ResetRequestPayload
): Promise<SnapshotResponse> {
  const response = await fetch('/api/v1/reset', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${operatorToken}`,
      Accept: 'application/json',
    },
    body: JSON.stringify(payload || {}),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Scenario reset rejected');
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// P4-04: AI Assistant / VQA endpoints
// Read-only — no operator token required (question role).
// ---------------------------------------------------------------------------

export async function postQuestion(payload: QuestionRequest): Promise<QuestionResponse> {
  const response = await fetch('/api/v1/questions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Question request failed');
  }

  return response.json();
}

export async function postVQAQuestion(payload: VQARequest): Promise<QuestionResponse> {
  const response = await fetch('/api/v1/questions/vqa', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'VQA request failed');
  }

  return response.json();
}
