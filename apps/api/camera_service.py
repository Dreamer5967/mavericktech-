"""
AEGIS Camera Service — frame retrieval and status verification.

Responsibilities:
- Verify junction camera status with the authoritative snapshot API.
- If camera_status is 'MISSING', reject frame retrieval with an explicit CAMERA_UNAVAILABLE error.
- Retrieve the actual camera frame buffer from the upstream AEGIS Camera API.
- Never substitute demo images or fabricated frames.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from .config import settings


class CameraUnavailableError(Exception):
    """Raised when a camera feed is unavailable or missing due to incident faults."""
    def __init__(self, message: str, junction_id: str | None = None):
        super().__init__(message)
        self.junction_id = junction_id


async def get_camera_status(junction_id: str) -> str:
    """Fetch current camera status for a junction from snapshot API."""
    try:
        async with httpx.AsyncClient(timeout=2.0, headers={"Connection": "close"}) as client:
            resp = await client.get(f"{settings.mock_api_url}/api/v1/snapshot")
            resp.raise_for_status()
            snapshot = resp.json()
            junctions = snapshot.get("junctions", [])
            for j in junctions:
                if j.get("junction_id") == junction_id:
                    return j.get("camera_status", "UNKNOWN")
            return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


async def fetch_camera_frame(junction_id: str) -> tuple[bytes, str]:
    """
    Retrieve the actual camera frame for the selected junction from the AEGIS camera API.

    Returns:
        (image_bytes, mime_type)

    Raises:
        CameraUnavailableError: if camera is offline / MISSING or upstream has no frame buffer.
    """
    norm_id = junction_id.upper().strip()
    if norm_id not in {"J1", "J2", "J3", "J4"}:
        raise ValueError(f"Invalid junction ID '{junction_id}'. Must be J1, J2, J3, or J4.")

    # 1. Authoritative check: verify perception status
    status = await get_camera_status(norm_id)
    if status == "MISSING":
        raise CameraUnavailableError(
            f"Camera frame for {norm_id} is unavailable (roadside sensor status is MISSING). "
            f"An active incident fault has dropped this camera.",
            junction_id=norm_id,
        )

    # 2. Retrieve the actual camera frame from the upstream AEGIS Camera API
    try:
        async with httpx.AsyncClient(timeout=2.0, headers={"Connection": "close"}) as client:
            upstream_resp = await client.get(f"{settings.mock_api_url}/api/v1/frames/{norm_id}")
            if upstream_resp.status_code == 200 and upstream_resp.content:
                mime = upstream_resp.headers.get("content-type", "image/jpeg")
                return upstream_resp.content, mime
            elif upstream_resp.status_code == 404:
                raise CameraUnavailableError(
                    f"Camera frame for {norm_id} is unavailable from the AEGIS camera API (no frame buffer published).",
                    junction_id=norm_id,
                )
            else:
                raise CameraUnavailableError(
                    f"AEGIS camera API returned HTTP {upstream_resp.status_code} for junction {norm_id}.",
                    junction_id=norm_id,
                )
    except httpx.RequestError as exc:
        raise CameraUnavailableError(
            f"Could not connect to AEGIS camera API at {settings.mock_api_url}: {exc}",
            junction_id=norm_id,
        )


async def get_camera_frame_base64(junction_id: str) -> tuple[str, str]:
    """Retrieve frame from AEGIS Camera API and return as (base64_string, mime_type)."""
    raw_bytes, mime_type = await fetch_camera_frame(junction_id)
    return base64.b64encode(raw_bytes).decode("ascii"), mime_type
