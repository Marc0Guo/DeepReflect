"""Build a knowledge graph from stored concepts and co-occurrence data."""
from __future__ import annotations

from typing import Any

import networkx as nx
from sqlmodel import Session, text

from deepreflect.analysis.domains import (
    get_or_create_domain_hub,
    is_domain_hub,
    normalize_graph_category,
)
from deepreflect.memory.db import get_concepts


def build_graph(session: Session) -> nx.Graph:
    """Hub-and-spoke graph: only domains that have ≥1 topic are shown."""
    G = nx.Graph()

    concepts = get_concepts(session, min_ask_count=1)
    topics = [c for c in concepts if not is_domain_hub(c.name)]
    active_domains = {
        normalize_graph_category(c.category or "general") for c in topics
    }

    hubs_by_domain = {
        domain: get_or_create_domain_hub(session, domain) for domain in active_domains
    }

    for hub in hubs_by_domain.values():
        G.add_node(
            hub.id,
            name=hub.name,
            category=hub.category or "general",
            ask_count=hub.ask_count,
            weak_score=round(hub.weak_score, 3),
            last_seen=hub.last_seen.isoformat() if hub.last_seen else None,
            first_seen=hub.first_seen.isoformat() if hub.first_seen else None,
            node_type="domain",
        )

    topic_domain: dict[int, str] = {}
    for c in topics:
        topic_domain[c.id] = normalize_graph_category(c.category or "general")
        G.add_node(
            c.id,
            name=c.name,
            category=c.category or "general",
            ask_count=c.ask_count,
            weak_score=round(c.weak_score, 3),
            last_seen=c.last_seen.isoformat() if c.last_seen else None,
            first_seen=c.first_seen.isoformat() if c.first_seen else None,
            node_type="topic",
        )
        domain = topic_domain[c.id]
        hub = hubs_by_domain.get(domain)
        if hub is not None:
            G.add_edge(
                c.id,
                hub.id,
                weight=max(1, c.ask_count),
                edge_type="hub",
            )

    rows = session.exec(
        text(
            """
            SELECT a.concept_id, b.concept_id, COUNT(*) as co_count
            FROM conceptmention a
            JOIN conceptmention b ON a.turn_id = b.turn_id AND a.concept_id < b.concept_id
            GROUP BY a.concept_id, b.concept_id
            HAVING co_count >= 1
            ORDER BY co_count DESC
            LIMIT 400
            """
        )
    ).fetchall()

    for row in rows:
        a_id, b_id, weight = row[0], row[1], row[2]
        dom_a = topic_domain.get(a_id)
        dom_b = topic_domain.get(b_id)
        if dom_a is None or dom_b is None:
            continue
        if not (G.has_node(a_id) and G.has_node(b_id)):
            continue
        if G.has_edge(a_id, b_id):
            continue
        cross = dom_a != dom_b
        if not cross and int(weight) < 2:
            continue
        G.add_edge(
            a_id,
            b_id,
            weight=int(weight),
            edge_type="cross" if cross else "peer",
        )

    return G


def graph_to_json(G: nx.Graph) -> dict[str, Any]:
    """Serialize graph to {nodes, edges} for the React Flow frontend."""
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append(
            {
                "id": str(node_id),
                "label": data.get("name", str(node_id)),
                "category": data.get("category", "general"),
                "ask_count": data.get("ask_count", 0),
                "weak_score": data.get("weak_score", 0.0),
                "last_seen": data.get("last_seen"),
                "first_seen": data.get("first_seen"),
                "node_type": data.get("node_type", "topic"),
            }
        )

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append(
            {
                "source": str(u),
                "target": str(v),
                "weight": data.get("weight", 1),
                "edge_type": data.get("edge_type", "peer"),
            }
        )

    return {"nodes": nodes, "edges": edges}
