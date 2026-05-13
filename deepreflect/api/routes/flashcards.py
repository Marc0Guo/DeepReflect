from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from deepreflect.agents.study_agent import generate_flashcards, generate_quiz, generate_study_guide
from deepreflect.analysis.llm_client import LLMClient
from deepreflect.config import load_config
from deepreflect.memory.db import (
    get_content_history,
    get_flashcards,
    get_session,
    save_generated_content,
)

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/flashcards")
async def list_flashcards(concept_id: int | None = None):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        cards = get_flashcards(session, concept_id=concept_id)
        return [{"id": c.id, "front": c.front, "back": c.back, "concept_id": c.concept_id} for c in cards]


@router.post("/flashcards/generate")
async def gen_flashcards(concept_id: int | None = None, limit: int = 10):
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured")
    llm = LLMClient.from_config(cfg)
    with get_session(cfg.db_path) as session:
        cards = await generate_flashcards(session, llm, limit=limit)
        return {"generated": len(cards)}


@router.get("/flashcards/export")
async def export_flashcards(fmt: str = "csv"):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        cards = get_flashcards(session)

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Front", "Back"])
        for c in cards:
            writer.writerow([c.front, c.back])
        return PlainTextResponse(buf.getvalue(), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=flashcards.csv"})
    else:  # markdown
        lines = [f"## Card {i+1}\n**Q:** {c.front}\n\n**A:** {c.back}\n" for i, c in enumerate(cards)]
        return PlainTextResponse("\n---\n".join(lines), media_type="text/markdown")


@router.get("/guide")
async def study_guide(period: str = "this week"):
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured")
    llm = LLMClient.from_config(cfg)
    with get_session(cfg.db_path) as session:
        text = await generate_study_guide(session, llm, period=period)
        title = f"Study Guide — {period}"
        save_generated_content(session, "study_guide", text, period=period, title=title)
    return {"guide": text}


@router.get("/quiz")
async def quiz():
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured")
    llm = LLMClient.from_config(cfg)
    with get_session(cfg.db_path) as session:
        questions = await generate_quiz(session, llm)
        if questions:
            save_generated_content(
                session,
                "quiz",
                json.dumps(questions),
                title=f"Quiz — {len(questions)} questions",
            )
    return {"questions": questions}


@router.get("/history")
async def content_history(content_type: str = "quiz", limit: int = 50):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        items = get_content_history(session, content_type, limit=limit)
        result = []
        for item in items:
            entry: dict = {
                "id": item.id,
                "content_type": item.content_type,
                "title": item.title,
                "period": item.period,
                "created_at": item.created_at.isoformat(),
            }
            if content_type == "quiz":
                try:
                    entry["questions"] = json.loads(item.content)
                except Exception:
                    entry["questions"] = []
            else:
                entry["content"] = item.content
            result.append(entry)
        return result
