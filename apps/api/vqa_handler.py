"""
P4 AI/VQA Question Service — VQA handler.

Supports:
1. Google Gemini API (Remote Provider) — primary modern vision model (e.g. gemini-3.8-flash).
2. ViLT (Local Provider) — optional local HuggingFace PyTorch model.
3. AEGIS Camera API frame integration — automatically retrieves the selected roadside camera frame.

Security / Integrity Constraints:
- GEMINI_API_KEY is read strictly from backend settings.
- Never log or expose API keys.
- Never send evaluator ground truth or simulator metrics to Gemini.
- Strictly validate image payload (JPEG/PNG only, <= 20,000,000 pixels).
"""

from __future__ import annotations

import base64
import io
import time
from typing import Any

from .camera_service import CameraUnavailableError, get_camera_frame_base64
from .config import settings
from .gemini_client import (
    GeminiAuthError,
    GeminiError,
    GeminiQuotaError,
    GeminiTimeoutError,
    generate_vqa_answer,
)

# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

async def answer_vqa(
    image_b64: str | None,
    question: str,
    junction_id: str | None,
    session_id: str,
) -> dict[str, Any]:
    t0 = time.monotonic()
    mime_type = "image/jpeg"

    # 1. Camera Frame Retrieval:
    # If no image_b64 was uploaded, retrieve frame from AEGIS camera API for junction_id
    if not image_b64 or not image_b64.strip():
        if not junction_id:
            raise ValueError(
                "Either an image_b64 or a valid junction_id must be provided for visual question answering."
            )
        try:
            image_b64, mime_type = await get_camera_frame_base64(junction_id)
        except CameraUnavailableError as exc:
            return _unavailable_response(
                session_id=session_id,
                question=question,
                junction_id=junction_id,
                reason=str(exc),
                status="CAMERA_UNAVAILABLE",
            )
        except ValueError as exc:
            raise ValueError(str(exc))

    # 2. Decode and validate image
    image_bytes, error = _decode_image(image_b64)
    if error:
        raise ValueError(error)

    pil_image, detected_mime, error = _validate_and_reencode(image_bytes)
    if error:
        raise ValueError(error)

    if detected_mime:
        mime_type = detected_mime

    # Re-encode clean buffer to base64
    buf = io.BytesIO()
    format_name = "JPEG" if "jpeg" in mime_type else "PNG"
    pil_image.save(buf, format=format_name)
    clean_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    # 3. Provider Routing:
    # Priority A: Google Gemini API (Remote Provider)
    if settings.gemini_api_key:
        try:
            answer, model_name, latency_ms = await generate_vqa_answer(
                image_b64=clean_b64,
                question=question,
                mime_type=mime_type,
            )
            return {
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "source": "gemini",
                "junction_id": junction_id,
                "data_quality": "ESTIMATE — NOT A MEASUREMENT. Visual Q&A answers are model predictions and may be incorrect.",
                "model": model_name,
                "status": "ESTIMATE_NOT_MEASUREMENT",
                "latency_ms": latency_ms,
                "timestamp": _now_iso(),
                "references": [],
            }
        except GeminiQuotaError as exc:
            return _unavailable_response(
                session_id, question, junction_id,
                reason=str(exc), status="QUOTA_EXCEEDED"
            )
        except GeminiAuthError as exc:
            return _unavailable_response(
                session_id, question, junction_id,
                reason=str(exc), status="AUTH_ERROR"
            )
        except GeminiTimeoutError as exc:
            return _unavailable_response(
                session_id, question, junction_id,
                reason=str(exc), status="TIMEOUT"
            )
        except GeminiError as exc:
            return _unavailable_response(
                session_id, question, junction_id,
                reason=f"Gemini API error: {exc}", status="GEMINI_ERROR"
            )

    # Priority B: Optional Local ViLT Provider (only if explicitly enabled)
    if settings.vqa_enabled:
        answer, model_name, error = _run_vilt(pil_image, question)
        latency_ms = int((time.monotonic() - t0) * 1000)
        if error:
            return _unavailable_response(
                session_id, question, junction_id,
                reason=f"ViLT model error: {error}", status="VQA_UNAVAILABLE"
            )
        return {
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "source": "vqa_model",
            "junction_id": junction_id,
            "data_quality": "ESTIMATE — NOT A MEASUREMENT. Visual Q&A answers are model predictions and may be incorrect.",
            "model": model_name,
            "status": "ESTIMATE_NOT_MEASUREMENT",
            "latency_ms": latency_ms,
            "timestamp": _now_iso(),
            "references": [],
        }

    # Neither remote Gemini nor local ViLT is active
    return _unavailable_response(
        session_id,
        question,
        junction_id,
        reason=(
            "No VQA provider is active. Configure GEMINI_API_KEY in apps/api/.env "
            "to enable Google Gemini remote vision understanding, or enable local ViLT with AEGIS_VQA_ENABLED=true."
        ),
        status="VQA_UNAVAILABLE",
    )


