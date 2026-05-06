from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from deepreflect.memory.models import ConversationTurn


class ImporterPlugin(ABC):
    name: str
    source_id: str

    @abstractmethod
    def detect(self, path: str) -> bool:
        """Return True if this importer can handle the given path."""

    @abstractmethod
    def parse(self, path: str) -> list[ConversationTurn]:
        """Parse and return normalized ConversationTurn list."""


def _extract_text(content) -> str:
    """Extract plain text from various Claude Code content shapes."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    pass  # skip thinking blocks
                elif block.get("type") == "tool_result":
                    for sub in block.get("content", []):
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            parts.append(sub.get("text", ""))
        return "\n".join(p for p in parts if p).strip()
    return str(content)
