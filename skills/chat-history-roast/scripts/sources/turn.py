"""Minimal turn record for standalone extract scripts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    source: str
    session_id: str
    timestamp: datetime
    user_prompt: str
    ai_response: str = ""
    cwd: str = ""
    extra: str = "{}"
