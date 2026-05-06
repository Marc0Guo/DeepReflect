"""Generate study materials from memory using the user's LLM."""
from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.memory.db import get_concept_turns, get_concepts, get_flashcards, get_turns, save_flashcard
from deepreflect.memory.models import Concept, Flashcard

_STUDY_GUIDE_SYSTEM = """You are a learning coach. Given a list of topics a user repeatedly asked an AI about, generate a concise, practical study guide.

Format:
## Study Guide — [period]

For each concept:
### [Concept Name]
- **What it is**: one-sentence definition
- **Why you keep asking**: likely gap
- **How to master it**: 2-3 concrete steps

End with:
## Suggested Weekly Goal
One clear, achievable goal."""

_FLASHCARD_SYSTEM = """You are a flashcard generator. Given a Q&A exchange, generate 1-3 Anki-style flashcards.

Return ONLY a JSON array:
[
  {"front": "question", "back": "concise answer"},
  ...
]

Make flashcards specific, testable, and self-contained."""


async def generate_study_guide(
    session: Session,
    llm: LLMClient,
    period: str = "this week",
    top_n: int = 10,
) -> str:
    concepts = get_concepts(session, min_ask_count=2)[:top_n]
    if not concepts:
        return "No repeated topics found yet. Keep using DeepReflect to build your learning history."

    concept_list = "\n".join(
        f"- {c.name} (asked {c.ask_count}x, category: {c.category})" for c in concepts
    )
    prompt = f"Period: {period}\n\nTop repeated topics:\n{concept_list}"

    try:
        return await llm.complete(_STUDY_GUIDE_SYSTEM, prompt, max_tokens=2048)
    except Exception as e:
        return f"Error generating study guide: {e}"


async def generate_flashcards(
    session: Session,
    llm: LLMClient,
    concept: Concept | None = None,
    limit: int = 10,
) -> list[Flashcard]:
    import json, re

    if concept:
        turns = get_concept_turns(session, concept.id)[:limit]
    else:
        turns = get_turns(session, limit=limit)

    cards: list[Flashcard] = []
    extract_re = re.compile(r"\[.*\]", re.DOTALL)

    for turn in turns:
        prompt = f"Q: {turn.user_prompt[:600]}\n\nA: {turn.ai_response[:600]}"
        try:
            raw = await llm.complete(_FLASHCARD_SYSTEM, prompt, max_tokens=512)
            m = extract_re.search(raw)
            if not m:
                continue
            items = json.loads(m.group())
            for item in items[:3]:
                if isinstance(item, dict) and item.get("front") and item.get("back"):
                    card = Flashcard(
                        front=item["front"],
                        back=item["back"],
                        concept_id=concept.id if concept else None,
                        source_turn_id=turn.id,
                    )
                    saved = save_flashcard(session, card)
                    cards.append(saved)
        except Exception:
            continue

    return cards


_QUIZ_SYSTEM = """You are a quiz generator for a learning app. Given a list of topics the user has been studying, generate exactly 5 quiz questions as a JSON array.

Return ONLY a valid JSON array with this exact structure — no markdown fences, no commentary:
[
  {
    "question": "Clear, specific question text",
    "type": "multiple_choice",
    "choices": [
      {"text": "Option A text", "is_correct": false, "explanation": "Why this is wrong"},
      {"text": "Option B text", "is_correct": true, "explanation": "Why this is correct"},
      {"text": "Option C text", "is_correct": false, "explanation": "Why this is wrong"},
      {"text": "Option D text", "is_correct": false, "explanation": "Why this is wrong"}
    ]
  },
  {
    "question": "Another question",
    "type": "short_answer",
    "answer": "The correct answer",
    "explanation": "Detailed explanation of why this is the answer and key concepts involved"
  }
]

Rules:
- Generate 4 multiple_choice and 1 short_answer question
- Each multiple_choice must have exactly 4 choices with exactly 1 correct
- Every choice needs an explanation (shown when user picks it)
- Questions should be practical and test real understanding, not trivia
- Vary difficulty: 2 easy, 2 medium, 1 hard"""


async def generate_quiz(
    session: Session,
    llm: LLMClient,
    top_n: int = 5,
) -> list[dict]:
    import json, re

    concepts = get_concepts(session, min_ask_count=2)[:top_n]
    if not concepts:
        return []

    concept_list = "\n".join(
        f"- {c.name} (category: {c.category}, asked {c.ask_count}x)"
        for c in concepts
    )
    prompt = f"Topics the user has been studying:\n{concept_list}"

    try:
        raw = await llm.complete(_QUIZ_SYSTEM, prompt, max_tokens=2500)
        extract_re = re.compile(r"\[.*\]", re.DOTALL)
        m = extract_re.search(raw)
        if not m:
            return []
        questions = json.loads(m.group())
        if isinstance(questions, list):
            return questions
        return []
    except Exception:
        return []
