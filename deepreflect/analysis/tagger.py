"""Extract topic tags from conversation turns using an LLM."""
from __future__ import annotations

import json
import re

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.memory.models import ConversationTurn

_SYSTEM = """You are a learning-analytics assistant. Given a user's AI conversation turn, extract the key technical concepts, topics, or skills being asked about.

Return ONLY a JSON object:
{
  "concepts": ["concept1", "concept2", ...],
  "category": "python|ml|git|web|data|math|general|other",
  "is_repeated_question": false
}

Rules:
- concepts: 1-5 short noun phrases, lowercase (e.g. "backpropagation", "git merge conflict", "sql joins")
- category: pick the single best fit
- Keep concepts specific and technical
- Return valid JSON only"""

_EXTRACT_RE = re.compile(r"\{.*\}", re.DOTALL)


async def tag_turn(turn: ConversationTurn, llm: LLMClient) -> tuple[list[str], str]:
    """Return (concepts, category) for a single conversation turn."""
    prompt = f"User asked:\n{turn.user_prompt[:800]}\n\nAI replied:\n{turn.ai_response[:400]}"
    try:
        raw = await llm.complete(_SYSTEM, prompt, max_tokens=256)
        m = _EXTRACT_RE.search(raw)
        if not m:
            return [], "general"
        data = json.loads(m.group())
        concepts = [str(c).lower().strip() for c in data.get("concepts", []) if c][:5]
        category = str(data.get("category", "general")).lower()
        return concepts, category
    except Exception:
        return [], "general"


async def tag_turns_batch(
    turns: list[ConversationTurn], llm: LLMClient, batch_size: int = 10
) -> list[tuple[list[str], str]]:
    """Tag multiple turns. Returns list of (concepts, category) in same order."""
    results: list[tuple[list[str], str]] = []
    for turn in turns:
        result = await tag_turn(turn, llm)
        results.append(result)
    return results
