"""Dashboard behavior insights: calendar, heatmaps, word cloud."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, col, func, select

from deepreflect.memory.db import (
    DashboardFilters,
    ConceptMention,
    ConversationTurn,
    _turn_filter_clauses,
    get_filtered_concepts,
)

_STOPWORDS = frozenset(
    """
    a an the and or but if then else when while for to from with without about into
    through during before after above below between under again further once here there
    all each few more most other some such no nor not only own same so than too very
    can will just don should now could would may might must shall it its this that
    these those am is are was were be been being have has had do does did doing get got
    make made use using used also like want need help please how what which who why
    where me my we you your i he she they them their our of in on at by as up out
    im ive id ok yes yeah nope etc vs via per let lets dont cant wont isnt arent
    wasnt werent havent hasnt hadnt doesnt didnt wont wouldnt couldnt shouldnt
    """.split()
)

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")
_WORD_CLOUD_LIMIT = 25


def _tokenize_prompt(text: str) -> list[str]:
    words = _TOKEN_RE.findall(text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) <= 32]


def _filtered_turn_ids(session: Session, filters: DashboardFilters) -> Optional[list[int]]:
    if not filters.concept and not filters.status:
        return None
    stmt = select(ConversationTurn.id).distinct()
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)
    concepts = get_filtered_concepts(session, filters, min_ask_count=1, limit=10_000)
    if not concepts:
        return []
    concept_ids = [c["id"] for c in concepts]
    stmt = stmt.join(
        ConceptMention, ConceptMention.turn_id == ConversationTurn.id
    ).where(col(ConceptMention.concept_id).in_(concept_ids))
    return list(session.exec(stmt).all())


def _apply_turn_filters(
    stmt,
    session: Session,
    filters: DashboardFilters,
    turn_ids: Optional[list[int]],
):
    for clause in _turn_filter_clauses(filters):
        stmt = stmt.where(clause)
    if turn_ids is not None:
        stmt = stmt.where(col(ConversationTurn.id).in_(turn_ids))
    return stmt


def _apply_source_filter(stmt, source: Optional[str]):
    if source:
        stmt = stmt.where(ConversationTurn.source == source)
    return stmt


def get_calendar_years(session: Session) -> list[int]:
    min_ts = session.exec(select(func.min(ConversationTurn.timestamp))).one()
    max_ts = session.exec(select(func.max(ConversationTurn.timestamp))).one()
    if not min_ts or not max_ts:
        return [datetime.now(timezone.utc).year]
    return list(range(min_ts.year, max_ts.year + 1))


def get_calendar_for_year(
    session: Session,
    year: int,
    source: Optional[str] = None,
) -> tuple[list[dict], int]:
    year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    day_expr = func.strftime("%Y-%m-%d", ConversationTurn.timestamp).label("day")
    cal_stmt = (
        select(day_expr, ConversationTurn.source, func.count(col(ConversationTurn.id)).label("count"))
        .where(ConversationTurn.timestamp >= year_start)
        .where(ConversationTurn.timestamp <= year_end)
    )
    cal_stmt = _apply_source_filter(cal_stmt, source)
    cal_stmt = cal_stmt.group_by(day_expr, ConversationTurn.source)

    by_day: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "cursor": 0, "claude-code": 0}
    )
    max_cal = 0
    for day, src, count in session.exec(cal_stmt).all():
        if not day:
            continue
        c = int(count)
        by_day[str(day)]["count"] += c
        if src in ("cursor", "claude-code"):
            by_day[str(day)][src] = c
        max_cal = max(max_cal, by_day[str(day)]["count"])

    calendar: list[dict] = []
    d = date(year, 1, 1)
    end_d = date(year, 12, 31)
    while d <= end_d:
        key = d.isoformat()
        row = by_day.get(key, {"count": 0, "cursor": 0, "claude-code": 0})
        calendar.append(
            {
                "date": key,
                "count": row["count"],
                "cursor": row.get("cursor", 0),
                "claude": row.get("claude-code", 0),
            }
        )
        d += timedelta(days=1)
    return calendar, max_cal


def get_global_time_heatmap(session: Session) -> tuple[list[dict], int]:
    dow_expr = func.strftime("%w", ConversationTurn.timestamp).label("dow")
    hour_expr = func.strftime("%H", ConversationTurn.timestamp).label("hour")
    heat_stmt = select(
        dow_expr,
        hour_expr,
        func.count(col(ConversationTurn.id)).label("count"),
    ).group_by(dow_expr, hour_expr)

    heat_cells: dict[tuple[int, int], dict] = {}
    max_heat = 0
    for dow_s, hour_s, count in session.exec(heat_stmt).all():
        dow_i, hour_i = int(dow_s), int(hour_s)
        c = int(count)
        heat_cells[(dow_i, hour_i)] = {"dow": dow_i, "hour": hour_i, "count": c, "cursor": 0, "claude": 0}
        max_heat = max(max_heat, c)

    cells = [
        heat_cells.get((d, h), {"dow": d, "hour": h, "count": 0, "cursor": 0, "claude": 0})
        for d in range(7)
        for h in range(24)
    ]
    return cells, max_heat


def get_word_cloud(
    session: Session,
    filters: DashboardFilters,
    limit: int = _WORD_CLOUD_LIMIT,
) -> list[dict]:
    turn_ids = _filtered_turn_ids(session, filters)
    if turn_ids is not None and not turn_ids:
        return []

    prompt_stmt = select(ConversationTurn.user_prompt)
    prompt_stmt = _apply_turn_filters(prompt_stmt, session, filters, turn_ids)
    counter: Counter[str] = Counter()
    for row in session.exec(prompt_stmt).all():
        prompt = row[0] if isinstance(row, tuple) else row
        if prompt:
            counter.update(_tokenize_prompt(str(prompt)))

    if not counter:
        return []

    max_w = max(counter.values())
    return [
        {"text": word, "count": count, "weight": round(count / max_w, 3)}
        for word, count in counter.most_common(limit)
    ]


def get_dashboard_insights(
    session: Session,
    filters: DashboardFilters,
    year: Optional[int] = None,
) -> dict:
    years = get_calendar_years(session)
    pick_year = year if year is not None else (years[-1] if years else datetime.now(timezone.utc).year)
    if pick_year not in years and years:
        pick_year = years[-1]

    calendar, calendar_max = get_calendar_for_year(
        session, pick_year, source=filters.source
    )
    time_heatmap, time_heatmap_max = get_global_time_heatmap(session)
    word_cloud = get_word_cloud(session, filters, limit=_WORD_CLOUD_LIMIT)

    return {
        "calendar_years": years,
        "calendar_year": pick_year,
        "calendar": calendar,
        "calendar_max": calendar_max,
        "time_heatmap": time_heatmap,
        "time_heatmap_max": time_heatmap_max,
        "word_cloud": word_cloud,
    }


def get_session_turns(
    session: Session,
    session_id: str,
    source: str,
    limit: int = 40,
) -> list[dict]:
    stmt = (
        select(ConversationTurn)
        .where(ConversationTurn.session_id == session_id)
        .where(ConversationTurn.source == source)
        .order_by(ConversationTurn.timestamp.desc())
        .limit(limit)
    )
    turns = list(session.exec(stmt).all())
    return [
        {
            "id": t.id,
            "timestamp": t.timestamp.isoformat(),
            "user_prompt": t.user_prompt[:800],
            "ai_response": t.ai_response[:800],
            "source": t.source,
        }
        for t in turns
    ]
