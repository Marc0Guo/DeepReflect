from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ConversationTurn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str  # claude-code | chatgpt | cursor | markdown | json
    session_id: str = ""
    timestamp: datetime
    user_prompt: str
    ai_response: str
    cwd: str = ""
    tags: str = "[]"  # JSON-encoded list[str]
    extra: str = "{}"  # JSON-encoded dict (named to avoid SQLAlchemy reserved 'metadata')
    analyzed: bool = False

    def get_tags(self) -> list[str]:
        return json.loads(self.tags)

    def set_tags(self, tags: list[str]) -> None:
        self.tags = json.dumps(tags)

    def get_extra(self) -> dict:
        return json.loads(self.extra)


class Concept(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    category: str = ""  # python | git | ml | general ...
    ask_count: int = 0
    weak_score: float = 0.0  # 0–1; higher = weaker / more repeated
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class ConceptMention(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    turn_id: int = Field(foreign_key="conversationturn.id", index=True)
    concept_id: int = Field(foreign_key="concept.id", index=True)
    confidence: float = 1.0


class Flashcard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    front: str
    back: str
    concept_id: Optional[int] = Field(default=None, foreign_key="concept.id")
    source_turn_id: Optional[int] = Field(default=None, foreign_key="conversationturn.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    review_count: int = 0
    last_reviewed: Optional[datetime] = None


class GeneratedContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content_type: str  # "quiz" | "study_guide"
    content: str  # JSON string for quiz, markdown text for study_guide
    period: str = ""  # e.g. "this week" for study guides
    title: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
