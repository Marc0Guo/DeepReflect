"""Generate shareable HTML learning summary pages — Vibe Roast visual style."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlmodel import Session

from deepreflect.memory.db import (
    DashboardFilters,
    get_filtered_concepts,
    get_filtered_stats,
    get_turns,
)

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TOP_TOPICS = 5

_CAT_COLORS = {
    "python": "#60a5fa",
    "ml": "#a78bfa",
    "git": "#fb923c",
    "web": "#34d399",
    "data": "#22d3ee",
    "math": "#fbbf24",
    "general": "#6b6280",
    "other": "#94a3b8",
}

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    auto_reload=True,
)


@dataclass(frozen=True)
class _PeriodLayout:
    since: datetime
    until: datetime
    label: str
    date_range: str
    hero_title: str
    hero_sub: str
    show_heatmap: bool
    heatmap_mode: str  # "days" | "months"
    heatmap_days: int
    heatmap_title: str
    bubbles: tuple[tuple[str, str], ...]  # (stat key, label)


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _period_layout(period: str) -> _PeriodLayout:
    now = _naive_utc(datetime.now(timezone.utc))
    if period == "daily":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return _PeriodLayout(
            since=since,
            until=now,
            label="Daily",
            date_range=now.strftime("%B %d, %Y"),
            hero_title="Today's AI Conversations",
            hero_sub="everything you explored with AI today",
            show_heatmap=False,
            heatmap_mode="days",
            heatmap_days=0,
            heatmap_title="",
            bubbles=(
                ("period_turns", "Today"),
                ("total_concepts", "Topics touched"),
                ("total_flashcards", "Flashcards"),
                ("tool_count", "Tools used"),
            ),
        )
    if period == "monthly":
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return _PeriodLayout(
            since=since,
            until=now,
            label="Monthly",
            date_range=now.strftime("%B %Y"),
            hero_title="This Month's AI Conversations",
            hero_sub="your learning activity this calendar month",
            show_heatmap=True,
            heatmap_mode="days",
            heatmap_days=(now.date() - since.date()).days + 1,
            heatmap_title="Activity — this month (by day)",
            bubbles=(
                ("period_turns", "This month"),
                ("total_concepts", "Topics"),
                ("active_days", "Active days"),
                ("category_count", "Categories"),
            ),
        )
    if period == "yearly":
        since = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return _PeriodLayout(
            since=since,
            until=now,
            label="Yearly",
            date_range=now.strftime("%Y"),
            hero_title="This Year's AI Conversations",
            hero_sub="your year in AI-assisted learning",
            show_heatmap=True,
            heatmap_mode="months",
            heatmap_days=12,
            heatmap_title="Activity — by month",
            bubbles=(
                ("period_turns", "This year"),
                ("total_concepts", "Topics"),
                ("longest_streak_days", "Best streak"),
                ("category_count", "Categories"),
            ),
        )
    # weekly (default)
    since = now - timedelta(days=7)
    return _PeriodLayout(
        since=since,
        until=now,
        label="Weekly",
        date_range=f"{since.strftime('%b %d')} – {now.strftime('%b %d, %Y')}",
        hero_title="This Week's AI Conversations",
        hero_sub="your last 7 days of AI-assisted learning",
        show_heatmap=True,
        heatmap_mode="days",
        heatmap_days=7,
        heatmap_title="Activity — last 7 days",
        bubbles=(
            ("period_turns", "This week"),
            ("total_concepts", "Topics"),
            ("active_days", "Active days"),
            ("tool_count", "Tools used"),
        ),
    )


def _heat_level(c: int) -> str:
    if c == 0:
        return ""
    if c == 1:
        return "l1"
    if c <= 3:
        return "l2"
    if c <= 6:
        return "l3"
    return "l4"


def _build_day_heatmap(turns: list, since: datetime, until: datetime, days: int) -> list[str]:
    since = _naive_utc(since)
    until = _naive_utc(until)
    counts: dict[str, int] = {}
    for t in turns:
        ts = _naive_utc(t.timestamp)
        if since <= ts <= until:
            key = ts.strftime("%Y-%m-%d")
            counts[key] = counts.get(key, 0) + 1

    cells = []
    end = until.date()
    for i in range(days - 1, -1, -1):
        day = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        cells.append(_heat_level(counts.get(day, 0)))
    return cells


def _build_month_heatmap(turns: list, since: datetime, until: datetime) -> list[str]:
    since = _naive_utc(since)
    until = _naive_utc(until)
    year = until.year
    counts = {m: 0 for m in range(1, 13)}
    for t in turns:
        ts = _naive_utc(t.timestamp)
        if since <= ts <= until and ts.year == year:
            counts[ts.month] += 1
    return [_heat_level(counts[m]) for m in range(1, 13)]


def _active_days(turns: list, since: datetime, until: datetime) -> int:
    since = _naive_utc(since)
    until = _naive_utc(until)
    days: set = set()
    for t in turns:
        ts = _naive_utc(t.timestamp)
        if since <= ts <= until:
            days.add(ts.date())
    return len(days)


def _build_category_counts(concepts: list) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for c in concepts:
        cat = (getattr(c, "category", None) or c.get("category") if isinstance(c, dict) else None) or "general"
        cnt = getattr(c, "ask_count", None) if not isinstance(c, dict) else c.get("ask_count", 0)
        counts[cat] = counts.get(cat, 0) + int(cnt or 0)
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def _bubble_value(key: str, stats: dict, extras: dict) -> int | str:
    if key == "tool_count":
        return extras.get("tool_count", 0)
    if key == "active_days":
        return extras.get("active_days", 0)
    val = stats.get(key)
    if val is None:
        return "—"
    return val


def generate_summary_html(
    session: Session,
    period: str = "weekly",
    out_dir: Path | None = None,
) -> Path:
    if period not in ("daily", "weekly", "monthly", "yearly"):
        period = "weekly"

    layout = _period_layout(period)
    filters = DashboardFilters(since=layout.since, until=layout.until)
    stats = get_filtered_stats(session, filters)

    period_rows = get_filtered_concepts(
        session, filters, min_ask_count=1, limit=_TOP_TOPICS
    )
    concepts = [
        SimpleNamespace(
            name=r["name"],
            category=r.get("category") or "general",
            ask_count=r["ask_count"],
            weak_score=r.get("weak_score", 0.0),
        )
        for r in period_rows
    ]

    all_period_concepts = get_filtered_concepts(
        session, filters, min_ask_count=1, limit=200
    )
    category_counts = _build_category_counts(all_period_concepts)

    period_turns = get_turns(
        session, since=layout.since, until=layout.until, limit=10_000
    )
    sources = stats.get("sources", {})
    extras = {
        "tool_count": len(sources),
        "active_days": _active_days(period_turns, layout.since, layout.until),
    }
    stats["period_turns"] = stats.get("total_turns", 0)

    heatmap_cells: list[str] = []
    heatmap_month_labels: list[str] = []
    if layout.show_heatmap:
        if layout.heatmap_mode == "months":
            heatmap_cells = _build_month_heatmap(
                period_turns, layout.since, layout.until
            )
            heatmap_month_labels = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ]
        else:
            heatmap_cells = _build_day_heatmap(
                period_turns, layout.since, layout.until, layout.heatmap_days
            )

    bubble_stats = [
        {"n": _bubble_value(key, stats, extras), "k": label}
        for key, label in layout.bubbles
    ]

    template = _env.get_template("learning_summary.html")
    html = template.render(
        period=period,
        period_label=layout.label,
        date_range=layout.date_range,
        hero_title=layout.hero_title,
        hero_sub=layout.hero_sub,
        period_turns=stats.get("total_turns", 0),
        stats=stats,
        bubble_stats=bubble_stats,
        concepts=concepts,
        sources=sources,
        show_heatmap=layout.show_heatmap,
        heatmap_mode=layout.heatmap_mode,
        heatmap_title=layout.heatmap_title,
        heatmap_cells=heatmap_cells,
        heatmap_month_labels=heatmap_month_labels,
        category_counts=category_counts,
        cat_colors=_CAT_COLORS,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if out_dir is None:
        out_dir = Path.home() / ".deepreflect" / "data" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"summary_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
