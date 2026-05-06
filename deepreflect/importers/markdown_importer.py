"""Import conversations from plain markdown files.

Expected format:
  ## User
  <prompt text>

  ## Assistant
  <response text>

  ## User
  ...
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from deepreflect.importers.base import ImporterPlugin
from deepreflect.memory.models import ConversationTurn

_ROLE_RE = re.compile(r"^#+\s*(user|human|assistant|ai|claude)\s*$", re.IGNORECASE)


class MarkdownImporter(ImporterPlugin):
    name = "Markdown"
    source_id = "markdown"

    def detect(self, path: str) -> bool:
        return Path(path).suffix.lower() in (".md", ".markdown", ".txt")

    def parse(self, path: str) -> list[ConversationTurn]:
        text = Path(path).read_text(encoding="utf-8")
        return _parse_markdown(text, source_path=path)


def _parse_markdown(text: str, source_path: str = "") -> list[ConversationTurn]:
    lines = text.splitlines()
    segments: list[tuple[str, str]] = []  # (role, content)
    current_role = ""
    current_lines: list[str] = []

    for line in lines:
        m = _ROLE_RE.match(line.strip())
        if m:
            if current_role and current_lines:
                segments.append((current_role, "\n".join(current_lines).strip()))
            current_role = m.group(1).lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_role and current_lines:
        segments.append((current_role, "\n".join(current_lines).strip()))

    turns: list[ConversationTurn] = []
    session_id = Path(source_path).stem
    now = datetime.now(timezone.utc)

    i = 0
    while i < len(segments):
        role, content = segments[i]
        if role in ("user", "human") and content:
            ai_response = ""
            if i + 1 < len(segments) and segments[i + 1][0] in ("assistant", "ai", "claude"):
                ai_response = segments[i + 1][1]
                i += 1
            turns.append(
                ConversationTurn(
                    source="markdown",
                    session_id=session_id,
                    timestamp=now,
                    user_prompt=content,
                    ai_response=ai_response,
                    cwd="",
                )
            )
        i += 1

    return turns
