from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, and_, create_engine, func, select, text

from deepreflect.memory.models import (
    Concept,
    ConceptMention,
    ConversationTurn,
    Flashcard,
    GeneratedContent,
)

_engines: dict[str, object] = {}


def get_engine(db_path: Path):
    key = str(db_path)
    if key not in _engines:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(engine)
        _engines[key] = engine
    return _engines[key]


def get_session(db_path: Path):
    """Return a Session context manager for the given db_path."""
    from contextlib import contextmanager

    @contextmanager
    def _session():
        engine = get_engine(db_path)
        with Session(engine) as session:
            yield session

    return _session()


# --- Conversation turns ---

def upsert_turn(session: Session, turn: ConversationTurn) -> ConversationTurn:
    existing = session.exec(
        select(ConversationTurn).where(
            and_(
                ConversationTurn.session_id == turn.session_id,
                ConversationTurn.timestamp == turn.timestamp,
                ConversationTurn.source == turn.source,
            )
        )
    ).first()
    if existing:
        return existing
    session.add(turn)
    session.commit()
    session.refresh(turn)
    return turn


def get_turns(
    session: Session,
    source: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    analyzed: Optional[bool] = None,
    limit: int = 1000,
) -> list[ConversationTurn]:
    stmt = select(ConversationTurn)
    if source:
        stmt = stmt.where(ConversationTurn.source == source)
    if since:
        stmt = stmt.where(ConversationTurn.timestamp >= since)
    if until:
        stmt = stmt.where(ConversationTurn.timestamp <= until)
    if analyzed is not None:
        stmt = stmt.where(ConversationTurn.analyzed == analyzed)
    stmt = stmt.order_by(ConversationTurn.timestamp.desc()).limit(limit)
    return list(session.exec(stmt))


def get_unanalyzed_turns(session: Session) -> list[ConversationTurn]:
    return get_turns(session, analyzed=False)


# --- Concepts ---

def get_or_create_concept(session: Session, name: str, category: str = "") -> Concept:
    concept = session.exec(select(Concept).where(Concept.name == name)).first()
    if not concept:
        concept = Concept(name=name, category=category, first_seen=datetime.now(timezone.utc))
        session.add(concept)
        session.commit()
        session.refresh(concept)
    return concept


def record_mention(
    session: Session, turn: ConversationTurn, concept: Concept, confidence: float = 1.0
) -> None:
    mention = ConceptMention(
        turn_id=turn.id, concept_id=concept.id, confidence=confidence
    )
    session.add(mention)

    concept.ask_count += 1
    concept.last_seen = turn.timestamp
    if not concept.first_seen:
        concept.first_seen = turn.timestamp

    # weak_score = clamp(ask_count / 10, 0, 1) — decays when not asked recently
    concept.weak_score = min(concept.ask_count / 10.0, 1.0)
    session.add(concept)
    session.commit()


def get_concepts(
    session: Session,
    min_ask_count: int = 0,
    limit: int = 200,
) -> list[Concept]:
    stmt = (
        select(Concept)
        .where(Concept.ask_count >= min_ask_count)
        .order_by(Concept.ask_count.desc())
        .limit(limit)
    )
    return list(session.exec(stmt))


def get_concept_turns(session: Session, concept_id: int) -> list[ConversationTurn]:
    stmt = (
        select(ConversationTurn)
        .join(ConceptMention, ConceptMention.turn_id == ConversationTurn.id)
        .where(ConceptMention.concept_id == concept_id)
        .order_by(ConversationTurn.timestamp.desc())
    )
    return list(session.exec(stmt))


def get_co_occurrences(session: Session) -> list[tuple[int, int, int]]:
    """Return (concept_a_id, concept_b_id, co_count) pairs from same session."""
    stmt = """
        SELECT a.concept_id, b.concept_id, COUNT(*) as co_count
        FROM conceptmention a
        JOIN conceptmention b ON a.turn_id = b.turn_id AND a.concept_id < b.concept_id
        GROUP BY a.concept_id, b.concept_id
        HAVING co_count >= 1
        ORDER BY co_count DESC
        LIMIT 500
    """
    rows = session.exec(text(stmt)).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


# --- Flashcards ---

def save_flashcard(session: Session, card: Flashcard) -> Flashcard:
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def get_flashcards(session: Session, concept_id: Optional[int] = None) -> list[Flashcard]:
    stmt = select(Flashcard)
    if concept_id is not None:
        stmt = stmt.where(Flashcard.concept_id == concept_id)
    stmt = stmt.order_by(Flashcard.created_at.desc())
    return list(session.exec(stmt))


# --- Stats ---

def get_stats(session: Session) -> dict:
    total_turns = session.exec(select(func.count(ConversationTurn.id))).one()
    total_concepts = session.exec(select(func.count(Concept.id))).one()
    total_flashcards = session.exec(select(func.count(Flashcard.id))).one()

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_turns = session.exec(
        select(func.count(ConversationTurn.id)).where(
            ConversationTurn.timestamp >= week_ago
        )
    ).one()

    sources = session.exec(
        select(ConversationTurn.source, func.count(ConversationTurn.id))
        .group_by(ConversationTurn.source)
    ).all()

    return {
        "total_turns": total_turns,
        "total_concepts": total_concepts,
        "total_flashcards": total_flashcards,
        "weekly_turns": weekly_turns,
        "sources": {src: cnt for src, cnt in sources},
    }


# --- Generated content history ---

def save_generated_content(
    session: Session,
    content_type: str,
    content: str,
    period: str = "",
    title: str = "",
) -> GeneratedContent:
    item = GeneratedContent(content_type=content_type, content=content, period=period, title=title)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_content_history(
    session: Session,
    content_type: str,
    limit: int = 50,
) -> list[GeneratedContent]:
    stmt = (
        select(GeneratedContent)
        .where(GeneratedContent.content_type == content_type)
        .order_by(GeneratedContent.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(stmt))
