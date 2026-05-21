"""Read Claude Code sessions from ~/.claude/projects/**/*.jsonl (standalone)."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .text_util import extract_text
from .turn import Turn

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def collect_claude_turns() -> list[Turn]:
    turns: list[Turn] = []
    if not PROJECTS_DIR.exists():
        return turns
    for jsonl in PROJECTS_DIR.rglob("*.jsonl"):
        turns.extend(_parse_jsonl(jsonl))
    return turns


def _parse_jsonl(path: Path) -> list[Turn]:
    if not path.exists():
        return []

    raw_entries: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                raw_entries.append(json.loads(line))
    except Exception:
        return []

    user_entries = [e for e in raw_entries if e.get("type") == "user"]
    assistant_entries = [e for e in raw_entries if e.get("type") == "assistant"]
    asst_by_parent: dict[str, list[dict]] = defaultdict(list)
    for ae in assistant_entries:
        parent = ae.get("parentUuid")
        if parent:
            asst_by_parent[parent].append(ae)

    turns: list[Turn] = []
    session_id = path.stem

    for ue in user_entries:
        if ue.get("isSidechain"):
            continue
        user_text = extract_text(ue.get("message", {}).get("content", ""))
        if not user_text:
            continue
        ts_str = ue.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue
        replies = asst_by_parent.get(ue.get("uuid", ""), [])
        ai_texts = [
            extract_text(ae.get("message", {}).get("content", []))
            for ae in replies
        ]
        ai_texts = [t for t in ai_texts if t]
        turns.append(
            Turn(
                source="claude-code",
                session_id=session_id,
                timestamp=ts,
                user_prompt=user_text,
                ai_response="\n\n".join(ai_texts),
                cwd=ue.get("cwd", ""),
                extra=json.dumps({"project": path.parent.name}),
            )
        )
    return turns
