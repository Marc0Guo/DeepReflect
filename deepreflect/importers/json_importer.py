"""Import conversations from a generic JSON file.

Accepts two shapes:
  1. Array of {user_prompt, ai_response, timestamp?, source?, session_id?}
  2. ChatGPT-style export: {conversations: [{mapping: {...}}]}
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from deepreflect.importers.base import ImporterPlugin, _extract_text
from deepreflect.memory.models import ConversationTurn


class JsonImporter(ImporterPlugin):
    name = "JSON"
    source_id = "json"

    def detect(self, path: str) -> bool:
        return Path(path).suffix.lower() == ".json"

    def parse(self, path: str) -> list[ConversationTurn]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            return _parse_generic(data, path)
        if isinstance(data, dict) and "conversations" in data:
            return _parse_chatgpt(data, path)
        return []


def _parse_generic(data: list[dict], source_path: str) -> list[ConversationTurn]:
    turns: list[ConversationTurn] = []
    session_id = Path(source_path).stem
    now = datetime.now(timezone.utc)
    for item in data:
        user_prompt = item.get("user_prompt") or item.get("human") or item.get("user", "")
        ai_response = item.get("ai_response") or item.get("assistant") or item.get("ai", "")
        if not user_prompt:
            continue
        ts_raw = item.get("timestamp")
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")) if ts_raw else now
        except Exception:
            ts = now
        turns.append(
            ConversationTurn(
                source=item.get("source", "json"),
                session_id=item.get("session_id", session_id),
                timestamp=ts,
                user_prompt=str(user_prompt),
                ai_response=str(ai_response),
            )
        )
    return turns


def _parse_chatgpt(data: dict, source_path: str) -> list[ConversationTurn]:
    """Parse ChatGPT export format."""
    turns: list[ConversationTurn] = []
    now = datetime.now(timezone.utc)

    for convo in data.get("conversations", []):
        mapping = convo.get("mapping", {})
        session_id = convo.get("id", Path(source_path).stem)

        # Build parent→children tree to walk in order
        nodes: dict[str, dict] = mapping
        root_ids = [nid for nid, node in nodes.items() if not node.get("parent")]

        def walk(node_id: str) -> list[dict]:
            node = nodes.get(node_id, {})
            result = [node]
            for child_id in node.get("children", []):
                result.extend(walk(child_id))
            return result

        ordered = []
        for root in root_ids:
            ordered.extend(walk(root))

        user_msg = None
        for node in ordered:
            msg = node.get("message")
            if not msg:
                continue
            role = msg.get("author", {}).get("role", "")
            content = msg.get("content", {})
            parts = content.get("parts", [])
            text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
            ts_raw = msg.get("create_time")
            try:
                ts = datetime.fromtimestamp(float(ts_raw), tz=timezone.utc) if ts_raw else now
            except Exception:
                ts = now

            if role == "user" and text:
                user_msg = (text, ts)
            elif role == "assistant" and text and user_msg:
                turns.append(
                    ConversationTurn(
                        source="chatgpt",
                        session_id=session_id,
                        timestamp=user_msg[1],
                        user_prompt=user_msg[0],
                        ai_response=text,
                    )
                )
                user_msg = None

    return turns
