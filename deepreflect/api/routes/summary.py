from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from deepreflect.agents.roast_generator import generate_roast_html
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
