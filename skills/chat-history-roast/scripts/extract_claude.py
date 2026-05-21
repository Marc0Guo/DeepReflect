#!/usr/bin/env python3
"""Extract recent Claude Code session history (~/.claude/projects).

Standalone — no DeepReflect install required.

  python3 skills/chat-history-roast/scripts/extract_claude.py --limit 50
  python3 skills/chat-history-roast/scripts/extract_claude.py --format json > claude.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _extract_common import add_extract_args, emit, finalize_records


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract recent Claude Code chats only.")
    add_extract_args(ap, default_limit=50)
    args = ap.parse_args()

    from sources.claude_storage import collect_claude_turns

    turns = collect_claude_turns()
    meta, records = finalize_records(turns, source_label="claude-code", limit=args.limit)
    emit(meta, records, args.format)


if __name__ == "__main__":
    main()
