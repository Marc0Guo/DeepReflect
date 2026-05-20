"""Import conversations from Cursor IDE storage.

Modern Cursor (2.x / 3.x) stores chat in:
  globalStorage/state.vscdb → cursorDiskKV
    composerData:{composerId}   conversation metadata + message order
    bubbleId:{composerId}:{id}  individual message content

Agent transcripts (newer) also live under:
  ~/.cursor/projects/<project>/agent-transcripts/<id>/<id>.jsonl
"""
from __future__ import annotations

import json
import platform
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from deepreflect.importers.base import ImporterPlugin, _extract_text
from deepreflect.memory.models import ConversationTurn

_BUBBLE_USER = 1
_BUBBLE_ASSISTANT = 2


def _cursor_user_data_root() -> Path | None:
    sys = platform.system()
    if sys == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor" / "User"
    if sys == "Linux":
        return Path.home() / ".config" / "Cursor" / "User"
    if sys == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Cursor" / "User"
    return None


def _cursor_storage_root() -> Path | None:
    root = _cursor_user_data_root()
    if not root:
        return None
    return root / "workspaceStorage"


def _global_storage_db() -> Path | None:
    root = _cursor_user_data_root()
    if not root:
        return None
    path = root / "globalStorage" / "state.vscdb"
    return path if path.exists() else None


def _cursor_projects_root() -> Path:
    return Path.home() / ".cursor" / "projects"


def _read_vscdb(path: Path) -> list[tuple[str, str]]:
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        try:
            return [(r[0], r[1]) for r in conn.execute("SELECT key, value FROM ItemTable").fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def _read_global_kv(key: str) -> str | None:
    db = _global_storage_db()
    if not db:
        return None
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
        try:
            row = conn.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    except Exception:
        return None


def _list_composer_ids() -> list[str]:
    ids: set[str] = set()
    db = _global_storage_db()
    if db:
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
            try:
                rows = conn.execute(
                    "SELECT key FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
                ).fetchall()
                for (key,) in rows:
                    ids.add(key.split(":", 1)[1])
            finally:
                conn.close()
        except Exception:
            pass

    # Cursor 3.0 central index
    global_db = _global_storage_db()
    if global_db:
        for key, value in _read_vscdb(global_db):
            if key == "composer.composerHeaders":
                try:
                    data = json.loads(value)
                    for composer in data.get("allComposers", []):
                        if cid := composer.get("composerId"):
                            ids.add(cid)
                except Exception:
                    pass

    # Cursor 2.x per-workspace index
    root = _cursor_storage_root()
    if root and root.exists():
        for vscdb in root.rglob("state.vscdb"):
            for key, value in _read_vscdb(vscdb):
                if key != "composer.composerData":
                    continue
                try:
                    data = json.loads(value)
                except Exception:
                    continue
                for composer in data.get("allComposers", []):
                    if cid := composer.get("composerId"):
                        ids.add(cid)
                for cid in data.get("selectedComposerIds", []):
                    ids.add(cid)
                for cid in data.get("lastFocusedComposerIds", []):
                    ids.add(cid)

    return sorted(ids)


def _ts(raw) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    if isinstance(raw, (int, float)):
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


def _extract_lexical_text(raw: str) -> str:
    if not raw or not raw.strip().startswith("{"):
        return raw.strip() if isinstance(raw, str) else ""
    try:
        data = json.loads(raw)
    except Exception:
        return raw.strip()

    parts: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            text = node.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
            for child in node.get("children") or []:
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data.get("root", data))
    return "".join(parts).strip()


def _extract_bubble_text(bubble: dict) -> str:
    text = bubble.get("text") or bubble.get("rawText") or ""
    if isinstance(text, str) and text.strip():
        cleaned = _extract_lexical_text(text)
        if cleaned:
            return cleaned
    rich = bubble.get("richText")
    if isinstance(rich, str) and rich.strip():
        cleaned = _extract_lexical_text(rich)
        if cleaned:
            return cleaned
    return ""


def _parse_composer(composer_id: str) -> list[ConversationTurn]:
    raw = _read_global_kv(f"composerData:{composer_id}")
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except Exception:
        return []

    headers = data.get("fullConversationHeadersOnly") or []
    conv_map = data.get("conversationMap") or {}
    default_ts = _ts(data.get("createdAt"))
    turns: list[ConversationTurn] = []

    pending_user: tuple[str, datetime] | None = None
    pending_ai: list[str] = []

    def flush() -> None:
        nonlocal pending_user, pending_ai
        if not pending_user:
            pending_ai = []
            return
        user_text, user_ts = pending_user
        ai_response = "\n\n".join(t for t in pending_ai if t).strip()
        turns.append(
            ConversationTurn(
                source="cursor",
                session_id=composer_id,
                timestamp=user_ts,
                user_prompt=user_text,
                ai_response=ai_response,
                extra=json.dumps({"composer_id": composer_id, "name": data.get("name", "")}),
            )
        )
        pending_user = None
        pending_ai = []

    for header in headers:
        bubble_id = header.get("bubbleId") or header.get("id")
        bubble_type = header.get("type")
        if not bubble_id:
            continue

        bubble = conv_map.get(bubble_id)
        if bubble is None:
            raw_bubble = _read_global_kv(f"bubbleId:{composer_id}:{bubble_id}")
            if raw_bubble:
                try:
                    bubble = json.loads(raw_bubble)
                except Exception:
                    bubble = {}
            else:
                bubble = {}

        text = _extract_bubble_text(bubble)
        ts = _ts(
            bubble.get("createdAt")
            or bubble.get("lastUpdatedAt")
            or header.get("lastUpdatedAt")
            or default_ts
        )
        role_type = bubble_type if bubble_type in (_BUBBLE_USER, _BUBBLE_ASSISTANT) else bubble.get("type")

        if role_type == _BUBBLE_USER:
            flush()
            if text:
                pending_user = (text, ts)
        elif role_type == _BUBBLE_ASSISTANT:
            if text:
                pending_ai.append(text)
            elif pending_user and not pending_ai:
                # Keep turn even if first assistant bubble is tool-only
                pass

    flush()
    return turns


