#!/usr/bin/env python3
"""
DeepReflect turn hook  —  dr-turn.py
======================================
Works with  Cursor  AND  Claude Code  (same script, both platforms detected).

Flow per agent turn:
  1. Reads hook stdin JSON  (Cursor: messages array / Claude Code: transcript_path)
  2. Extracts the last user-prompt + AI-response from the conversation
  3. Parses the hidden tag  <!-- dr:{"t":[...],"d":"..."} -->  that Claude appended
  4. POSTs user_prompt + ai_response + topics + domain  to DeepReflect /ingest/raw-turn
     → turn stored as  analyzed=True  immediately — no second LLM call needed

Configuration:
  DR_URL   env var   (default: http://localhost:8000)

The hook exits silently if DeepReflect is not running or if no conversation
content is found.  It never blocks the agent.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DR_URL = os.environ.get("DR_URL", "http://localhost:8000").rstrip("/")

# Matches  <!-- dr:{"t":[...],"d":"..."} -->  with optional whitespace
_TAG_RE = re.compile(r"<!--\s*dr:(\{.*?\})\s*-->", re.DOTALL)


# ── Conversation extraction ───────────────────────────────────────────────────

def _text_from_content(content) -> str:
    """Normalise Anthropic-style content (string or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", block.get("content", ""))))
            else:
                parts.append(str(block))
        return " ".join(p for p in parts if p)
    return str(content or "")


def _from_transcript(path: str) -> tuple[str, str]:
    """Read the last user/assistant pair from a Claude Code JSONL transcript."""
    try:
        with open(path, encoding="utf-8") as fh:
            events = [json.loads(ln) for ln in fh if ln.strip()]
    except Exception:
        return "", ""

    user_msg = ai_msg = ""
    for ev in reversed(events):
        role = str(ev.get("role", ev.get("type", ""))).lower()
        content = _text_from_content(ev.get("content", ev.get("message", ""))).strip()
        if not content:
            continue
        if not ai_msg and role in ("assistant", "ai", "model"):
            ai_msg = content
        elif not user_msg and ai_msg and role in ("user", "human"):
            user_msg = content
            break
    return user_msg, ai_msg


def _from_messages(msgs: list) -> tuple[str, str]:
    """Extract last pair from an inline messages array (Cursor format)."""
    user_msg = ai_msg = ""
    for m in reversed(msgs):
        role = str(m.get("role", m.get("type", ""))).lower()
        content = _text_from_content(m.get("content", m.get("text", m.get("message", "")))).strip()
        if not content:
            continue
        if not ai_msg and role in ("assistant", "ai", "model"):
            ai_msg = content
        elif not user_msg and ai_msg and role in ("user", "human"):
            user_msg = content
            break
    return user_msg, ai_msg


def extract_turn(data: dict) -> tuple[str, str]:
    """Return (user_prompt, ai_response) — tries transcript path first, then inline."""
    # Claude Code provides transcript_path in every Stop event
    transcript_path = data.get("transcript_path", "")
    if transcript_path and os.path.isfile(transcript_path):
        u, a = _from_transcript(transcript_path)
        if a:
            return u, a

    # Cursor embeds messages inline (or uses other keys)
    for key in ("messages", "conversation", "turns", "history"):
        msgs = data.get(key)
        if isinstance(msgs, list) and msgs:
            u, a = _from_messages(msgs)
            if a:
                return u, a

    # Flat fallback fields
    u = str(data.get("user_prompt", data.get("user_message", data.get("query", ""))))
    a = str(data.get("ai_response", data.get("assistant_message", data.get("response", ""))))
    return u, a


# ── Tag parsing ───────────────────────────────────────────────────────────────

def parse_tag(text: str) -> tuple[list[str], str]:
    """Extract topics and domain from the hidden  <!-- dr:{...} -->  comment."""
    m = _TAG_RE.search(text)
    if not m:
        return [], "general"
    try:
        tag = json.loads(m.group(1))
        topics = [str(t).lower().strip() for t in tag.get("t", tag.get("topics", [])) if t]
        domain = str(tag.get("d", tag.get("domain", "general")))
        return topics, domain
    except (json.JSONDecodeError, TypeError, AttributeError):
        return [], "general"


def clean_response(text: str) -> str:
    """Remove the hidden tag from the stored response text."""
    return _TAG_RE.sub("", text).rstrip()


# ── HTTP call ─────────────────────────────────────────────────────────────────

def post_turn(payload: dict) -> None:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{DR_URL}/ingest/raw-turn",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=10)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    try:
        raw = sys.stdin.read()
        data: dict = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    user_prompt, ai_response = extract_turn(data)
    if not ai_response:
        sys.exit(0)

    topics, domain = parse_tag(ai_response)
    ai_clean = clean_response(ai_response)

    # Detect source platform
    hook_event = str(data.get("hook_event_name", "")).lower()
    source = "claude-code" if "transcript_path" in data or hook_event == "stop" and "transcript_path" in data else "cursor"
    if "transcript_path" in data:
        source = "claude-code"

    payload = {
        "user_prompt":  user_prompt[:4000],
        "ai_response":  ai_clean[:8000],
        "source":       source,
        "session_id":   str(data.get("session_id", "")),
        "cwd":          str(data.get("cwd", os.getcwd())),
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "topics":       topics or None,
        "domain":       domain if topics else None,
    }

    try:
        post_turn(payload)
    except urllib.error.URLError:
        pass  # DeepReflect not running — silent fail
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
