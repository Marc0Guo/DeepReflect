"""Detect repeated questions and weak areas from memory."""
from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from deepreflect.memory.db import get_concepts
from deepreflect.memory.models import Concept


def get_weak_concepts(session: Session, threshold: int = 3) -> list[Concept]:
    """Return concepts asked >= threshold times, sorted by ask_count desc."""
    all_concepts = get_concepts(session)
    return [c for c in all_concepts if c.ask_count >= threshold]


def get_repeated_question_report(session: Session, threshold: int = 3) -> dict:
    """Build a summary of repeated topics for the coach agent / summary pages."""
    weak = get_weak_concepts(session, threshold)
    return {
        "repeated_concepts": [
            {
                "name": c.name,
                "category": c.category,
                "ask_count": c.ask_count,
                "weak_score": round(c.weak_score, 2),
                "last_seen": c.last_seen.isoformat() if c.last_seen else None,
            }
            for c in weak
        ],
        "total_repeated": len(weak),
    }


def check_intervention(
    session: Session, prompt: str, threshold: int = 3
) -> tuple[bool, list[str]]:
    """Check if the incoming prompt touches concepts repeated >= threshold times.

    Returns (should_intervene, list_of_repeated_concept_names).
    Simple heuristic: concept name appears in prompt (case-insensitive).
    """
    weak = get_weak_concepts(session, threshold)
    prompt_lower = prompt.lower()
    triggered = [c.name for c in weak if c.name in prompt_lower]
    return bool(triggered), triggered
