from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from deepreflect.config import load_config
from deepreflect.importers.claude_code import ClaudeCodeImporter
from deepreflect.importers.cursor import CursorImporter
from deepreflect.importers.json_importer import JsonImporter
from deepreflect.importers.markdown_importer import MarkdownImporter
from deepreflect.memory.db import get_session, upsert_turn

router = APIRouter(prefix="/ingest", tags=["ingest"])

_IMPORTERS = [ClaudeCodeImporter(), CursorImporter(), MarkdownImporter(), JsonImporter()]


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


@router.get("/projects")
async def list_claude_projects():
    return {"projects": ClaudeCodeImporter().list_projects()}


@router.get("/cursor/workspaces")
async def list_cursor_workspaces():
    return {"workspaces": CursorImporter().list_workspaces()}
