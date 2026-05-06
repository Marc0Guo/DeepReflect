"""Import conversations from Claude Code JSONL session files.

Claude Code stores sessions in ~/.claude/projects/<project-slug>/<session-id>.jsonl
Each line is a JSON object with type: permission-mode | user | assistant | tool_use | tool_result
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from deepreflect.importers.base import ImporterPlugin, _extract_text
from deepreflect.memory.models import ConversationTurn

_PROJECTS_DIR = Path.home() / ".claude" / "projects"


class ClaudeCodeImporter(ImporterPlugin):
    name = "Claude Code"
    source_id = "claude-code"

    def detect(self, path: str) -> bool:
        p = Path(path)
        return p.suffix == ".jsonl" and p.exists()

    def parse(self, path: str) -> list[ConversationTurn]:
        return _parse_jsonl(Path(path))

    def import_all_projects(self) -> list[ConversationTurn]:
        """Import every session across all Claude Code projects."""
        turns: list[ConversationTurn] = []
        if not _PROJECTS_DIR.exists():
            return turns
        for jsonl in _PROJECTS_DIR.rglob("*.jsonl"):
            turns.extend(_parse_jsonl(jsonl))
        return turns

    def import_project(self, project_slug: str) -> list[ConversationTurn]:
        project_dir = _PROJECTS_DIR / project_slug
        turns: list[ConversationTurn] = []
        if not project_dir.exists():
            return turns
        for jsonl in project_dir.glob("*.jsonl"):
            turns.extend(_parse_jsonl(jsonl))
        return turns

    def import_session(self, session_id: str) -> list[ConversationTurn]:
        for jsonl in _PROJECTS_DIR.rglob(f"{session_id}.jsonl"):
            return _parse_jsonl(jsonl)
        return []

    def list_projects(self) -> list[str]:
        if not _PROJECTS_DIR.exists():
            return []
        return [p.name for p in _PROJECTS_DIR.iterdir() if p.is_dir()]


def _parse_jsonl(path: Path) -> list[ConversationTurn]:
    """Pair user + assistant messages from a JSONL session file into turns."""
    if not path.exists():
        return []

    raw_entries: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw_entries.append(json.loads(line))
    except Exception:
        return []

    # Build uuid→entry map and collect user/assistant entries
    by_uuid: dict[str, dict] = {}
    for entry in raw_entries:
        uid = entry.get("uuid")
        if uid:
            by_uuid[uid] = entry

    # Collect user prompts with their timestamps
    user_entries = [e for e in raw_entries if e.get("type") == "user"]
    assistant_entries = [e for e in raw_entries if e.get("type") == "assistant"]

    # Index assistant entries by parentUuid
    asst_by_parent: dict[str, list[dict]] = defaultdict(list)
    for ae in assistant_entries:
        parent = ae.get("parentUuid")
        if parent:
            asst_by_parent[parent].append(ae)

    turns: list[ConversationTurn] = []
    session_id = path.stem

    for ue in user_entries:
        if ue.get("isSidechain"):
            continue

        user_content = ue.get("message", {}).get("content", "")
        user_text = _extract_text(user_content)
        if not user_text:
            continue

        ts_str = ue.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue

        # Find the assistant reply(ies) whose parentUuid == this user uuid
        uuid = ue.get("uuid", "")
        replies = asst_by_parent.get(uuid, [])

        # Collect all text content from reply chain
        ai_texts: list[str] = []
        for ae in replies:
            content = ae.get("message", {}).get("content", [])
            text = _extract_text(content)
            if text:
                ai_texts.append(text)

        ai_response = "\n\n".join(ai_texts) if ai_texts else ""

        turns.append(
            ConversationTurn(
                source="claude-code",
                session_id=session_id,
                timestamp=ts,
                user_prompt=user_text,
                ai_response=ai_response,
                cwd=ue.get("cwd", ""),
                extra=json.dumps(
                    {
                        "version": ue.get("version", ""),
                        "git_branch": ue.get("gitBranch", ""),
                        "entrypoint": ue.get("entrypoint", ""),
                        "project": path.parent.name,
                    }
                ),
            )
        )

    return turns
