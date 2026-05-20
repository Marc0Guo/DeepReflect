from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, and_, col, create_engine, func, select, text

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


# --- Dashboard filters ---

WEAK_ASK_THRESHOLD = 4  # matches weak_score >= 0.4 in ConceptTable


@dataclass
class DashboardFilters:
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    source: Optional[str] = None
    concept: Optional[str] = None
    status: Optional[str] = None  # "weak" | "solved"


def resolve_period(period: Optional[str]) -> tuple[Optional[datetime], Optional[datetime]]:
    if not period or period == "all":
        return None, None
    now = datetime.now(timezone.utc)
    deltas = {"day": 1, "week": 7, "month": 30, "year": 365}
    days = deltas.get(period)
    if days is None:
        return None, None
    return now - timedelta(days=days), now


def _turn_filter_clauses(filters: DashboardFilters) -> list:
    clauses = []
    if filters.since:
        clauses.append(ConversationTurn.timestamp >= filters.since)
    if filters.until:
        clauses.append(ConversationTurn.timestamp <= filters.until)
    if filters.source:
        clauses.append(ConversationTurn.source == filters.source)
    return clauses


def filters_are_active(filters: DashboardFilters) -> bool:
    return any(
        [
            filters.since,
            filters.until,
            filters.source,
            filters.concept,
            filters.status,
        ]
    )


def get_available_sources(session: Session) -> list[str]:
    rows = session.exec(
        select(ConversationTurn.source)
        .distinct()
        .order_by(ConversationTurn.source)
    ).all()
    return list(rows)


def get_filtered_concepts(
    session: Session,
    filters: DashboardFilters,
    min_ask_count: int = 1,
    limit: int = 100,
) -> list[dict]:
    mention_count = func.count(col(ConceptMention.id)).label("period_ask_count")
    stmt = (
        select(
            Concept,
            mention_count,
            func.max(ConversationTurn.timestamp).label("last_seen"),
        )
        .join(ConceptMention, ConceptMention.concept_id == Concept.id)
        .join(ConversationTurn, ConversationTurn.id == ConceptMention.turn_id)
    )
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)
    if filters.concept:
        stmt = stmt.where(Concept.name.contains(filters.concept.lower().strip()))
    stmt = stmt.group_by(col(Concept.id)).having(mention_count >= min_ask_count)
    if filters.status == "weak":
        stmt = stmt.having(mention_count >= WEAK_ASK_THRESHOLD)
    elif filters.status == "solved":
        stmt = stmt.having(mention_count < WEAK_ASK_THRESHOLD)
    stmt = stmt.order_by(mention_count.desc()).limit(limit)
    rows = session.exec(stmt).all()
    return [
        {
            "id": concept.id,
            "name": concept.name,
            "category": concept.category,
            "ask_count": int(count),
            "weak_score": min(int(count) / 10.0, 1.0),
            "last_seen": last_seen.isoformat() if last_seen else None,
        }
        for concept, count, last_seen in rows
    ]


def get_filtered_stats(session: Session, filters: DashboardFilters) -> dict:
    turn_clauses = _turn_filter_clauses(filters)
    turn_count_stmt = select(func.count(col(ConversationTurn.id)))
    for clause in turn_clauses:
        turn_count_stmt = turn_count_stmt.where(clause)
    total_turns = session.exec(turn_count_stmt).one()

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_stmt = select(func.count(col(ConversationTurn.id))).where(
        ConversationTurn.timestamp >= week_ago
    )
    if filters.source:
        weekly_stmt = weekly_stmt.where(ConversationTurn.source == filters.source)
    weekly_turns = session.exec(weekly_stmt).one()

    sources_stmt = select(
        ConversationTurn.source, func.count(col(ConversationTurn.id))
    ).group_by(ConversationTurn.source)
    for clause in turn_clauses:
        sources_stmt = sources_stmt.where(clause)
    sources = session.exec(sources_stmt).all()

    concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=10_000)
    concept_ids = [c["id"] for c in concepts]

    if concept_ids:
        flashcard_stmt = select(func.count(col(Flashcard.id))).where(
            col(Flashcard.concept_id).in_(concept_ids)
        )
        total_flashcards = session.exec(flashcard_stmt).one()
    elif filters_are_active(filters):
        total_flashcards = 0
    else:
        total_flashcards = session.exec(select(func.count(col(Flashcard.id)))).one()

    return {
        "total_turns": total_turns,
        "total_concepts": len(concepts),
        "total_flashcards": total_flashcards,
        "weekly_turns": weekly_turns,
        "period_turns": total_turns if filters.since or filters.until else weekly_turns,
        "sources": {src: cnt for src, cnt in sources},
        "available_sources": get_available_sources(session),
        "filters_active": filters_are_active(filters),
    }


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
        "period_turns": weekly_turns,
        "sources": {src: cnt for src, cnt in sources},
        "available_sources": get_available_sources(session),
        "filters_active": False,
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
