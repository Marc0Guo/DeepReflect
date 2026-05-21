"""Generate a Vibe Roast HTML page from DeepReflect memory (playful, not TechRoast dark theme)."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlmodel import Session

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.memory.db import get_concepts, get_stats, get_turns

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_COASTER_X = [18, 175, 355, 535, 755]

_ROAST_SYSTEM = """You write Vibe Roast reports — playful, specific roasts of a developer's AI chat habits.
Tone: clever, observant, slightly unhinged. NOT corporate annual review. NOT generic.

Use their REAL data below. Wrap highlight phrases in <em>...</em> (html2canvas-safe highlights).
You may use <strong> and <span class="danger">...</span> sparingly in mini_cards body HTML only.

Return ONLY valid JSON with this exact shape:
{
  "score": 42,
  "score_label": "SHORT LABEL",
  "ribbon": "🔥 vibe check failed · not a slide deck",
  "title_lines": ["Line one", "Line two"],
  "tagline": "N sessions · M prompts · tools used",
  "sub_meme": "(one short funny disclaimer)",
  "bubbles": [
    {"n": "42", "k": "vibe score label"},
    {"n": "78%", "k": "second stat"},
    {"n": "6×", "k": "third stat"},
    {"n": "9.2", "k": "fourth stat"}
  ],
  "lead": "One punchy lead with <em>highlight</em>.",
  "vibe_body": "2-3 sentences on their actual patterns.",
  "bars": [
    {"name": "metric label", "pct": 88},
    {"name": "Framework tourism", "pct": 74},
    {"name": "AI reads docs", "pct": 91},
    {"name": "Actually shipping", "pct": 19}
  ],
  "pills": ["Cursor ×14", "concept ×3"],
  "taxonomy": [
    {"emoji": "🔄", "title": "pattern name", "desc": "one line"},
    {"emoji": "📋", "title": "...", "desc": "..."},
    {"emoji": "🧪", "title": "...", "desc": "..."},
    {"emoji": "🦀", "title": "...", "desc": "..."}
  ],
  "chaotic_quote": "verbatim or paraphrased wildest prompt, max 120 chars",
  "chaotic_note": "👈 one line roast of that moment",
  "mini_cards": [
    {"emoji": "🔁", "title": "Repeat mistake", "body": "html allowed"},
    {"emoji": "🐍", "title": "Script moment", "body": "html allowed"}
  ],
  "risk_line": "⚠️ One high-risk architecture line",
  "coaster_labels": ["hope", "paste repo", "rage", "new stack", "sleep?"],
  "dependency_html": "Bullet lines with <br> between, use <strong> for numbers",
  "award_paragraphs": ["para1", "para2", "para3"],
  "final_line": "Vibe score <strong>42/100</strong> · one-line quest",
  "footer_quote": "Therapist-style one-liner in quotes",
  "footer_sign": "— Vibe Roast · DeepReflect · date"
}

