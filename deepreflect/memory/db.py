from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, and_, col, create_engine, delete, func, select, text

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


def _unanalyzed_stmt(
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    source: Optional[str] = None,
):
    stmt = select(ConversationTurn).where(ConversationTurn.analyzed == False)  # noqa: E712
    if since:
        stmt = stmt.where(ConversationTurn.timestamp >= since)
    if until:
        stmt = stmt.where(ConversationTurn.timestamp <= until)
    if source:
        stmt = stmt.where(ConversationTurn.source == source)
    return stmt


def count_unanalyzed_turns(
    session: Session,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    source: Optional[str] = None,
) -> int:
    stmt = select(func.count(col(ConversationTurn.id))).select_from(ConversationTurn)
    stmt = stmt.where(ConversationTurn.analyzed == False)  # noqa: E712
    if since:
        stmt = stmt.where(ConversationTurn.timestamp >= since)
    if until:
        stmt = stmt.where(ConversationTurn.timestamp <= until)
    if source:
        stmt = stmt.where(ConversationTurn.source == source)
    return int(session.exec(stmt).one())


def get_unanalyzed_date_bounds(
    session: Session,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Earliest and latest timestamps among unanalyzed turns."""
    stmt = select(
        func.min(ConversationTurn.timestamp),
        func.max(ConversationTurn.timestamp),
    ).where(ConversationTurn.analyzed == False)  # noqa: E712
    row = session.exec(stmt).one()
    return row[0], row[1]


def get_unanalyzed_turns_for_analysis(
    session: Session,
    limit: Optional[int] = 50,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    source: Optional[str] = None,
) -> list[ConversationTurn]:
    """Unanalyzed turns, newest first; optional cap by limit."""
    stmt = _unanalyzed_stmt(since, until, source)
    stmt = stmt.order_by(ConversationTurn.timestamp.desc())
    if limit is not None:
        stmt = stmt.limit(max(1, limit))
    return list(session.exec(stmt))


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


_SESSION_GAP = timedelta(minutes=30)
_DEFAULT_TURN_DURATION = timedelta(minutes=5)
_CHARS_PER_TOKEN = 4  # rough estimate when providers don't log usage


def estimate_tokens(text: str) -> int:
    """Estimate tokens from text length (~4 chars/token for English/code)."""
    if not text or not str(text).strip():
        return 0
    return max(1, len(str(text)) // _CHARS_PER_TOKEN)


def _sum_filtered_tokens(session: Session, filters: DashboardFilters) -> int:
    stmt = select(
        ConversationTurn.id,
        ConversationTurn.user_prompt,
        ConversationTurn.ai_response,
    )
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)

    if filters.concept or filters.status:
        concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=10_000)
        if not concepts:
            return 0
        concept_ids = [c["id"] for c in concepts]
        stmt = stmt.join(
            ConceptMention, ConceptMention.turn_id == ConversationTurn.id
        ).where(col(ConceptMention.concept_id).in_(concept_ids))

    seen_ids: set[int] = set()
    total = 0
    for turn_id, prompt, response in session.exec(stmt).all():
        if turn_id in seen_ids:
            continue
        seen_ids.add(turn_id)
        total += estimate_tokens(prompt) + estimate_tokens(response)
    return total


def _filtered_turn_rows(
    session: Session,
    filters: DashboardFilters,
) -> list[tuple[datetime, str]]:
    """(timestamp, session_id) for turns matching dashboard filters."""
    stmt = select(
        ConversationTurn.id,
        ConversationTurn.timestamp,
        ConversationTurn.session_id,
    )
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)

    if filters.concept or filters.status:
        concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=10_000)
        if not concepts:
            return []
        concept_ids = [c["id"] for c in concepts]
        stmt = stmt.join(
            ConceptMention, ConceptMention.turn_id == ConversationTurn.id
        ).where(col(ConceptMention.concept_id).in_(concept_ids))

    seen_ids: set[int] = set()
    result: list[tuple[datetime, str]] = []
    for turn_id, ts, session_id in session.exec(stmt).all():
        if turn_id in seen_ids:
            continue
        seen_ids.add(turn_id)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        result.append((ts, session_id or ""))
    return result


def _longest_day_streak(active_days: list[date]) -> int:
    if not active_days:
        return 0
    sorted_days = sorted(set(active_days))
    longest = 1
    current = 1
    for i in range(1, len(sorted_days)):
        if (sorted_days[i] - sorted_days[i - 1]).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _estimate_duration_seconds(rows: list[tuple[datetime, str]]) -> int:
    by_session: dict[str, list[datetime]] = defaultdict(list)
    for ts, session_id in rows:
        by_session[session_id].append(ts)

    total = timedelta(0)
    for timestamps in by_session.values():
        timestamps.sort()
        if len(timestamps) == 1:
            total += _DEFAULT_TURN_DURATION
            continue
        for i in range(len(timestamps) - 1):
            gap = timestamps[i + 1] - timestamps[i]
            if gap <= timedelta(0):
                total += _DEFAULT_TURN_DURATION
            else:
                total += min(gap, _SESSION_GAP)
        total += _DEFAULT_TURN_DURATION
    return int(total.total_seconds())


def get_dashboard_metrics(session: Session, filters: DashboardFilters) -> dict:
    rows = _filtered_turn_rows(session, filters)
    exchange_count = len(rows)

    if not rows:
        category_count = _count_filtered_categories(session, filters)
        return {
            "last_updated": None,
            "coverage_days": 0,
            "history_start": None,
            "history_end": None,
            "longest_streak_days": 0,
            "total_duration_seconds": 0,
            "category_count": category_count,
            "filtered_exchanges": 0,
            "filtered_tokens": 0,
        }

    timestamps = [ts for ts, _ in rows]
    active_days = [ts.date() for ts in timestamps]
    earliest = min(timestamps)
    latest = max(timestamps)
    coverage_days = (latest.date() - earliest.date()).days + 1

    return {
        "last_updated": latest.isoformat(),
        "coverage_days": coverage_days,
        "history_start": earliest.isoformat(),
        "history_end": latest.isoformat(),
        "longest_streak_days": _longest_day_streak(active_days),
        "total_duration_seconds": _estimate_duration_seconds(rows),
        "category_count": _count_filtered_categories(session, filters),
        "filtered_exchanges": exchange_count,
        "filtered_tokens": _sum_filtered_tokens(session, filters),
    }


def _count_filtered_categories(session: Session, filters: DashboardFilters) -> Optional[int]:
    """Distinct concept categories in filtered data; None if analysis has not run."""
    stmt = (
        select(func.count(func.distinct(Concept.category)))
        .select_from(Concept)
        .join(ConceptMention, ConceptMention.concept_id == Concept.id)
        .join(ConversationTurn, ConversationTurn.id == ConceptMention.turn_id)
        .where(Concept.category != "")
        .where(Concept.category.is_not(None))
    )
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)
    if filters.concept or filters.status:
        concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=10_000)
        if not concepts:
            return None
        concept_ids = [c["id"] for c in concepts]
        stmt = stmt.where(col(ConceptMention.concept_id).in_(concept_ids))
    count = session.exec(stmt).one()
    return int(count) if count else None


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

    metrics = get_dashboard_metrics(session, filters)

    return {
        "total_turns": metrics["filtered_exchanges"],
        "total_concepts": len(concepts),
        "total_flashcards": total_flashcards,
        "weekly_turns": weekly_turns,
        "period_turns": total_turns if filters.since or filters.until else weekly_turns,
        "sources": {src: cnt for src, cnt in sources},
        "available_sources": get_available_sources(session),
        "filters_active": filters_are_active(filters),
        **metrics,
    }


# --- Dashboard analytics (activity timeline + distributions) ---

CATEGORY_COLORS: dict[str, str] = {
    "python": "#3b6fd9",
    "ml": "#9b7ede",
    "git": "#6bcb9a",
    "general": "#64748b",
    "devops": "#f5a962",
    "web": "#5ec9e8",
    "data": "#f07167",
}


def _category_color(category: str) -> str:
    key = (category or "general").lower().strip()
    return CATEGORY_COLORS.get(key, "#94a3b8")


def _resolve_activity_window(
    session: Session,
    filters: DashboardFilters,
) -> tuple[datetime, datetime, int]:
    """Calendar-day range for the activity chart, aligned with dashboard period filters."""
    now = datetime.now(timezone.utc)
    window_end = filters.until if filters.until else now
    if window_end.tzinfo is None:
        window_end = window_end.replace(tzinfo=timezone.utc)

    if filters.since:
        window_start = filters.since
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
    else:
        stmt = select(func.min(ConversationTurn.timestamp))
        if filters.source:
            stmt = stmt.where(ConversationTurn.source == filters.source)
        earliest = session.exec(stmt).one()
        if earliest:
            window_start = earliest
            if window_start.tzinfo is None:
                window_start = window_start.replace(tzinfo=timezone.utc)
        else:
            window_start = now - timedelta(days=29)

    window_start = window_start.replace(hour=0, minute=0, second=0, microsecond=0)
    day_count = (window_end.date() - window_start.date()).days + 1
    day_count = max(1, day_count)

    # All-time ranges can span years — cap chart length for readability
    max_days = 366
    if day_count > max_days:
        window_start = (window_end - timedelta(days=max_days - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_count = max_days

    return window_start, window_end, day_count


def get_dashboard_analytics(
    session: Session,
    filters: DashboardFilters,
) -> dict:
    """Daily activity + topic/category distributions for the agent usage dashboard."""
    window_start, window_end, days = _resolve_activity_window(session, filters)
    turn_clauses = _turn_filter_clauses(filters)

    day_expr = func.strftime("%Y-%m-%d", ConversationTurn.timestamp).label("day")
    activity_stmt = (
        select(day_expr, func.count(col(ConversationTurn.id)).label("count"))
        .where(ConversationTurn.timestamp >= window_start)
        .where(ConversationTurn.timestamp <= window_end)
    )
    for clause in turn_clauses:
        activity_stmt = activity_stmt.where(clause)
    activity_stmt = activity_stmt.group_by(day_expr).order_by(day_expr)
    activity_rows = session.exec(activity_stmt).all()
    counts_by_day = {str(day): int(count) for day, count in activity_rows if day}

    activity: list[dict] = []
    for i in range(days):
        day = (window_start + timedelta(days=i)).strftime("%Y-%m-%d")
        activity.append({"date": day, "count": counts_by_day.get(day, 0)})

    concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=50)
    topics = [
        {
            "name": c["name"],
            "count": c["ask_count"],
            "category": c["category"] or "general",
        }
        for c in concepts[:12]
    ]

    category_totals: dict[str, int] = {}
    for c in concepts:
        cat = (c["category"] or "general").lower()
        category_totals[cat] = category_totals.get(cat, 0) + c["ask_count"]
    categories = [
        {
            "name": name,
            "count": count,
            "color": _category_color(name),
        }
        for name, count in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "days": days,
        "activity": activity,
        "topics": topics,
        "categories": categories,
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

    metrics = get_dashboard_metrics(session, DashboardFilters())

    return {
        "total_turns": total_turns,
        "total_concepts": total_concepts,
        "total_flashcards": total_flashcards,
        "weekly_turns": weekly_turns,
        "period_turns": weekly_turns,
        "sources": {src: cnt for src, cnt in sources},
        "available_sources": get_available_sources(session),
        "filters_active": False,
        **metrics,
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


def clear_memory(session: Session) -> dict[str, int]:
    """Remove all imported conversations, concepts, and derived study content."""
    counts: dict[str, int] = {}
    for model, key in [
        (ConceptMention, "mentions"),
        (Flashcard, "flashcards"),
        (GeneratedContent, "generated"),
        (ConversationTurn, "turns"),
        (Concept, "concepts"),
    ]:
        result = session.exec(delete(model))
        counts[key] = result.rowcount  # type: ignore[attr-defined]
    session.commit()
    return counts