# ---------------------------------------------------------------------------
# Image validation
# ---------------------------------------------------------------------------

def _decode_image(image_b64: str) -> tuple[bytes | None, str | None]:
    """Decode base64 image. Returns (bytes, None) or (None, error_msg)."""
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    try:
        return base64.b64decode(image_b64, validate=True), None
    except Exception:
        return None, "image_b64 is not valid base64."


def _validate_and_reencode(image_bytes: bytes) -> tuple[Any, str | None, str | None]:
    """
    Validate JPEG/PNG format and pixel dimensions.
    Re-encode to RGB to strip EXIF / normalise colour space.
    Returns (PIL.Image, mime_type, error_msg).
    """
    try:
        from PIL import Image
    except ImportError:
        return None, None, "Pillow is not installed on this server."

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return None, None, "Could not decode image. Only JPEG and PNG are accepted."

    if img.format not in ("JPEG", "PNG"):
        return None, None, f"Unsupported image format '{img.format}'. Only JPEG and PNG are accepted."

    w, h = img.size
    if w * h > 20_000_000:
        return None, None, (
            f"Image is too large ({w}×{h} = {w * h:,} pixels). "
            "Maximum is 20,000,000 pixels."
        )

    mime = "image/jpeg" if img.format == "JPEG" else "image/png"
    # Re-encode: convert to RGB, strip EXIF
    img = img.convert("RGB")
    return img, mime, None


# ---------------------------------------------------------------------------
# ViLT inference (Optional Local Fallback)
# ---------------------------------------------------------------------------

def _run_vilt(pil_image: Any, question: str) -> tuple[str, str, str | None]:
    """
    Run the local ViLT VQA model if installed.
    Returns (answer, model_name, error_or_None).
    """
    model_name = settings.vqa_model
    try:
        from transformers import ViltForQuestionAnswering, ViltProcessor
        import torch
    except ImportError as exc:
        return "", model_name, f"Missing local dependency: {exc}. Install torch and transformers."

    try:
        processor = ViltProcessor.from_pretrained(model_name)
        model = ViltForQuestionAnswering.from_pretrained(model_name)
        model.eval()

        inputs = processor(pil_image, question, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        idx = logits.argmax(-1).item()
        answer = model.config.id2label[idx]
        return answer, model_name, None
    except Exception as exc:
        return "", model_name, str(exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unavailable_response(
    session_id: str,
    question: str,
    junction_id: str | None,
    reason: str,
    status: str = "VQA_UNAVAILABLE",
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "question": question,
        "answer": f"Visual Q&A unavailable: {reason}",
        "source": "degraded",
        "junction_id": junction_id,
        "data_quality": status,
        "model": None,
        "status": status,
        "latency_ms": 0,
        "timestamp": _now_iso(),
        "references": [],
    }


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