Score 0-100 (higher = more repeat-asker chaos). Bars pct 0-100. Be specific to their concepts and prompts."""


def _build_context(concepts, stats, turns) -> str:
    top = concepts[:10]
    concept_lines = "\n".join(
        f"- {c.name} ({c.category}): asked {c.ask_count}×"
        for c in top
    ) or "- (no repeated concepts yet)"
    sources = stats.get("sources") or {}
    source_line = ", ".join(f"{k} {v}" for k, v in sources.items()) if sources else "unknown"
    snippets = []
    for t in turns[:12]:
        prompt = (t.user_prompt or "").strip().replace("\n", " ")[:220]
        if prompt:
            snippets.append(f"[{t.source}] {prompt}")
    snippet_block = "\n".join(snippets) if snippets else "(no recent prompts)"
    return (
        f"Total turns: {stats['total_turns']}\n"
        f"Weekly turns: {stats['weekly_turns']}\n"
        f"Concepts tracked: {stats['total_concepts']}\n"
        f"Sources: {source_line}\n\n"
        f"Top repeated concepts:\n{concept_lines}\n\n"
        f"Recent user prompts:\n{snippet_block}"
    )


def _fallback_data(concepts, stats) -> dict:
    top = concepts[:5]
    avg = int(sum(c.ask_count for c in top) / max(len(top), 1) * 8) if top else 40
    score = min(max(avg, 12), 88)
    concept_name = top[0].name if top else "everything"
    return {
        "score": score,
        "score_label": "CERTIFIED REPEAT ASKER",
        "ribbon": "🔥 vibe check failed · not a slide deck",
        "title_lines": ["Your AI History", "Got Cooked"],
        "tagline": (
            f"{stats['total_turns']} conversations · "
            f"{stats['total_concepts']} concepts tracked"
        ),
        "sub_meme": "(roasted from your DeepReflect memory — gentle version)",
        "bubbles": [
            {"n": str(score), "k": "Vibe score"},
            {"n": str(top[0].ask_count if top else 0) + "×", "k": f"「{concept_name}」"},
            {"n": str(stats["weekly_turns"]), "k": "This week"},
            {"n": str(len(top)), "k": "Repeat topics"},
        ],
        "lead": f"You don't learn — you <em>re-ask</em> about {concept_name}.",
        "vibe_body": (
            f"DeepReflect caught you circling the same topics. "
            f"That's not curiosity, that's <em>concept hoarding</em> with extra steps."
        ),
        "bars": [
            {"name": "Debugging in circles", "pct": 85},
            {"name": "Framework tourism", "pct": 60},
            {"name": "AI reads docs for you", "pct": 75},
            {"name": "Actually shipping", "pct": 25},
        ],
        "pills": [f"{c.name} ×{c.ask_count}" for c in top[:4]] or ["no pills yet"],
        "taxonomy": [
            {
                "emoji": "🔄",
                "title": f"「{c.name}」 loop",
                "desc": f"Asked {c.ask_count}× — the AI remembers even if you don't.",
            }
            for c in top[:4]
        ]
        or [
            {"emoji": "🔄", "title": "Empty archive", "desc": "Import more chats to get roasted properly."}
        ],
        "chaotic_quote": f"Can you explain {concept_name} again but simpler?",
        "chaotic_note": "👈 peak déjà vu energy",
        "mini_cards": [
            {
                "emoji": "🔁",
                "title": "Top offender",
                "body": f"<strong>{concept_name}</strong> — {top[0].ask_count if top else 0} visits.",
            },
            {
                "emoji": "📚",
                "title": "Study mode?",
                "body": "You tracked concepts but the vibes say <em>panic googling</em>.",
            },
        ],
        "risk_line": "⚠️ Risk: asking the same question until the model gaslights you with confidence.",
        "coaster_labels": ["hope", "paste", "confused", "repeat", "sleep?"],
        "dependency_html": (
            f"• <strong>{stats['total_turns']}</strong> AI turns on record — copilot energy.<br>"
            "• Split: whatever tool was open during the spiral.<br>"
            "• Would've Googled in 2019 index: <strong>8/10</strong>"
        ),
        "award_paragraphs": [
            "You treat AI like infinite patience with a search bar attached.",
            "The honest win: you showed up enough times to generate this roast.",
            "Next quest: pick one concept and read docs before the 4th ask.",
        ],
        "final_line": f"Vibe score <strong>{score}/100</strong> · delete one repeated question from your vocabulary",
        "footer_quote": '"Chronic re-asking. Prognosis: more prompts, slightly fewer epiphanies."',
        "footer_sign": f"— Vibe Roast · DeepReflect · {datetime.now().strftime('%Y-%m-%d')}",
    }


async def _generate_roast_data(concepts, stats, turns, llm: LLMClient) -> dict:
    prompt = _build_context(concepts, stats, turns)
    try:
        raw = await llm.complete(_ROAST_SYSTEM, prompt, max_tokens=2500)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group())
            labels = data.get("coaster_labels") or []
            data["coaster_labels"] = [
                {"x": _COASTER_X[i], "text": labels[i] if i < len(labels) else "…"}
                for i in range(5)
            ]
            return data
    except Exception:
        pass
    fb = _fallback_data(concepts, stats)
    fb["coaster_labels"] = [
        {"x": _COASTER_X[i], "text": fb["coaster_labels"][i]}
        for i in range(5)
    ]
    return fb


_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html", "xml")),
)


async def generate_roast_html(
    session: Session,
    llm: LLMClient,
    out_dir: Path | None = None,
) -> Path:
    stats = get_stats(session)
    concepts = get_concepts(session, min_ask_count=2)[:10]
    turns = get_turns(session, limit=40)

    roast_data = await _generate_roast_data(concepts, stats, turns, llm)

    template = _env.get_template("vibe_roast.html")
    html = template.render(data=roast_data)

    if out_dir is None:
        out_dir = Path.home() / ".deepreflect" / "data" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"roast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
