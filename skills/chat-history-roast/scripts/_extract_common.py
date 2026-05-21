"""Shared helpers for chat-history-roast extract scripts."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


def turn_extra(turn) -> dict[str, Any]:
    raw = turn.extra or ""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def turn_to_record(turn, *, max_chars: int = 2500) -> dict[str, Any]:
    extra = turn_extra(turn)
    assistant = (turn.ai_response or "").strip()
    user = (turn.user_prompt or "").strip()
    if len(assistant) > max_chars:
        assistant = assistant[:max_chars] + "\n… [truncated]"
    if len(user) > max_chars:
        user = user[:max_chars] + "\n… [truncated]"
    return {
        "source": turn.source,
        "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
        "session_id": turn.session_id,
        "project": extra.get("project") or extra.get("name") or getattr(turn, "cwd", "") or "",
        "user": user,
        "assistant": assistant,
    }


def finalize_records(
    turns: list[Any],
    *,
    source_label: str,
    limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    turns = [t for t in turns if (t.user_prompt or "").strip()]
    turns.sort(
        key=lambda t: t.timestamp or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    total_found = len(turns)
    trimmed = turns[: max(1, limit)]
    meta = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "source": source_label,
        "limit": limit,
        "total_found": total_found,
        "returned": len(trimmed),
    }
    return meta, [turn_to_record(t) for t in trimmed]


def format_text(meta: dict[str, Any], records: list[dict[str, Any]]) -> str:
    src = meta.get("source", "?")
    lines = [
        f"# AI chat history — {src} ({meta['returned']} of {meta['total_found']}, newest first)",
        f"# extracted {meta['extracted_at']}",
        "",
    ]
    for rec in records:
        ts = rec.get("timestamp") or "unknown time"
        try:
            ts_display = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime(
                "%Y-%m-%d %H:%M"
            )
        except Exception:
            ts_display = ts
        if rec["source"] == "cursor":
            label = "Cursor"
        elif rec["source"] in ("claude-code", "claude"):
            label = "Claude Code"
        else:
            label = rec["source"]
        proj = rec.get("project") or rec.get("session_id") or ""
        lines.append(f"## {label} — {ts_display}" + (f" · {proj}" if proj else ""))
        lines.append(f"User: {rec['user']}")
        if rec.get("assistant"):
            lines.append(f"Assistant: {rec['assistant']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit(meta: dict[str, Any], records: list[dict[str, Any]], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({"meta": meta, "turns": records}, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(format_text(meta, records))


def add_extract_args(ap, *, default_limit: int = 50) -> None:
    ap.add_argument(
        "--limit",
        type=int,
        default=default_limit,
        help=f"Max user turns, newest first (default: {default_limit}). Use 20–80 for roasts; 100+ burns tokens.",
    )
    ap.add_argument("--format", choices=["text", "json"], default="text")
