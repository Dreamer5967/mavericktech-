"""
P4 AI/VQA Question Service — FastAPI application entry-point.

Endpoints
---------
GET  /health                     Service liveness & provider readiness probe.
GET  /api/v1/frames/{frame_id}   Retrieve camera frame from AEGIS Camera API.
POST /api/v1/questions           Text-based Q&A from live snapshot data.
POST /api/v1/questions/vqa       Visual Q&A using Google Gemini API or local ViLT.

Role boundary
-------------
This service is strictly READ-ONLY and informational. It has no operator
token and cannot mutate simulator state, signals, or faults.
"""

from __future__ import annotations

import re
import uuid
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .camera_service import CameraUnavailableError, fetch_camera_frame
from .config import settings
from .question_handler import answer_question
from .vqa_handler import answer_vqa

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AEGIS P4 AI/VQA Question Service",
    version="1.1.0",
    description="Read-only informational Q&A and Gemini VQA for the AEGIS operator dashboard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    junction_id: str | None = Field(None, pattern=r"^J[1-4]$")
    session_id: str | None = None


class VQARequest(BaseModel):
    image_b64: str | None = None
    question: str = Field(..., min_length=1, max_length=500)
    junction_id: str | None = Field(None, pattern=r"^J[1-4]$")
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Middleware: enforce body size limits
# ---------------------------------------------------------------------------

@app.middleware("http")
async def enforce_body_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    path = request.url.path

    if path.endswith("/vqa"):
        limit = settings.max_body_bytes_vqa
    else:
        limit = settings.max_body_bytes_text

    if content_length and int(content_length) > limit:
        return JSONResponse(
            status_code=413,
            content={"error": "body_too_large", "detail": f"Body exceeds {limit} byte limit."},
        )

    return await call_next(request)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Liveness probe — verifies backend reachability & Gemini configuration."""
    mock_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.camera_api_url}/health")
            mock_ok = resp.status_code == 200
    except Exception:
        pass

    gemini_ready = bool(settings.gemini_api_key)

    return {
        "ok": True,
        "service": "aegis-qa",
        "camera_backend_reachable": mock_ok,
        "gemini_configured": gemini_ready,
        "gemini_model": settings.gemini_model if gemini_ready else None,
        "vqa_enabled": settings.vqa_enabled,
        "vilt_enabled": settings.vqa_enabled,
        "active_vqa_provider": "gemini" if gemini_ready else ("vilt" if settings.vqa_enabled else "none"),
    }


@app.get("/api/v1/frames/{frame_id}")
async def get_frame(frame_id: str):
    """
    Retrieve real camera frame from the AEGIS camera service.
    If camera status is MISSING, returns 404 (unavailable).
    """
    # Normalize ID: e.g. cam_j1_roadside -> J1, J1 -> J1
    m = re.search(r"J[1-4]", frame_id.upper())
    junction_id = m.group(0) if m else frame_id.upper()

    try:
        frame_bytes, mime_type = await fetch_camera_frame(junction_id)
        return Response(content=frame_bytes, media_type=mime_type)
    except CameraUnavailableError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "camera_unavailable",
                "detail": str(exc),
                "junction_id": junction_id,
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "detail": str(exc)},
        )


@app.post("/api/v1/questions")
async def post_question(body: QuestionRequest):
    """Answer text questions strictly from live snapshot data."""
    session_id = body.session_id or str(uuid.uuid4())

    try:
        result = await answer_question(
            question=body.question,
            junction_id=body.junction_id,
            session_id=session_id,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "backend_unavailable",
                "detail": f"Cannot reach mock backend at {settings.mock_api_url}: {exc}",
            },
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "backend_error",
                "detail": f"Mock backend returned {exc.response.status_code}.",
            },
        )

    return result


@app.post("/api/v1/questions/vqa")
async def post_vqa_question(body: VQARequest):
    """
    Visual Question Answering endpoint.

    Operator can either provide:
    1. An uploaded base64 image (image_b64), OR
    2. A target junction_id (J1-J4) to pull the actual frame from the Camera API.

    Answers are generated by Google Gemini (remote) or ViLT (local).
    Answers are labelled ESTIMATE_NOT_MEASUREMENT.
    """
    session_id = body.session_id or str(uuid.uuid4())

    try:
        result = await answer_vqa(
            image_b64=body.image_b64,
            question=body.question,
            junction_id=body.junction_id,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "detail": str(exc)},
        )

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="127.0.0.1", port=settings.port, reload=True)
