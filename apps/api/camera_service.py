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


CAMERA_BY_JUNCTION={"J1":"cam_g1","J2":"cam_g3","J3":"cam_g4","J4":"cam_g5"}


def signal_phase(traffic_lights: dict[str, str] | None) -> str:
    """Compact an observed signal group without inventing a controller phase."""
    states=sorted({str(state).upper() for state in (traffic_lights or {}).values() if state})
    if not states or states==["UNAVAILABLE"]:
        return "NOT_AVAILABLE"
    return states[0] if len(states)==1 else "MIXED ("+"/".join(states)+")"


async def fetch_snapshot() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=3.0, headers={"Connection": "close"}) as client:
        response=await client.get(f"{settings.camera_api_url}/api/v1/snapshot")
        response.raise_for_status()
        return response.json()


def dashboard_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Map P2 camera observations to junction rows without fabricating queues."""
    by_id={camera.get("camera_id"):camera for camera in snapshot.get("cameras",[])}
    junctions=[]
    for junction_id,camera_id in CAMERA_BY_JUNCTION.items():
        camera=by_id.get(camera_id,{})
        status=camera.get("status","missing")
        available="AVAILABLE" if status=="fresh" else "STALE" if status=="stale" else "MISSING"
        junctions.append({
            "junction_id":junction_id,"camera_id":camera_id,"camera_status":available,
            "phase":signal_phase(camera.get("traffic_lights")),"traffic_lights":camera.get("traffic_lights") or {},
            "observed_count":camera.get("observed_vehicle_count"),
            "lane_counts":camera.get("lane_counts"),"estimated_queue":None,
            "estimated_queue_status":"not_published","queue_interval":None,
            "queue_interval_status":"not_published","frame_url":camera.get("frame_url"),
            "source":"p2_camera_observation","data_quality":camera.get("lane_count_semantics", "whole_image_detection"),
        })
    return {**snapshot,"notice":"ROI occupancy is not a queue estimate.","junctions":junctions}


async def get_camera_status(junction_id: str) -> str:
    """Fetch current camera status for a junction from snapshot API."""
    try:
        snapshot=dashboard_snapshot(await fetch_snapshot())
        for junction in snapshot["junctions"]:
            if junction["junction_id"]==junction_id:
                return junction["camera_status"]
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

    snapshot=dashboard_snapshot(await fetch_snapshot())
    row=next((item for item in snapshot["junctions"] if item["junction_id"]==norm_id),None)
    frame_url=row.get("frame_url") if row else None
    if not frame_url:
        raise CameraUnavailableError(f"Camera frame for {norm_id} has no published frame URL.",junction_id=norm_id)

    # 2. Retrieve the actual P2 bounded-cache frame; never invent a frame ID.
    try:
        async with httpx.AsyncClient(timeout=2.0, headers={"Connection": "close"}) as client:
            upstream_resp = await client.get(f"{settings.camera_api_url}{frame_url}")
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
