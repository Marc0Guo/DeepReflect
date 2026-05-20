from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from deepreflect.agents.roast_generator import generate_roast_html
from deepreflect.agents.summary_generator import generate_summary_html
from deepreflect.api.dashboard_filters import dashboard_filters
from deepreflect.config import load_config
from deepreflect.memory.db import (
    DashboardFilters,
    filters_are_active,
    get_dashboard_analytics,
    get_filtered_stats,
    get_session,
    get_stats,
)
from deepreflect.memory.insights import get_dashboard_insights, get_session_turns

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/stats")
async def stats(filters: Annotated[DashboardFilters, Depends(dashboard_filters)]):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        if filters_are_active(filters):
            return get_filtered_stats(session, filters)
        return get_stats(session)


@router.get("/analytics")
async def analytics(
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
):
    """Activity timeline + topic/category distribution for the dashboard."""
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        return get_dashboard_analytics(session, filters)


@router.get("/insights")
async def insights(
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
    year: Optional[int] = Query(None, description="Calendar year (full Jan–Dec)"),
):
    """Behavior charts: year calendar, global time heatmap, filtered word cloud."""
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        return get_dashboard_insights(session, filters, year=year)


@router.get("/thread-turns")
async def thread_turns(
    session_id: str,
    source: str,
    limit: int = 40,
):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        return get_session_turns(session, session_id, source, limit=limit)


@router.get("/generate/{period}", response_class=HTMLResponse)
async def generate(period: str = "weekly"):
    if period not in ("daily", "weekly", "monthly", "yearly"):
        period = "weekly"
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        out_path = generate_summary_html(session, period, cfg.summaries_dir)
    return FileResponse(out_path, media_type="text/html")


@router.get("/roast", response_class=HTMLResponse)
async def roast():
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured. Set it in Settings first.")
    llm_client = None
    from deepreflect.analysis.llm_client import LLMClient
    llm_client = LLMClient.from_config(cfg)
    with get_session(cfg.db_path) as session:
        out_path = await generate_roast_html(session, llm_client, cfg.summaries_dir)
    return FileResponse(out_path, media_type="text/html")


@router.get("/list")
async def list_summaries():
    cfg = load_config()
    files = sorted(cfg.summaries_dir.glob("summary_*.html"), reverse=True)
    return [
        {"filename": f.name, "path": str(f), "size": f.stat().st_size}
        for f in files[:20]
    ]
