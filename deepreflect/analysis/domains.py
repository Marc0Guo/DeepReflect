"""Domain hub topics for the knowledge graph (Web, Data, ML, …)."""
from __future__ import annotations

from sqlmodel import Session, select

from deepreflect.memory.db import get_or_create_concept, record_mention
from deepreflect.memory.models import Concept, ConceptMention, ConversationTurn

# Canonical graph categories → display hub label.
DOMAIN_HUBS: dict[str, str] = {
    "web": "Web",
    "data": "Data",
    "ml": "ML & AI",
    "programming": "Programming",
    "infra": "Infra & DevOps",
    "mobile": "Mobile",
    "math": "Math",
    "general": "General",
    "other": "Other",
}

HUB_LABELS: frozenset[str] = frozenset(DOMAIN_HUBS.values())

# Map LLM tagger categories to graph domains.
TAGGER_TO_DOMAIN: dict[str, str] = {
    "web": "web",
    "data": "data",
    "ml_ai": "ml",
    "ml": "ml",
    "programming": "programming",
    "infra": "infra",
    "mobile": "mobile",
    "math": "math",
    "research": "general",
    "general": "general",
    "other": "other",
    "python": "programming",
    "git": "programming",
}


def normalize_graph_category(raw: str) -> str:
    cat = str(raw or "general").lower().strip()
    return TAGGER_TO_DOMAIN.get(cat, "general")


def is_domain_hub(name: str) -> bool:
    return name in HUB_LABELS


def ensure_domain_hubs(session: Session) -> dict[str, Concept]:
    """Create missing domain hub concepts (Web, Data, …)."""
    hubs: dict[str, Concept] = {}
    for domain, label in DOMAIN_HUBS.items():
        hubs[domain] = get_or_create_concept(session, label, domain)
    return hubs


def get_or_create_domain_hub(session: Session, category: str) -> Concept:
    domain = normalize_graph_category(category)
    label = DOMAIN_HUBS.get(domain, DOMAIN_HUBS["general"])
    return get_or_create_concept(session, label, domain)


def backfill_domain_mentions(session: Session) -> int:
    """Link existing topic mentions to domain hubs (fixes graphs analyzed without hubs)."""
    hubs = ensure_domain_hubs(session)
    hub_ids = {h.id for h in hubs.values()}

    rows = session.exec(
        select(ConceptMention.turn_id, Concept.category)
        .join(Concept, Concept.id == ConceptMention.concept_id)
        .where(ConceptMention.concept_id.not_in(hub_ids))  # type: ignore[attr-defined]
    ).all()

    added = 0
    seen: set[tuple[int, str]] = set()
    for turn_id, category in rows:
        domain = normalize_graph_category(category or "general")
        key = (turn_id, domain)
        if key in seen:
            continue
        seen.add(key)

        hub = hubs[domain]
        exists = session.exec(
            select(ConceptMention).where(
                ConceptMention.turn_id == turn_id,
                ConceptMention.concept_id == hub.id,
            )
        ).first()
        if exists:
            continue

        turn = session.get(ConversationTurn, turn_id)
        if turn is None:
            continue
        record_mention(session, turn, hub)
        added += 1

    return added


def record_turn_tags(
    session: Session,
    turn: ConversationTurn,
    concepts: list[str],
    category: str,
) -> None:
    """Attach specific topics + their domain hub to one turn."""
    domain = normalize_graph_category(category)
    seen: set[str] = set()
    for name in concepts:
        if not name or name in seen or is_domain_hub(name):
            continue
        seen.add(name)
        concept = get_or_create_concept(session, name, domain)
        record_mention(session, turn, concept)
    hub = get_or_create_domain_hub(session, domain)
    record_mention(session, turn, hub)
