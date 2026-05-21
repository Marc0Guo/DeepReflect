#!/usr/bin/env python3
"""Extract recent Cursor chat history (composer + agent transcripts + workspace).

Standalone — no DeepReflect install required.

  python3 skills/chat-history-roast/scripts/extract_cursor.py --limit 50
  python3 skills/chat-history-roast/scripts/extract_cursor.py --format json > cursor.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _extract_common import add_extract_args, emit, finalize_records


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract recent Cursor chats only.")
    add_extract_args(ap, default_limit=50)
    args = ap.parse_args()

    from sources.cursor_storage import collect_cursor_turns

    print("Scanning Cursor local storage (this can take 30–60s)…", file=sys.stderr)
    turns = collect_cursor_turns()
    meta, records = finalize_records(turns, source_label="cursor", limit=args.limit)
    emit(meta, records, args.format)


if __name__ == "__main__":
    main()
