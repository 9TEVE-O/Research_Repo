"""Graph-based retrieval interface for knowledge queries."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .graph import KnowledgeGraph
from .models import EntityType, KnowledgeNode, Triple

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """A matched node with its supporting triples and neighbor context."""

    node: KnowledgeNode
    matching_triples: list[Triple]
    neighbor_ids: set[str] = field(default_factory=set)
    hop_distance: int = 0


class GraphRetriever:
    """Query interface over a KnowledgeGraph.

    Supports:
        - Entity lookup by type
        - Predicate-filtered triple search
        - k-hop context expansion for graph-based RAG
        - Path-based reasoning queries
        - Bounded AI context blocks
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def find_by_type(self, entity_type: EntityType) -> list[KnowledgeNode]:
        return self._graph.nodes_by_type(entity_type)

    def find_by_predicate(self, predicate: str) -> list[Triple]:
        return self._graph.triples_by_predicate(predicate)

    def context_for(self, node_id: str, k: int = 2) -> QueryResult | None:
        """Retrieve a node and its k-hop neighborhood for RAG context."""
        node = self._graph.get_node(node_id)
        if node is None:
            logger.warning("Node '%s' not found in graph.", node_id)
            return None
        outgoing = self._graph.triples_from(node_id)
        incoming = self._graph.triples_to(node_id)
        neighbors = self._graph.k_hop_neighbors(node_id, k=k)
        return QueryResult(
            node=node,
            matching_triples=outgoing + incoming,
            neighbor_ids=neighbors,
            hop_distance=k,
        )

    def build_ai_context(self, node_id: str, k: int = 2) -> str:
        """Build a bounded plain-text context block for AI queries.

        Constructs a structured string describing the node, its typed
        relationships, and its k-hop neighborhood.  Suitable for injection
        into an LLM prompt as grounded, curated context.

        Example output::

            Entity: LAB Safe Intake [workflow]
            Summary: Privacy-first document intake workflow.
            Properties:
              status: active
            Relationships:
              LAB Safe Intake -> redacts -> PII (confidence=0.95)
              LAB Safe Intake -> requires -> Human Review (confidence=1.00)
            Nearby entities:
              - PII [risk]
              - Human Review [workflow]
        """
        result = self.context_for(node_id, k=k)
        if result is None:
            return f"No knowledge available about '{node_id}'."

        node = result.node
        lines: list[str] = [
            f"Entity: {node.label} [{node.entity_type.value}]",
            f"Summary: {node.summary or '(no summary)'}",
        ]

        if node.properties:
            lines.append("Properties:")
            for prop_key, prop_val in node.properties.items():
                lines.append(f"  {prop_key}: {prop_val}")

        if result.matching_triples:
            lines.append("Relationships:")
            for triple in result.matching_triples:
                subj = self._graph.get_node(triple.subject_id)
                obj = self._graph.get_node(triple.object_id)
                subj_label = subj.label if subj else triple.subject_id
                obj_label = obj.label if obj else triple.object_id
                conf_str = ""
                if triple.evidence:
                    conf_str = f" (confidence={triple.evidence.confidence:.2f})"
                lines.append(
                    f"  {subj_label} -> {triple.predicate} -> {obj_label}{conf_str}"
                )

        if result.neighbor_ids:
            neighbor_labels: list[str] = []
            for nid in list(result.neighbor_ids)[:10]:
                n = self._graph.get_node(nid)
                if n:
                    neighbor_labels.append(f"{n.label} [{n.entity_type.value}]")
            if neighbor_labels:
                lines.append("Nearby entities:")
                for label in neighbor_labels:
                    lines.append(f"  - {label}")

        return "\n".join(lines)

    def answer_risk_query(self) -> list[tuple[KnowledgeNode, list[KnowledgeNode]]]:
        """Return (repo_node, [risk_nodes]) pairs for all flagged repos."""
        results: list[tuple[KnowledgeNode, list[KnowledgeNode]]] = []
        for triple in self._graph.triples_by_predicate("flagged_with"):
            repo = self._graph.get_node(triple.subject_id)
            risk = self._graph.get_node(triple.object_id)
            if repo and risk:
                for existing_repo, risks in results:
                    if existing_repo.id == repo.id:
                        risks.append(risk)
                        break
                else:
                    results.append((repo, [risk]))
        return results

    def answer_relevance_query(
        self, min_confidence: float = 0.7
    ) -> list[KnowledgeNode]:
        """Return repos that support the AI/LLM claim above min_confidence.

        Results are sorted by relevance_score descending.
        """
        repos: list[KnowledgeNode] = []
        for triple in self._graph.triples_by_predicate("supports"):
            if triple.evidence and triple.evidence.confidence >= min_confidence:
                node = self._graph.get_node(triple.subject_id)
                if node and node.entity_type == EntityType.REPOSITORY:
                    repos.append(node)
        return sorted(
            repos,
            key=lambda n: n.properties.get("relevance_score", 0),
            reverse=True,
        )

    def summarize(self) -> str:
        """Return a plain-English summary of the graph contents."""
        stats = self._graph.stats()
        lines = [
            f"Knowledge graph: {stats['node_count']} entities, "
            f"{stats['triple_count']} relationships.",
            "Entity breakdown:",
        ]
        for etype, count in stats["entities_by_type"].items():
            lines.append(f"  {etype}: {count}")
        lines.append("Relationship types:")
        for pred, count in stats["predicates"].items():
            lines.append(f"  {pred}: {count}")
        return "\n".join(lines)
