"""
Google Gemini API client for AEGIS Visual Question Answering (VQA).

Security & Integrity Constraints:
- Read GEMINI_API_KEY from backend settings/environment only.
- Never log or expose API keys.
- Never send evaluator ground truth or simulator metrics to Gemini.
- Send only the roadside camera frame and operator's question.
"""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

from .config import settings

# Fallback models in case primary requested model is not available on user's account tier
CANDIDATE_MODELS = [
    settings.gemini_model,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class GeminiError(Exception):
    """Base exception for Gemini API issues."""
    def __init__(self, message: str, status_code: int = 502, code: str = "gemini_error"):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class GeminiAuthError(GeminiError):
    def __init__(self, message: str = "Invalid or missing GEMINI_API_KEY."):
        super().__init__(message, status_code=401, code="gemini_auth_error")


class GeminiQuotaError(GeminiError):
    def __init__(self, message: str = "Gemini API quota exceeded (HTTP 429)."):
        super().__init__(message, status_code=429, code="gemini_quota_exceeded")


class GeminiTimeoutError(GeminiError):
    def __init__(self, message: str = "Gemini API request timed out."):
        super().__init__(message, status_code=504, code="gemini_timeout")


async def generate_vqa_answer(
    image_b64: str,
    question: str,
    mime_type: str = "image/jpeg",
) -> tuple[str, str, int]:
    """
    Send image and question to Google Gemini API.

    Returns:
        (answer_text, model_name_used, latency_ms)
    """
    api_key = settings.gemini_api_key
    if not api_key:
        raise GeminiAuthError(
            "GEMINI_API_KEY is not configured. Set GEMINI_API_KEY in apps/api/.env."
        )

    # Clean base64 if it has data URL prefix
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    # Verify base64 integrity
    try:
        base64.b64decode(image_b64, validate=True)
    except Exception:
        raise GeminiError("Invalid base64 image data.", status_code=400, code="invalid_image")

    # Strict isolation: prompt contains ONLY operator question and system instruction.
    # NO ground truth counts, simulator queues, or internal sensor telemetry.
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                    {
                        "text": question.strip(),
                    },
                ],
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are the AEGIS Traffic Visual Question Answering Assistant. "
                        "Inspect the provided traffic camera frame and answer the operator's "
                        "question factually and concisely based strictly on what is visible in the frame. "
                        "Do not fabricate or extrapolate beyond visible evidence."
                    )
                }
            ]
        },
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    t0 = time.monotonic()
    last_error: Exception | None = None

    # Try preferred model first, falling back if model is not available (404)
    # Deduplicate candidate models maintaining order
    models_to_try = []
    for m in CANDIDATE_MODELS:
        if m and m not in models_to_try:
            models_to_try.append(m)

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=4.0, read=12.0, write=5.0, pool=5.0)) as client:
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException:
                # If first candidate model times out, try next candidate model
                last_error = GeminiTimeoutError(f"Model '{model_name}' timed out after 12s.")
                continue
            except httpx.RequestError as exc:
                raise GeminiError(f"Network error connecting to Gemini API: {exc}", status_code=502)

            if resp.status_code == 200:
                data = resp.json()
                answer = _extract_answer(data)
                latency_ms = int((time.monotonic() - t0) * 1000)
                return answer, model_name, latency_ms

            if resp.status_code == 429:
                raise GeminiQuotaError(
                    "Gemini API rate limit or quota exceeded (429). Please retry later."
                )

            if resp.status_code in (401, 403):
                raise GeminiAuthError(
                    f"Gemini API authentication failed (HTTP {resp.status_code}). Verify your GEMINI_API_KEY."
                )

            if resp.status_code in (404, 503):
                # Model not found on this tier or experiencing transient 503 high demand spike.
                # Fall back to next candidate model in list.
                last_error = GeminiError(
                    f"Model '{model_name}' returned HTTP {resp.status_code}.",
                    status_code=resp.status_code,
                    code="model_unavailable",
                )
                continue

            # Other HTTP errors
            err_msg = f"Gemini API returned HTTP {resp.status_code}"
            try:
                err_body = resp.json()
                if "error" in err_body and "message" in err_body["error"]:
                    err_msg += f": {err_body['error']['message']}"
            except Exception:
                pass
            raise GeminiError(err_msg, status_code=resp.status_code)

    if last_error:
        raise last_error

    raise GeminiError("Failed to obtain response from Gemini API.", status_code=502)


def _extract_answer(data: dict[str, Any]) -> str:
    """Extract candidate text from Gemini response."""
    candidates = data.get("candidates", [])
    if not candidates:
        feedback = data.get("promptFeedback", {})
        block_reason = feedback.get("blockReason")
        if block_reason:
            return f"[Response blocked by safety filter: {block_reason}]"
        return "No response generated by the model."

    candidate = candidates[0]
    content = candidate.get("content", {})
    parts = content.get("parts", [])
    text_pieces = [p.get("text", "") for p in parts if "text" in p]
    answer = "".join(text_pieces).strip()
    return answer or "No text returned by the model."
