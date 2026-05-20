from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.analysis.tagger import tag_turn
from deepreflect.config import load_config
from deepreflect.memory.db import (
    count_unanalyzed_turns,
    get_or_create_concept,
    get_session,
    get_unanalyzed_date_bounds,
    get_unanalyzed_turns,
    get_unanalyzed_turns_for_analysis,
    record_mention,
    resolve_period,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])


def _parse_date_param(value: str, *, end_of_day: bool = False) -> datetime:
    raw = value.strip()
    if "T" in raw:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    dt = datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def _period_bounds(period: Optional[str]) -> tuple[Optional[datetime], Optional[datetime]]:
    if not period or period == "all":
        return None, None
    return resolve_period(period)


def _resolve_since_until(
    since: Optional[str],
    until: Optional[str],
    period: Optional[str],
) -> tuple[Optional[datetime], Optional[datetime]]:
    if since or until:
        since_dt = _parse_date_param(since) if since else None
        until_dt = _parse_date_param(until, end_of_day=True) if until else None
        return since_dt, until_dt
    return _period_bounds(period)


def _iso_date(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _build_preview_summary(
    *,
    to_process: int,
    in_selection: int,
    total_unanalyzed: int,
    selection_mode: str,
) -> tuple[str, str]:
    if total_unanalyzed == 0:
        return (
            "No unanalyzed messages in memory.",
            "Import conversations first, then run analysis.",
        )
    if to_process == 0:
        if selection_mode == "range":
            return (
                "No unanalyzed messages in the selected date range.",
                f"{total_unanalyzed:,} unanalyzed in memory.",
            )
        return (
            "No messages match this selection.",
            f"{total_unanalyzed:,} unanalyzed in memory.",
        )

    noun = "message" if to_process == 1 else "messages"
    summary = f"{to_process:,} {noun} to analyze."
    if selection_mode == "range":
        detail = (
            f"{in_selection:,} in date range · {total_unanalyzed:,} unanalyzed in memory."
        )
    else:
        detail = f"{total_unanalyzed:,} unanalyzed in memory."
    return summary, detail


@router.get("/bounds")
async def analyze_bounds():
    """Date range and recent-count limits for the analysis modal."""
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        total = count_unanalyzed_turns(session)
        dmin, dmax = get_unanalyzed_date_bounds(session)
    cap = max(1, total) if total else 1
    return {
        "total_unanalyzed": total,
        "date_min": _iso_date(dmin),
        "date_max": _iso_date(dmax),
        "recent_limit_min": 1,
        "recent_limit_max": cap,
        "recent_limit_default": min(50, cap),
    }


@router.get("/preview")
async def analyze_preview(
    mode: str = Query("recent", description="recent|range"),
    period: Optional[str] = Query(None, description="legacy: all|day|week|month|year"),
    since: Optional[str] = Query(None, description="ISO date or datetime (inclusive start)"),
    until: Optional[str] = Query(None, description="ISO date or datetime (inclusive end)"),
    source: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
):
    selection_mode = "range" if mode == "range" else "recent"
    since_dt, until_dt = (
        _resolve_since_until(since, until, period)
        if selection_mode == "range"
        else (None, None)
    )
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        total_unanalyzed = count_unanalyzed_turns(session)
        in_selection = (
            count_unanalyzed_turns(session, since=since_dt, until=until_dt, source=source)
            if selection_mode == "range"
            else total_unanalyzed
        )
        if selection_mode == "recent" and limit is not None:
            to_process = min(limit, in_selection)
        elif selection_mode == "range":
            to_process = in_selection
        else:
            to_process = in_selection
        summary, detail = _build_preview_summary(
            to_process=to_process,
            in_selection=in_selection,
            total_unanalyzed=total_unanalyzed,
            selection_mode=selection_mode,
        )
    return {
        "total_unanalyzed": total_unanalyzed,
        "in_selection": in_selection,
        "to_process": to_process,
        "limit": limit,
        "since": _iso_date(since_dt),
        "until": _iso_date(until_dt),
        "summary": summary,
        "detail": detail,
    }


@router.post("")
async def run_analysis(
    period: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
    until: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
):
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM API key not configured. Set it in Settings first.",
        )

    since_dt, until_dt = _resolve_since_until(since, until, period)
    llm = LLMClient.from_config(cfg)
    processed = 0
    errors = 0

    with get_session(cfg.db_path) as session:
        turns = get_unanalyzed_turns_for_analysis(
            session, limit=limit, since=since_dt, until=until_dt, source=source
        )
        for turn in turns:
            try:
                concepts, category = await tag_turn(turn, llm)
                for concept_name in concepts:
                    concept = get_or_create_concept(session, concept_name, category)
                    record_mention(session, turn, concept)
                turn.analyzed = True
                session.add(turn)
                session.commit()
                processed += 1
            except Exception:
                errors += 1

        remaining = count_unanalyzed_turns(session)
    return {"processed": processed, "errors": errors, "remaining": remaining}


@router.post("/stream")
async def analyze_stream(
    period: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
    until: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
):
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM API key not configured. Set it in Settings first.",
        )

    since_dt, until_dt = _resolve_since_until(since, until, period)
    llm = LLMClient.from_config(cfg)

    async def event_stream():
        with get_session(cfg.db_path) as session:
            turns = get_unanalyzed_turns_for_analysis(
                session, limit=limit, since=since_dt, until=until_dt, source=source
            )
            total = len(turns)
            yield json.dumps(
                {
                    "stage": "start",
                    "progress": 0,
                    "total": total,
                    "message": f"Found {total} messages to analyze",
                }
            ) + "\n"

            if total == 0:
                yield json.dumps(
                    {
                        "stage": "done",
                        "progress": 100,
                        "processed": 0,
                        "errors": 0,
                        "message": "No unanalyzed messages in this selection",
                    }
                ) + "\n"
                return

            processed = 0
            errors = 0
            for i, turn in enumerate(turns):
                label = (turn.user_prompt or "(empty)")[:60].replace("\n", " ")
                try:
                    concepts, category = await tag_turn(turn, llm)
                    for concept_name in concepts:
                        concept = get_or_create_concept(session, concept_name, category)
                        record_mention(session, turn, concept)
                    turn.analyzed = True
                    session.add(turn)
                    session.commit()
                    processed += 1
                    msg = f"Tagged {i + 1}/{total}: {label}…"
                except Exception:
                    errors += 1
                    msg = f"Failed {i + 1}/{total}: {label}…"

                progress = int(100 * (i + 1) / total)
                yield json.dumps(
                    {
                        "stage": "progress",
                        "progress": progress,
                        "current": i + 1,
                        "total": total,
                        "processed": processed,
                        "errors": errors,
                        "message": msg,
                    }
                ) + "\n"

            remaining = count_unanalyzed_turns(session)
            yield json.dumps(
                {
                    "stage": "done",
                    "progress": 100,
                    "processed": processed,
                    "errors": errors,
                    "remaining": remaining,
                    "message": "Analysis complete",
                }
            ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.get("/status")
async def analysis_status():
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        unanalyzed = get_unanalyzed_turns(session)
        return {"unanalyzed_turns": len(unanalyzed)}
