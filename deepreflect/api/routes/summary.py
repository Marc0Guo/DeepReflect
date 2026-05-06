from __future__ import annotations

import webbrowser
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from deepreflect.agents.summary_generator import generate_summary_html
from deepreflect.config import load_config
from deepreflect.memory.db import get_session, get_stats

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/stats")
async def stats():
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        return get_stats(session)


@router.get("/generate/{period}", response_class=HTMLResponse)
async def generate(period: str = "weekly"):
    if period not in ("daily", "weekly", "monthly", "yearly"):
        period = "weekly"
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        out_path = generate_summary_html(session, period, cfg.summaries_dir)
    return FileResponse(out_path, media_type="text/html")


@router.get("/list")
async def list_summaries():
    cfg = load_config()
    files = sorted(cfg.summaries_dir.glob("summary_*.html"), reverse=True)
    return [
        {"filename": f.name, "path": str(f), "size": f.stat().st_size}
        for f in files[:20]
    ]
