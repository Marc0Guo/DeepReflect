from __future__ import annotations

from fastapi import APIRouter

from deepreflect.analysis.graph import build_graph, graph_to_json
from deepreflect.config import load_config
from deepreflect.memory.db import get_concept_turns, get_session, get_concepts

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_graph():
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        G = build_graph(session)
        return graph_to_json(G)


@router.get("/concept/{concept_id}/turns")
async def get_concept_history(concept_id: int, limit: int = 20):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        turns = get_concept_turns(session, concept_id)[:limit]
        return [
            {
                "id": t.id,
                "timestamp": t.timestamp.isoformat(),
                "user_prompt": t.user_prompt[:500],
                "ai_response": t.ai_response[:500],
                "source": t.source,
                "cwd": t.cwd,
            }
            for t in turns
        ]


@router.get("/concepts")
async def list_concepts(min_ask_count: int = 1, limit: int = 100):
    cfg = load_config()
    with get_session(cfg.db_path) as session:
        concepts = get_concepts(session, min_ask_count=min_ask_count, limit=limit)
        return [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "ask_count": c.ask_count,
                "weak_score": c.weak_score,
                "last_seen": c.last_seen.isoformat() if c.last_seen else None,
            }
            for c in concepts
        ]
