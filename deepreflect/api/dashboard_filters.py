from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Query

from deepreflect.memory.db import DashboardFilters, resolve_period


def _parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def dashboard_filters(
    period: Optional[str] = Query(None, description="all|day|week|month|year"),
    since: Optional[str] = Query(None, description="ISO datetime lower bound"),
    until: Optional[str] = Query(None, description="ISO datetime upper bound"),
    source: Optional[str] = Query(None, description="Conversation source filter"),
    concept: Optional[str] = Query(None, description="Concept name substring"),
    status: Optional[str] = Query(None, description="weak|solved"),
) -> DashboardFilters:
    since_dt, until_dt = resolve_period(period)
    if since:
        since_dt = _parse_iso_datetime(since)
    if until:
        until_dt = _parse_iso_datetime(until)

    status_val = None
    if status in ("weak", "solved"):
        status_val = status

    return DashboardFilters(
        since=since_dt,
        until=until_dt,
        source=source or None,
        concept=concept.strip() if concept else None,
        status=status_val,
    )
