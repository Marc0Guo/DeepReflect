"""Read Cursor chats from local storage (standalone, no DeepReflect app)."""
from __future__ import annotations

import json
import platform
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .text_util import extract_text
from .turn import Turn


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


def _ts(raw, *, fallback: datetime | None = None) -> datetime | None:
    """Parse Cursor timestamps (ISO, unix ms, or numeric strings). Never invents 'now'."""
    if raw is None or raw == "":
        return fallback
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return fallback
        if s.isdigit():
            return _ts(int(s), fallback=fallback)
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return fallback
    if isinstance(raw, (int, float)):
        ts = float(raw)
        if ts > 1e15:
            ts /= 1_000_000.0
        elif ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return fallback
    return fallback


def _interpolate_time(start: datetime, end: datetime, index: int, total: int) -> datetime:
    if total <= 1:
        return start
    span_sec = (end - start).total_seconds()
    if span_sec <= 0:
        return start + timedelta(seconds=index)
    return start + timedelta(seconds=span_sec * index / (total - 1))


def _file_time_span(path: Path) -> tuple[datetime, datetime]:
    st = path.stat()
    end = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
    start_raw = getattr(st, "st_birthtime", None) or st.st_ctime
    start = datetime.fromtimestamp(start_raw, tz=timezone.utc)
    if start > end:
        start = end
    return start, end


def _bubble_timestamp(
    bubble: dict,
    header: dict,
    *,
    start: datetime,
    end: datetime,
    index: int,
    total: int,
) -> datetime:
    for raw in (
        bubble.get("createdAt"),
        bubble.get("lastUpdatedAt"),
        header.get("lastUpdatedAt"),
    ):
        parsed = _ts(raw)
        if parsed is not None:
            return parsed
    return _interpolate_time(start, end, index, total)


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


def _parse_composer(composer_id: str) -> list[Turn]:
    raw = _read_global_kv(f"composerData:{composer_id}")
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except Exception:
        return []

    headers = data.get("fullConversationHeadersOnly") or []
    conv_map = data.get("conversationMap") or {}
    now = datetime.now(timezone.utc)
    start = _ts(data.get("createdAt"), fallback=now) or now
    end = _ts(data.get("lastUpdatedAt"), fallback=start) or start
    if end < start:
        end = start
    n_headers = len(headers)
    turns: list[Turn] = []

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
            Turn(
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

    for idx, header in enumerate(headers):
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
        ts = _bubble_timestamp(
            bubble,
            header,
            start=start,
            end=end,
            index=idx,
            total=n_headers,
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


def _parse_agent_transcript(path: Path) -> list[Turn]:
    if not path.exists() or path.suffix != ".jsonl":
        return []

    session_id = path.stem
    events: list[tuple[str, str, object]] = []

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            role = str(entry.get("role") or entry.get("type") or "").lower()
            content = entry.get("message", {}).get("content", entry.get("content", ""))
            text = extract_text(content)
            if not text:
                continue
            events.append((role, text, entry.get("timestamp") or entry.get("createdAt")))
    except Exception:
        return []

    if not events:
        return []

    span_start, span_end = _file_time_span(path)
    user_indices = [i for i, (role, _, _) in enumerate(events) if role in ("user", "human")]
    user_times: dict[int, datetime] = {}
    for j, evt_idx in enumerate(user_indices):
        explicit = _ts(events[evt_idx][2])
        user_times[evt_idx] = explicit or _interpolate_time(
            span_start, span_end, j, len(user_indices)
        )

    turns: list[Turn] = []
    pending_user: tuple[str, datetime] | None = None
    pending_ai: list[str] = []

    def flush() -> None:
        nonlocal pending_user, pending_ai
        if not pending_user:
            pending_ai = []
            return
        user_text, user_ts = pending_user
        turns.append(
            Turn(
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

    for i, (role, text, _) in enumerate(events):
        if role in ("user", "human"):
            flush()
            pending_user = (text, user_times[i])
        elif role in ("assistant", "ai", "bot"):
            if pending_user:
                pending_ai.append(text)

    flush()
    return turns


def _parse_workspace_generations(vscdb_path: Path) -> list[Turn]:
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
                Turn(
                    source="cursor",
                    session_id=session_id,
                    timestamp=_ts(gen.get("unixMs"), fallback=datetime.now(timezone.utc)),
                    user_prompt=text,
                    ai_response="",
                    extra=json.dumps({"generation_uuid": gen.get("generationUUID", "")}),
                )
            )
        return turns
    return []


def _parse_vscdb(path: Path) -> list[Turn]:
    """Legacy workspace parser — kept as fallback."""
    return _parse_workspace_generations(path)



def collect_cursor_turns() -> list[Turn]:
    """Scan composer data, agent transcripts, and workspace fallbacks."""
    turns: list[Turn] = []
    seen: set[tuple[str, str, str]] = set()

    def add(items: list[Turn]) -> None:
        for turn in items:
            key = (turn.source, turn.session_id, turn.timestamp.isoformat())
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
    root = _cursor_storage_root()
    if root and root.exists():
        for vscdb in root.rglob("state.vscdb"):
            add(_parse_workspace_generations(vscdb))
    return turns
