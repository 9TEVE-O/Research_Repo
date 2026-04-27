"""Subgraph detection, connected-component analysis, and pattern mining.

Implements the compounding-knowledge insight: over time, repeated
relationships between entity types reveal structural patterns, and
weakly-connected components reveal natural knowledge clusters.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .graph import KnowledgeGraph
from .models import KnowledgeNode, Triple


@dataclass
class Cluster:
    """A weakly connected subgraph — a natural knowledge cluster."""

    nodes: list[KnowledgeNode]
    internal_triples: list[Triple]

    @property
    def size(self) -> int:
        return len(self.nodes)

    def dominant_type(self) -> str | None:
        """Most common entity type in this cluster."""
        counts: dict[str, int] = defaultdict(int)
        for node in self.nodes:
            counts[node.entity_type.value] += 1
        return max(counts, key=counts.__getitem__) if counts else None

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "dominant_type": self.dominant_type(),
            "node_ids": [n.id for n in self.nodes],
            "internal_triple_count": len(self.internal_triples),
        }


@dataclass
class RelationshipPattern:
    """A recurring (predicate, subject_type, object_type) pattern."""

    predicate: str
    subject_type: str
    object_type: str
    count: int

    def to_dict(self) -> dict:
        return {
            "predicate": self.predicate,
            "subject_type": self.subject_type,
            "object_type": self.object_type,
            "count": self.count,
        }


def find_connected_components(graph: KnowledgeGraph) -> list[Cluster]:
    """Find weakly connected components via undirected BFS.

    Returns clusters sorted by size descending.
    """
    node_ids = {n.id for n in graph.all_nodes()}
    visited: set[str] = set()
    all_triples = graph.all_triples()
    components: list[list[str]] = []

    def bfs(start: str) -> list[str]:
        component: list[str] = []
        queue = [start]
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            component.append(nid)
            for t in graph.triples_from(nid):
                if t.object_id not in visited:
                    queue.append(t.object_id)
            for t in graph.triples_to(nid):
                if t.subject_id not in visited:
                    queue.append(t.subject_id)
        return component

    for nid in node_ids:
        if nid not in visited:
            component = bfs(nid)
            if component:
                components.append(component)

    clusters: list[Cluster] = []
    for component in components:
        component_set = set(component)
        nodes = [graph.get_node(nid) for nid in component if graph.get_node(nid)]
        internal = [
            t
            for t in all_triples
            if t.subject_id in component_set and t.object_id in component_set
        ]
        clusters.append(Cluster(nodes=nodes, internal_triples=internal))

    return sorted(clusters, key=lambda c: c.size, reverse=True)


def detect_patterns(graph: KnowledgeGraph) -> list[RelationshipPattern]:
    """Mine recurring (predicate, subject_type, object_type) patterns.

    Returns patterns sorted by frequency descending.  A high-count pattern
    means many entities share the same structural relationship, which is a
    signal worth surfacing for AI context.
    """
    pattern_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for triple in graph.all_triples():
        subj = graph.get_node(triple.subject_id)
        obj = graph.get_node(triple.object_id)
        if subj and obj:
            key = (
                triple.predicate,
                subj.entity_type.value,
                obj.entity_type.value,
            )
            pattern_counts[key] += 1

    patterns = [
        RelationshipPattern(
            predicate=pred,
            subject_type=stype,
            object_type=otype,
            count=count,
        )
        for (pred, stype, otype), count in pattern_counts.items()
    ]
    return sorted(patterns, key=lambda p: p.count, reverse=True)


def build_subgraph(
    graph: KnowledgeGraph, seed_ids: list[str], k: int = 1
) -> KnowledgeGraph:
    """Extract a new KnowledgeGraph from seed nodes and their k-hop neighborhood.

    Useful for narrowing a large graph to the context relevant for a
    specific query or AI task.
    """
    included: set[str] = set(seed_ids)
    for seed_id in seed_ids:
        included |= graph.k_hop_neighbors(seed_id, k=k)

    sub = KnowledgeGraph()
    for nid in included:
        node = graph.get_node(nid)
        if node:
            sub.add_node(node)
    for triple in graph.all_triples():
        if triple.subject_id in included and triple.object_id in included:
            sub.add_triple(triple)
    return sub
