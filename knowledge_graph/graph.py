"""KnowledgeGraph: entity, relationship, evidence, permission, and audit layers."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

from .audit import AuditEvent, AuditLog
from .models import EntityType, KnowledgeNode, Triple

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """In-memory knowledge graph with typed relationships and provenance.

    Layers:
        Entity:       Nodes keyed by id.
        Relationship: Typed directed triples (subject, predicate, object).
        Evidence:     Provenance attached to each triple.
        Permission:   Access masks on each node.
        Audit:        Append-only record of all mutations.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._triples: dict[str, Triple] = {}
        self._outgoing: dict[str, list[str]] = defaultdict(list)
        self._incoming: dict[str, list[str]] = defaultdict(list)
        self.audit = AuditLog()

    # ── Entity layer ──────────────────────────────────────────────────────────

    def add_node(self, node: KnowledgeNode) -> None:
        if node.id in self._nodes:
            logger.debug("Node '%s' already exists; skipping.", node.id)
            return
        self._nodes[node.id] = node
        self.audit.record(
            AuditEvent(
                "add_node",
                node.id,
                {"label": node.label, "type": node.entity_type.value},
            )
        )

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[KnowledgeNode]:
        return list(self._nodes.values())

    def nodes_by_type(self, entity_type: EntityType) -> list[KnowledgeNode]:
        return [n for n in self._nodes.values() if n.entity_type == entity_type]

    # ── Relationship layer ────────────────────────────────────────────────────

    def add_triple(self, triple: Triple) -> None:
        if triple.subject_id not in self._nodes:
            raise ValueError(
                f"Subject node '{triple.subject_id}' not found; add it first."
            )
        if triple.object_id not in self._nodes:
            raise ValueError(
                f"Object node '{triple.object_id}' not found; add it first."
            )
        if triple.id in self._triples:
            logger.debug("Triple '%s' already exists; skipping.", triple.id)
            return
        self._triples[triple.id] = triple
        self._outgoing[triple.subject_id].append(triple.id)
        self._incoming[triple.object_id].append(triple.id)
        self.audit.record(AuditEvent("add_triple", triple.id, triple.to_dict()))

    def get_triple(self, triple_id: str) -> Optional[Triple]:
        return self._triples.get(triple_id)

    def triples_from(self, subject_id: str) -> list[Triple]:
        return [self._triples[tid] for tid in self._outgoing.get(subject_id, [])]

    def triples_to(self, object_id: str) -> list[Triple]:
        return [self._triples[tid] for tid in self._incoming.get(object_id, [])]

    def all_triples(self) -> list[Triple]:
        return list(self._triples.values())

    def triples_by_predicate(self, predicate: str) -> list[Triple]:
        return [t for t in self._triples.values() if t.predicate == predicate]

    # ── Retrieval layer ───────────────────────────────────────────────────────

    def k_hop_neighbors(self, node_id: str, k: int = 1) -> set[str]:
        """Return all node ids reachable within k directed hops from node_id."""
        visited: set[str] = {node_id}
        frontier: set[str] = {node_id}
        for _ in range(k):
            next_frontier: set[str] = set()
            for nid in frontier:
                for triple in self.triples_from(nid):
                    if triple.object_id not in visited:
                        next_frontier.add(triple.object_id)
            visited |= next_frontier
            frontier = next_frontier
            if not frontier:
                break
        visited.discard(node_id)
        return visited

    def path_between(
        self, source_id: str, target_id: str, max_hops: int = 5
    ) -> list[str] | None:
        """BFS shortest directed path from source to target.

        Returns the list of node ids (inclusive) or None if unreachable.
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        if source_id == target_id:
            return [source_id]
        queue: list[list[str]] = [[source_id]]
        visited: set[str] = {source_id}
        while queue:
            path = queue.pop(0)
            if len(path) > max_hops:
                break
            current = path[-1]
            for triple in self.triples_from(current):
                nxt = triple.object_id
                if nxt == target_id:
                    return path + [nxt]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(path + [nxt])
        return None

    # ── Stats / export ────────────────────────────────────────────────────────

    def stats(self) -> dict:
        by_type: dict[str, int] = defaultdict(int)
        for node in self._nodes.values():
            by_type[node.entity_type.value] += 1
        predicates: dict[str, int] = defaultdict(int)
        for triple in self._triples.values():
            predicates[triple.predicate] += 1
        return {
            "node_count": len(self._nodes),
            "triple_count": len(self._triples),
            "entities_by_type": dict(by_type),
            "predicates": dict(predicates),
        }

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "triples": [t.to_dict() for t in self._triples.values()],
            "stats": self.stats(),
        }
