"""Extract topic tags from conversation turns using an LLM."""
from __future__ import annotations

import json
import re

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.memory.models import ConversationTurn

_SYSTEM = """
You are a technical concept extraction assistant for a developer learning graph.

Given ONE exchange from an AI coding conversation, extract 1-3 core learning topics
and assign ONE category for the exchange.

Return ONLY valid JSON:

{
  "concepts": ["topic one", "topic two"],
  "category": "web|data|ml|programming|infra|mobile|math|general|other"
}

Topic naming rules (strict):
- 2-5 English words, ALWAYS separated by spaces (never concatenate words)
- Lowercase only; use proper product names when needed (react, slack, git)
- Name the technology, pattern, or task — not vague meta labels
- Prefer stable labels a developer would study (reusable across sessions)
- Do NOT echo UI settings, skill names, plugin titles, or file names literally
- Avoid trailing filler: "skill", "management", "layout", "integration", "ui design"
  unless that is the actual subject (e.g. "slack webhook integration" is fine)
- Max 3 concepts; pick only what the user is clearly trying to learn or fix

GOOD examples:
- "git merge conflict"
- "react dashboard layout"
- "data visualization charts"
- "slack bot notifications"
- "python asyncio debugging"

BAD examples (never output like these):
- "datavisualization"
- "frontenddesign skill"
- "plugininstallation"
- "ai skillmanagement"
- "glassmorphism"
- "saasdashboard ui"
- "notificationscheduling"

Category guide (pick ONE primary domain for the exchange):
- web → frontend/backend, React, CSS, browsers, APIs for apps
- data → SQL, analytics, charts, pipelines, visualization
- ml → LLMs, agents, embeddings, machine learning
- programming → languages, algorithms, debugging, git
- infra → docker, kubernetes, cloud, devops, networking
- mobile → iOS/Android development
- math → statistics, linear algebra, optimization
- general → mixed technical work
- other → non-technical

Return JSON only.
"""

# Longest-first greedy split for model outputs that glue words together.
_COMPOUND_TOKENS: tuple[str, ...] = tuple(
    sorted(
        {
            "visualization", "installation", "integration", "management", "scheduling",
            "glassmorphism", "morphism", "dashboard", "frontend", "backend", "notification",
            "saas", "conflict", "debugging", "asyncio", "kubernetes", "docker",
            "python", "typescript", "javascript", "react", "slack", "discord",
            "plugin", "skill", "design", "layout", "light", "mode", "git", "merge",
            "branch", "api", "webhook", "database", "sql", "chart", "agent",
            "embedding", "prompt", "ui", "ux", "mobile", "android", "ios", "cloud",
            "aws", "azure", "network", "security", "auth", "authentication",
            "authorization", "cache", "caching", "test", "testing", "deploy",
            "deployment", "ci", "cd", "pipeline", "etl", "analytics", "machine",
            "learning", "deep", "vector", "retrieval", "rag", "data",
        },
        key=len,
        reverse=True,
    )
)

_VALID_CATEGORIES = frozenset({
    "web", "data", "ml", "ml_ai", "programming", "infra", "mobile",
    "math", "research", "general", "other",
})

_GENERIC_ONLY = frozenset({
    "ui", "ux", "design", "layout", "skill", "skills", "plugin", "plugins",
    "integration", "management", "tool", "tools", "feature", "features",
    "setting", "settings", "config", "configuration", "mode", "light",
})

_EXTRACT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _split_compound_word(text: str) -> str:
    """Turn glued lowercase strings into spaced phrases when possible."""
    if " " in text or len(text) <= 10:
        return text
    tokens: list[str] = []
    i = 0
    sorted_tokens = sorted(_COMPOUND_TOKENS, key=len, reverse=True)
    while i < len(text):
        matched = False
        for tok in sorted_tokens:
            if text[i:].startswith(tok):
                tokens.append(tok)
                i += len(tok)
                matched = True
                break
        if not matched:
            return text
    return " ".join(tokens) if len(tokens) >= 2 else text


def normalize_concept(raw: str) -> str | None:
    """Canonicalize a single concept label; return None if too weak to keep."""
    s = raw.lower().strip()
    s = re.sub(r"[_\-/]+", " ", s)
    s = re.sub(r"[^a-z0-9.+# ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Drop noisy suffixes when the label is already multi-word.
    for suffix in (" skill", " skills", " management", " layout", " ui design"):
        if s.endswith(suffix) and s.count(" ") >= 1:
            s = s[: -len(suffix)].strip()

    if " " not in s:
        s = _split_compound_word(s)
    else:
        parts = [_split_compound_word(p) if " " not in p else p for p in s.split()]
        s = " ".join(parts)
    s = re.sub(r"\s+", " ", s).strip()

    words = s.split()
    if len(words) < 1 or len(words) > 6:
        return None
    if len(s) < 3:
        return None
    if len(words) == 1 and words[0] in _GENERIC_ONLY:
        return None
    if words == ["ai", "skill"] or words == ["ai", "skills"]:
        return None
    return s


def normalize_category(raw: str) -> str:
    from deepreflect.analysis.domains import normalize_graph_category

    cat = str(raw or "general").lower().strip()
    if cat not in _VALID_CATEGORIES:
        return "general"
    return normalize_graph_category(cat)


async def tag_turn(turn: ConversationTurn, llm: LLMClient) -> tuple[list[str], str]:
    """Return (concepts, category) for a single conversation turn."""
    prompt = f"User asked:\n{turn.user_prompt[:800]}\n\nAI replied:\n{turn.ai_response[:400]}"
    try:
        raw = await llm.complete(_SYSTEM, prompt, max_tokens=1024)
        m = _EXTRACT_RE.search(raw)
        if not m:
            return [], "general"
        data = json.loads(m.group())
        seen: set[str] = set()
        concepts: list[str] = []
        for c in data.get("concepts", []):
            name = normalize_concept(str(c))
            if name and name not in seen:
                seen.add(name)
                concepts.append(name)
            if len(concepts) >= 3:
                break
        category = normalize_category(str(data.get("category", "general")))
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
