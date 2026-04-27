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
