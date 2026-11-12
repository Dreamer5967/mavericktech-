"""
P4 AI/VQA Question Service — text-based question handler.

Answers operator questions purely from live snapshot data fetched from the
mock backend.  No VQA model is involved here.  Answers are always sourced
from real structured data and are labelled accordingly.

Data quality note: the mock backend returns FIXTURE data, so every answer
carries an explicit data_quality: "fixture" warning.
"""

from __future__ import annotations

import re
import time
from typing import Any

import httpx

from .camera_service import dashboard_snapshot, fetch_snapshot

# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

async def answer_question(
    question: str,
    junction_id: str | None,
    session_id: str,
) -> dict[str, Any]:
    """
    Fetch the current snapshot from the mock backend and answer *question*
    using only the data returned.

    Returns a dict matching QuestionResponse on the frontend.
    """
    t0 = time.monotonic()

    snapshot = await _fetch_snapshot()

    junctions: list[dict] = snapshot.get("junctions", [])

    # Filter to a specific junction if requested
    if junction_id:
        junctions = [j for j in junctions if j.get("junction_id") == junction_id]

    answer, refs = _answer(question.strip().lower(), junctions, snapshot)
    latency_ms = int((time.monotonic() - t0) * 1000)

    return {
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "source": "snapshot",
        "junction_id": junction_id,
        "data_quality": snapshot.get("notice", "fixture — not live sensor data"),
        "model": None,
        "status": "OK",
        "latency_ms": latency_ms,
        "timestamp": _now_iso(),
        "references": refs,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _fetch_snapshot() -> dict[str, Any]:
    return dashboard_snapshot(await fetch_snapshot())


def _answer(
    q: str,
    junctions: list[dict],
    snapshot: dict,
) -> tuple[str, list[str]]:
    """
    Rule-based question answering over snapshot data.
    Returns (answer_text, list_of_field_references).
    """
    refs: list[str] = []

    # --- highest queue / most congested ---
    if _matches(q, ["highest queue", "most congested", "longest queue", "busiest"]):
        if not junctions:
            return _no_data("queue information"), []
        ranked = [j for j in junctions if j.get("estimated_queue") is not None]
        if not ranked:
            return "Queue estimates are not published by the P2 camera service; ROI occupancy is not a queue measurement.", []
        ranked = sorted(ranked, key=lambda j: j["estimated_queue"], reverse=True)
        top = ranked[0]
        refs = [f"{top['junction_id']}.estimated_queue"]
        answer = (
            f"Junction {top['junction_id']} currently has the highest estimated queue "
            f"({top['estimated_queue']:.1f} vehicles)."
        )
        if len(ranked) > 1:
            others = ", ".join(
                f"{j['junction_id']}: {j['estimated_queue']:.1f}" for j in ranked[1:]
            )
            answer += f"  Other junctions — {others}."
        return answer, refs

    # --- lowest queue / least congested ---
    if _matches(q, ["lowest queue", "least congested", "shortest queue", "quietest"]):
        if not junctions:
            return _no_data("queue information"), []
        ranked = [j for j in junctions if j.get("estimated_queue") is not None]
        if not ranked:
            return "Queue estimates are not published by the P2 camera service; ROI occupancy is not a queue measurement.", []
        ranked = sorted(ranked, key=lambda j: j["estimated_queue"])
        top = ranked[0]
        refs = [f"{top['junction_id']}.estimated_queue"]
        return (
            f"Junction {top['junction_id']} has the lowest estimated queue "
            f"({top['estimated_queue']:.1f} vehicles).",
            refs,
        )

    # --- camera status / dropout ---
    if _matches(q, ["camera", "dropout", "missing", "offline", "unavailable"]):
        missing = [j for j in junctions if j.get("camera_status") == "MISSING"]
        available = [j for j in junctions if j.get("camera_status") == "AVAILABLE"]
        refs = [f"{j['junction_id']}.camera_status" for j in junctions]
        if not missing:
            return (
                f"All cameras in scope are AVAILABLE "
                f"({', '.join(j['junction_id'] for j in available)}).",
                refs,
            )
        return (
            f"{len(missing)} camera(s) are currently MISSING/offline: "
            f"{', '.join(j['junction_id'] for j in missing)}.  "
            f"Available: {', '.join(j['junction_id'] for j in available) or 'none'}.",
            refs,
        )

    # --- phase / signal ---
    if _matches(q, ["phase", "signal", "green", "red", "yellow", "amber"]):
        if not junctions:
            return _no_data("phase information"), []
        lines = [
            f"{j['junction_id']}: {j.get('phase', 'unknown')}"
            for j in junctions
        ]
        refs = [f"{j['junction_id']}.phase" for j in junctions]
        return "Current signal phases — " + "; ".join(lines) + ".", refs

    # --- observed count / vehicle count ---
    if _matches(q, ["observed", "count", "vehicle", "how many", "detected"]):
        if not junctions:
            return _no_data("vehicle count"), []
        lines = []
        for j in junctions:
            cnt = j.get("observed_count")
            cam = j.get("camera_status", "UNKNOWN")
            if cnt is None:
                lines.append(f"{j['junction_id']}: null (camera {cam})")
            else:
                lines.append(f"{j['junction_id']}: {cnt} (camera {cam})")
        refs = [f"{j['junction_id']}.observed_count" for j in junctions]
        return "Observed vehicle counts — " + "; ".join(lines) + ".", refs

    # --- state revision / system revision ---
    if _matches(q, ["revision", "state_revision", "version", "sequence"]):
        rev = snapshot.get("state_revision", "unknown")
        refs = ["snapshot.state_revision"]
        return f"The current state revision is {rev}.", refs

    # --- mode ---
    if _matches(q, ["mode", "live", "mock", "replay"]):
        mode = snapshot.get("mode", "unknown")
        refs = ["snapshot.mode"]
        return f"The system is currently running in {mode} mode.", refs

    # --- run id ---
    if _matches(q, ["run id", "run_id", "session", "run"]):
        run_id = snapshot.get("run_id", "unknown")
        refs = ["snapshot.run_id"]
        return f"Current run ID: {run_id}.", refs

    # --- summary / overview ---
    if _matches(q, ["summary", "overview", "status", "how is", "what is happening", "situation"]):
        if not junctions:
            return _no_data("junction status"), []
        lines = []
        for j in junctions:
            cnt = j.get("observed_count")
            cnt_str = str(cnt) if cnt is not None else "null (camera unavailable or stale)"
            lines.append(
                f"  {j['junction_id']}: phase={j.get('phase','?')}, "
                f"queue=not published, "
                f"observed={cnt_str}, camera={j.get('camera_status','?')}"
            )
        refs = [j["junction_id"] for j in junctions]
        mode = snapshot.get("mode", "?")
        rev = snapshot.get("state_revision", "?")
        summary = (
            f"AEGIS is in {mode} mode (rev #{rev}).  Junction status:\n"
            + "\n".join(lines)
        )
        return summary, refs

    # --- data quality ---
    if _matches(q, ["data quality", "fixture", "real data", "simulated"]):
        notice = snapshot.get("notice", "No notice available.")
        refs = ["snapshot.notice"]
        return f"Data quality notice: {notice}", refs

    # --- fallback ---
    available_topics = (
        "camera status, signal phases, vehicle counts, estimated queues, "
        "system mode, state revision, run ID, or a general status summary."
    )
    return (
        f"I can answer questions about: {available_topics}  "
        f"Please rephrase your question or be more specific.",
        [],
    )


def _matches(question: str, keywords: list[str]) -> bool:
    return any(kw in question for kw in keywords)


def _no_data(topic: str) -> str:
    return f"No {topic} is available in the current snapshot scope."


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

