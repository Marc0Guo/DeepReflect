from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from deepreflect.analysis.domains import backfill_domain_mentions, record_turn_tags
from deepreflect.config import load_config
from deepreflect.importers.claude_code import ClaudeCodeImporter
from deepreflect.importers.cursor import CursorImporter
from deepreflect.importers.json_importer import JsonImporter
from deepreflect.importers.markdown_importer import MarkdownImporter
from deepreflect.memory.db import clear_memory, get_session, upsert_turn
from deepreflect.memory.models import ConversationTurn

router = APIRouter(prefix="/ingest", tags=["ingest"])

_IMPORTERS = [ClaudeCodeImporter(), CursorImporter(), MarkdownImporter(), JsonImporter()]


# ── Raw-turn ingestion (used by the DeepReflect Cursor/Claude Code hook) ──────

class RawTurnRequest(BaseModel):
    """A single conversation turn pushed directly from the editor hook.

    If ``topics`` is supplied (extracted by Claude in the hook rule), the turn
    is tagged immediately — no second LLM call needed.  If omitted the turn is
    stored unanalyzed and can be processed later via the normal analyze flow.
    """
    user_prompt: str
    ai_response: str
    source: str = "cursor"
    timestamp: Optional[str] = None   # ISO-8601; defaults to now
    cwd: Optional[str] = None
    session_id: Optional[str] = None
    # Pre-extracted by Claude via the hook rule (no LLM re-tagging needed)
    topics: Optional[list[str]] = None
    domain: Optional[str] = None      # web|data|ml|programming|infra|mobile|math|general


@router.post("/raw-turn")
async def ingest_raw_turn(req: RawTurnRequest):
    """Store one turn and, if Claude already supplied tags, apply them instantly."""
    cfg = load_config()

    try:
        ts = datetime.fromisoformat(req.timestamp.replace("Z", "+00:00")) if req.timestamp else datetime.now(timezone.utc)
    except (ValueError, AttributeError):
        ts = datetime.now(timezone.utc)

    turn = ConversationTurn(
        user_prompt=req.user_prompt[:8000],
        ai_response=req.ai_response[:16000],
        source=req.source,
        cwd=req.cwd or "",
        session_id=req.session_id or f"hook-{req.source}-{ts.date()}",
        timestamp=ts,
        analyzed=False,
    )

    with get_session(cfg.db_path) as session:
        saved = upsert_turn(session, turn)
        is_new = saved is turn
        tagged = False

        if req.topics and is_new:
            clean_topics = [t.lower().strip() for t in req.topics if t and len(t) < 80]
            if clean_topics:
                record_turn_tags(session, saved, clean_topics, req.domain or "general")
                saved.analyzed = True
                session.add(saved)
                backfill_domain_mentions(session)
                session.commit()
                tagged = True

    return {"status": "ok", "new": is_new, "tagged": tagged, "topics": req.topics or []}


class IngestRequest(BaseModel):
    path: str | None = None
    source: str = "claude-code"
    session_id: str | None = None


@router.post("")
async def ingest(req: IngestRequest):
    cfg = load_config()

    if req.source == "claude-code" and req.path is None:
        importer = ClaudeCodeImporter()
        if req.session_id:
            turns = importer.import_session(req.session_id)
        else:
            turns = importer.import_all_projects()
    elif req.source == "cursor" and req.path is None:
        turns = CursorImporter().import_all()
    elif req.path:
        path = Path(req.path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {req.path}")
        importer = next((i for i in _IMPORTERS if i.detect(req.path)), None)
        if not importer:
            raise HTTPException(status_code=400, detail="No importer found for this file type")
        turns = importer.parse(req.path)
    else:
        raise HTTPException(status_code=400, detail="Provide path or source=claude-code")

    with get_session(cfg.db_path) as session:
        saved = 0
        for turn in turns:
            result = upsert_turn(session, turn)
            if result is turn:
                saved += 1

    return {"imported": len(turns), "new": saved, "source": req.source}


@router.post("/claude-code/all")
async def ingest_all_claude():
    cfg = load_config()
    importer = ClaudeCodeImporter()
    turns = importer.import_all_projects()
    with get_session(cfg.db_path) as session:
        saved = sum(1 for t in turns if upsert_turn(session, t) is t)
    return {"imported": len(turns), "new": saved, "source": "claude-code"}


@router.post("/cursor/all")
async def ingest_all_cursor():
    cfg = load_config()
    turns = CursorImporter().import_all()
    with get_session(cfg.db_path) as session:
        saved = sum(1 for t in turns if upsert_turn(session, t) is t)
    return {"imported": len(turns), "new": saved, "source": "cursor"}


@router.post("/cursor/all/stream")
async def ingest_all_cursor_stream():
    cfg = load_config()

    def event_stream():
        importer = CursorImporter()
        turns: list = []

        for event in importer.iter_import_all():
            if event.get("stage") == "parsed":
                turns = importer._parsed_turns
                event = {
                    **event,
                    "message": f"Saving {len(turns)} exchanges to memory…",
                }
            yield json.dumps(event) + "\n"

        saved = 0
        total = max(len(turns), 1)
        with get_session(cfg.db_path) as session:
            for i, turn in enumerate(turns):
                if upsert_turn(session, turn) is turn:
                    saved += 1
                if i % 50 == 0 or i == total - 1:
                    yield json.dumps(
                        {
                            "stage": "saving",
                            "progress": 78 + int(21 * (i + 1) / total),
                            "message": f"Saving exchanges ({i + 1}/{total})…",
                        }
                    ) + "\n"

        yield json.dumps(
            {
                "stage": "done",
                "progress": 100,
                "message": "Import complete",
                "imported": len(turns),
                "new": saved,
            }
        ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.post("/clear")
async def ingest_clear():
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        deleted = clear_memory(session)
    return {"cleared": deleted}


@router.get("/projects")
async def list_claude_projects():
    return {"projects": ClaudeCodeImporter().list_projects()}


@router.get("/cursor/workspaces")
async def list_cursor_workspaces():
    return {"workspaces": CursorImporter().list_workspaces()}
