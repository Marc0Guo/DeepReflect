from __future__ import annotations

from fastapi import APIRouter, HTTPException

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.analysis.tagger import tag_turn
from deepreflect.config import load_config
from deepreflect.memory.db import get_session, get_unanalyzed_turns, record_mention, get_or_create_concept
from deepreflect.memory.models import ConversationTurn

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("")
async def run_analysis(limit: int = 50):
    cfg = load_config()
    if not cfg.llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured. Run: deepreflect config set-key")

    llm = LLMClient.from_config(cfg)
    processed = 0
    errors = 0

    with get_session(cfg.db_path) as session:
        turns = get_unanalyzed_turns(session)[:limit]
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

    return {"processed": processed, "errors": errors, "remaining": len(turns) - processed}


@router.get("/status")
async def analysis_status():
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        unanalyzed = get_unanalyzed_turns(session)
        return {"unanalyzed_turns": len(unanalyzed)}