def _parse_agent_transcript(path: Path) -> list[ConversationTurn]:
    if not path.exists() or path.suffix != ".jsonl":
        return []

    session_id = path.stem
    turns: list[ConversationTurn] = []
    pending_user: tuple[str, datetime] | None = None
    pending_ai: list[str] = []
    line_no = 0

    def flush() -> None:
        nonlocal pending_user, pending_ai
        if not pending_user:
            pending_ai = []
            return
        user_text, user_ts = pending_user
        turns.append(
            ConversationTurn(
                source="cursor",
                session_id=session_id,
                timestamp=user_ts,
                user_prompt=user_text,
                ai_response="\n\n".join(t for t in pending_ai if t).strip(),
                extra=json.dumps({"transcript": str(path)}),
            )
        )
        pending_user = None
        pending_ai = []

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            line_no += 1
            try:
                entry = json.loads(line)
            except Exception:
                continue

            role = str(entry.get("role") or entry.get("type") or "").lower()
            content = entry.get("message", {}).get("content", entry.get("content", ""))
            text = _extract_text(content)
            if not text:
                continue

            ts = _ts(entry.get("timestamp") or entry.get("createdAt"))
            if not entry.get("timestamp") and not entry.get("createdAt"):
                ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

            if role in ("user", "human"):
                flush()
                pending_user = (text, ts)
            elif role in ("assistant", "ai", "bot"):
                if pending_user:
                    pending_ai.append(text)
    except Exception:
        return turns

    flush()
    return turns


def _parse_workspace_generations(vscdb_path: Path) -> list[ConversationTurn]:
    """Fallback: user prompts only when bubble storage is unavailable."""
    rows = _read_vscdb(vscdb_path)
    for key, value in rows:
        if key != "aiService.generations":
            continue
        try:
            generations = json.loads(value)
        except Exception:
            return []
        session_id = vscdb_path.parent.name
        turns = []
        for gen in generations:
            text = str(gen.get("textDescription") or gen.get("text") or "").strip()
            if not text:
                continue
            turns.append(
                ConversationTurn(
                    source="cursor",
                    session_id=session_id,
                    timestamp=_ts(gen.get("unixMs")),
                    user_prompt=text,
                    ai_response="",
                    extra=json.dumps({"generation_uuid": gen.get("generationUUID", "")}),
                )
            )
        return turns
    return []


def _parse_vscdb(path: Path) -> list[ConversationTurn]:
    """Legacy workspace parser — kept as fallback."""
    return _parse_workspace_generations(path)


class CursorImporter(ImporterPlugin):
    name = "Cursor"
    source_id = "cursor"

    def detect(self, path: str) -> bool:
        p = Path(path)
        if p.suffix == ".vscdb" and p.exists():
            return True
        if p.suffix == ".jsonl" and "agent-transcripts" in p.parts:
            return True
        return False

    def parse(self, path: str) -> list[ConversationTurn]:
        p = Path(path)
        if p.suffix == ".jsonl":
            return _parse_agent_transcript(p)
        if p.name == "state.vscdb":
            return _parse_vscdb(p)
        return []

    def import_all(self) -> list[ConversationTurn]:
        turns: list[ConversationTurn] = []
        seen: set[tuple[str, str, str]] = set()

        def add(items: list[ConversationTurn]) -> None:
            for turn in items:
                key = (
                    turn.source,
                    turn.session_id,
                    turn.timestamp.isoformat(),
                )
                if key in seen:
                    continue
                seen.add(key)
                turns.append(turn)

        for composer_id in _list_composer_ids():
            add(_parse_composer(composer_id))

        projects_root = _cursor_projects_root()
        if projects_root.exists():
            for transcript in projects_root.rglob("agent-transcripts/*/*.jsonl"):
                add(_parse_agent_transcript(transcript))

        # Last-resort fallback for workspaces without global bubble data
        root = _cursor_storage_root()
        if root and root.exists():
            for vscdb in root.rglob("state.vscdb"):
                add(_parse_workspace_generations(vscdb))

        return turns

    def list_workspaces(self) -> list[str]:
        root = _cursor_storage_root()
        if not root or not root.exists():
            return []
        return [p.name for p in root.iterdir() if p.is_dir() and (p / "state.vscdb").exists()]
