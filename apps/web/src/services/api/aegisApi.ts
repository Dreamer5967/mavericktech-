import {
  FaultRequestPayload,
  HealthResponse,
  QuestionRequest,
  QuestionResponse,
  ResetRequestPayload,
  SnapshotResponse,
  VQARequest,
} from '../../types/api';

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

  return response.json();
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
