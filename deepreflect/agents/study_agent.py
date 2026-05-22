"""Generate study materials from memory using the user's LLM."""
from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select as sql_select

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

_FLASHCARD_SYSTEM = """You are a scenario-based flashcard generator for developers.

LANGUAGE RULE (non-negotiable): The flashcard front AND back MUST be written in English, regardless of what language the original exchange was in. Translate if necessary.

Given a real Q&A exchange from a developer's AI chat, generate 1 Anki-style flashcard about a transferable programming/engineering concept.

SKIP and return [] if the exchange is about ANY of the following — these make bad flashcards:
- Installing, configuring, or troubleshooting a specific tool or app (e.g. DeepReflect, Ollama setup, npm install errors for a specific project)
- Questions that only make sense in one person's environment (paths, credentials, specific repo names)
- Vague or conversational exchanges with no concrete technical content
- Asking an AI assistant to "open", "restart", "commit", or "push" something

Card style rules (for exchanges that DO qualify):
- Front: a SCENARIO or SITUATION any developer could realistically face, starting with phrases like:
  "When you...", "You encounter...", "Your code...", "You need to...", "After running..."
- Back: a concise, actionable answer — the exact command, step, or explanation they need
- Topic must be a general programming/engineering concept, not specific to one project

Good examples:
  front: "When you run git pull and see 'CONFLICT (content)' — what do you do?"
  back: "Open the conflicted file, look for <<<<<<< markers, resolve manually, then: git add <file> && git commit"

  front: "Your React component re-renders too often. You suspect a prop is changing reference each render. What do you check first?"
  back: "Wrap the value in useMemo() or useCallback(). Use React DevTools Profiler to confirm unnecessary renders."

  front: "You need to switch to a branch that exists on remote but not locally. What command?"
  back: "git fetch origin && git checkout <branch-name>  (or: git switch <branch-name> after fetch)"

Return ONLY a valid JSON array with exactly 1 card, or [] if the exchange doesn't qualify:
[
  {"front": "scenario question", "back": "concise actionable answer"}
]"""


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
    limit: int = 1,
) -> list[Flashcard]:
    import json, random, re

    # Minimum combined length (chars) for a turn to be worth converting
    _MIN_LENGTH = 120
    # How many random turns to try before giving up
    _MAX_ATTEMPTS = 15

    # Keywords that indicate a meta/setup turn that won't make a good flashcard
    _SKIP_PHRASES = [
        "deepreflect", "npm install", "npm run build", "npm run dev",
        "ollama", "pip install", "404 not found", "deepreflect serve",
        "restart", "commit and push", "git push", "help me open",
        "setup-notifications", "chromium not found",
    ]

    def _is_meta_turn(turn: object) -> bool:
        text = ((getattr(turn, "user_prompt", "") or "") + (getattr(turn, "ai_response", "") or "")).lower()
        return any(phrase in text for phrase in _SKIP_PHRASES)

    if concept:
        pool = get_concept_turns(session, concept.id)
    else:
        pool = get_turns(session, limit=2000)

    # Pre-filter obvious meta/setup turns
    pool = [t for t in pool if not _is_meta_turn(t)]

    # Pre-filter turns that already have a flashcard
    used_turn_ids: set[int] = {
        row
        for row in session.exec(
            sql_select(Flashcard.source_turn_id).where(
                Flashcard.source_turn_id.isnot(None)  # type: ignore[union-attr]
            )
        ).all()
        if row is not None
    }
    pool = [t for t in pool if t.id not in used_turn_ids]

    if not pool:
        return []

    extract_re = re.compile(r"\[.*\]", re.DOTALL)
    tried: set[int] = set()

    def _coerce(val: object) -> str:
        if isinstance(val, list):
            return " ".join(str(x) for x in val)
        return str(val).strip()

    for _ in range(_MAX_ATTEMPTS):
        # Pick a random turn we haven't tried yet
        candidates = [t for t in pool if t.id not in tried]
        if not candidates:
            break
        turn = random.choice(candidates)
        tried.add(turn.id)

        # Skip turns that are too short to yield a useful flashcard
        combined = (turn.user_prompt or "") + (turn.ai_response or "")
        if len(combined) < _MIN_LENGTH:
            continue

        prompt = f"Q: {turn.user_prompt[:600]}\n\nA: {turn.ai_response[:600]}"
        try:
            raw = await llm.complete(_FLASHCARD_SYSTEM, prompt, max_tokens=512)
            m = extract_re.search(raw)
            if not m:
                continue
            items = json.loads(m.group())
            if not items:
                continue
            item = items[0]
            if not isinstance(item, dict):
                continue
            front_val = _coerce(item.get("front", ""))
            back_val = _coerce(item.get("back", ""))
            if not front_val or not back_val:
                continue
            card = Flashcard(
                front=front_val,
                back=back_val,
                concept_id=concept.id if concept else None,
                source_turn_id=turn.id,
            )
            saved = save_flashcard(session, card)
            return [saved]
        except Exception:
            continue

    return []


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
