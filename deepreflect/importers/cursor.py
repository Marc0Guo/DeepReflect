"""Import conversations from Cursor's workspace storage databases.

Cursor (cursor.sh) stores chat history in VS Code-style SQLite databases:
  macOS:   ~/Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb
  Linux:   ~/.config/Cursor/User/workspaceStorage/*/state.vscdb
  Windows: %APPDATA%/Cursor/User/workspaceStorage/*/state.vscdb

Each .vscdb file is a SQLite database with an ItemTable(key TEXT, value TEXT).
Chat data is stored as JSON under one of several versioned keys.
"""
from __future__ import annotations

import json
import platform
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from deepreflect.importers.base import ImporterPlugin
from deepreflect.memory.models import ConversationTurn

# Known keys used across Cursor versions to store chat history
_CHAT_KEYS = [
    "aiPromptStore",
    "aiPromptStoreV2",
    "cursor.chat.sessions",
    "composerData",
    "workbench.panel.aichat.view.aichat.chatdata",
    "aiconversations",
    "aichat.sessions",
]


def _cursor_storage_root() -> Path | None:
    sys = platform.system()
    if sys == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
    if sys == "Linux":
        return Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage"
    if sys == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "Cursor" / "User" / "workspaceStorage"
    return None


def _read_vscdb(path: Path) -> list[tuple[str, str]]:
    """Return all (key, value) rows from ItemTable."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        try:
            rows = conn.execute("SELECT key, value FROM ItemTable").fetchall()
            return [(r[0], r[1]) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def _ts(raw) -> datetime:
    """Parse a timestamp from various formats to a timezone-aware datetime."""
    if raw is None:
        return datetime.now(timezone.utc)
    if isinstance(raw, (int, float)):
        # Unix milliseconds (Cursor uses ms) or seconds
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.now(timezone.utc)


def _parse_chat_json(data: object, session_id: str) -> list[ConversationTurn]:
    """Try all known Cursor JSON shapes and return ConversationTurns."""
    turns: list[ConversationTurn] = []

    if not isinstance(data, dict):
        return turns

    # Shape 1: {tabs: [{bubbles: [{type, text, lastUpdatedAt}]}]}
    tabs = data.get("tabs") or data.get("conversations") or []
    if isinstance(tabs, list):
        for tab in tabs:
            if not isinstance(tab, dict):
                continue
            tab_id = str(tab.get("tabId") or tab.get("id") or session_id)
            bubbles = tab.get("bubbles") or tab.get("messages") or []
            if not isinstance(bubbles, list):
                continue

            user_msg: tuple[str, datetime] | None = None
            for bubble in bubbles:
                if not isinstance(bubble, dict):
                    continue

                role = (bubble.get("type") or bubble.get("role") or "").lower()
                text = (
                    bubble.get("text")
                    or bubble.get("content")
                    or bubble.get("rawText")
                    or ""
                )
                if isinstance(text, list):
                    # content may be a list of blocks
                    text = " ".join(
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in text
                    ).strip()
                text = str(text).strip()
                ts = _ts(bubble.get("lastUpdatedAt") or bubble.get("timestamp") or bubble.get("createdAt"))

                if role in ("user", "human") and text:
                    user_msg = (text, ts)
                elif role in ("ai", "assistant", "bot") and text and user_msg:
                    turns.append(
                        ConversationTurn(
                            source="cursor",
                            session_id=tab_id,
                            timestamp=user_msg[1],
                            user_prompt=user_msg[0],
                            ai_response=text,
                        )
                    )
                    user_msg = None

    # Shape 2: flat {messages: [{role, content, timestamp}]}
    if not turns:
        messages = data.get("messages")
        if isinstance(messages, list):
            user_msg = None
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                role = str(msg.get("role") or "").lower()
                text = str(msg.get("content") or msg.get("text") or "").strip()
                ts = _ts(msg.get("timestamp") or msg.get("createdAt"))
                if role in ("user", "human") and text:
                    user_msg = (text, ts)
                elif role in ("assistant", "ai") and text and user_msg:
                    turns.append(
                        ConversationTurn(
                            source="cursor",
                            session_id=session_id,
                            timestamp=user_msg[1],
                            user_prompt=user_msg[0],
                            ai_response=text,
                        )
                    )
                    user_msg = None

    return turns


def _parse_vscdb(path: Path) -> list[ConversationTurn]:
    rows = _read_vscdb(path)
    session_id = path.parent.name  # the workspace hash

    for key, value in rows:
        if not any(k in key.lower() for k in ("chat", "prompt", "composer", "aichat", "conversation")):
            continue
        try:
            data = json.loads(value)
        except Exception:
            continue
        turns = _parse_chat_json(data, session_id)
        if turns:
            return turns

    return []


class CursorImporter(ImporterPlugin):
    name = "Cursor"
    source_id = "cursor"

    def detect(self, path: str) -> bool:
        p = Path(path)
        return p.suffix == ".vscdb" and p.exists()

    def parse(self, path: str) -> list[ConversationTurn]:
        return _parse_vscdb(Path(path))

    def import_all(self) -> list[ConversationTurn]:
        """Import all Cursor workspace chat histories from the default storage dir."""
        root = _cursor_storage_root()
        if not root or not root.exists():
            return []

        turns: list[ConversationTurn] = []
        for vscdb in root.rglob("state.vscdb"):
            turns.extend(_parse_vscdb(vscdb))
        return turns

    def list_workspaces(self) -> list[str]:
        root = _cursor_storage_root()
        if not root or not root.exists():
            return []
        return [p.name for p in root.iterdir() if p.is_dir() and (p / "state.vscdb").exists()]
