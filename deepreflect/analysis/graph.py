"""Build a knowledge graph from stored concepts and co-occurrence data."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
from sqlmodel import Session, text

from deepreflect.memory.db import get_concepts
from deepreflect.memory.models import Concept


def build_graph(session: Session) -> nx.Graph:
    """Construct a NetworkX graph from concepts + co-occurrences."""
    G = nx.Graph()

    concepts = get_concepts(session, min_ask_count=1)
    for c in concepts:
        G.add_node(
            c.id,
            name=c.name,
            category=c.category or "general",
            ask_count=c.ask_count,
            weak_score=round(c.weak_score, 3),
            last_seen=c.last_seen.isoformat() if c.last_seen else None,
            first_seen=c.first_seen.isoformat() if c.first_seen else None,
        )

    # Co-occurrence edges from concept_mentions sharing the same turn
    rows = session.exec(
        text(
            """
            SELECT a.concept_id, b.concept_id, COUNT(*) as co_count
            FROM conceptmention a
            JOIN conceptmention b ON a.turn_id = b.turn_id AND a.concept_id < b.concept_id
            GROUP BY a.concept_id, b.concept_id
            HAVING co_count >= 1
            ORDER BY co_count DESC
            LIMIT 500
            """
        )
    ).fetchall()

    for row in rows:
        a_id, b_id, weight = row[0], row[1], row[2]
        if G.has_node(a_id) and G.has_node(b_id):
            G.add_edge(a_id, b_id, weight=int(weight))

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
            }
        )

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append(
            {
                "source": str(u),
                "target": str(v),
                "weight": data.get("weight", 1),
            }
        )

    return {"nodes": nodes, "edges": edges}
