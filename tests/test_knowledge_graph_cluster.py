"""Tests for cluster detection, pattern mining, and bounded AI context."""

import pytest

from knowledge_graph.cluster import (
    Cluster,
    RelationshipPattern,
    build_subgraph,
    detect_patterns,
    find_connected_components,
)
from knowledge_graph.graph import KnowledgeGraph
from knowledge_graph.models import EntityType, KnowledgeNode, Triple
from knowledge_graph.retrieval import GraphRetriever


# ── Helpers ──────────────────────────────────────────────────────────────────


def node(nid: str, label: str, etype: EntityType = EntityType.REPOSITORY) -> KnowledgeNode:
    return KnowledgeNode(id=nid, label=label, entity_type=etype)


def triple(sub: str, pred: str, obj: str) -> Triple:
    return Triple(subject_id=sub, predicate=pred, object_id=obj)


def two_component_graph() -> KnowledgeGraph:
    """Graph with two disconnected components: {a,b,c} and {x,y}."""
    g = KnowledgeGraph()
    for nid, label in [("a", "A"), ("b", "B"), ("c", "C")]:
        g.add_node(node(nid, label))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    g.add_node(node("x", "X", EntityType.TOPIC))
    g.add_node(node("y", "Y", EntityType.TOPIC))
    g.add_triple(triple("x", "rel", "y"))
    return g


# ── find_connected_components ───────────────────────────────────────────────────


def test_single_component() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(node(nid, nid.upper()))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    clusters = find_connected_components(g)
    assert len(clusters) == 1
    assert clusters[0].size == 3


def test_two_components() -> None:
    g = two_component_graph()
    clusters = find_connected_components(g)
    assert len(clusters) == 2
    assert clusters[0].size == 3  # larger first
    assert clusters[1].size == 2


def test_isolated_nodes_are_own_components() -> None:
    g = KnowledgeGraph()
    g.add_node(node("a", "A"))
    g.add_node(node("b", "B"))
    clusters = find_connected_components(g)
    assert len(clusters) == 2
    for c in clusters:
        assert c.size == 1


def test_internal_triples_counted_correctly() -> None:
    g = two_component_graph()
    clusters = find_connected_components(g)
    large = next(c for c in clusters if c.size == 3)
    assert large.internal_triple_count == 2


def test_empty_graph_returns_no_clusters() -> None:
    assert find_connected_components(KnowledgeGraph()) == []


def test_dominant_type_reported() -> None:
    g = KnowledgeGraph()
    g.add_node(node("r1", "R1", EntityType.REPOSITORY))
    g.add_node(node("r2", "R2", EntityType.REPOSITORY))
    g.add_node(node("t1", "T1", EntityType.TOPIC))
    g.add_triple(triple("r1", "tagged_with", "t1"))
    g.add_triple(triple("r2", "tagged_with", "t1"))
    clusters = find_connected_components(g)
    assert len(clusters) == 1
    assert clusters[0].dominant_type() == "repository"


# ── detect_patterns ───────────────────────────────────────────────────────────────


def test_detect_patterns_empty_graph() -> None:
    assert detect_patterns(KnowledgeGraph()) == []


def test_detect_patterns_counts_correctly() -> None:
    g = KnowledgeGraph()
    for nid, etype in [("r1", EntityType.REPOSITORY), ("r2", EntityType.REPOSITORY),
                       ("t1", EntityType.TOPIC), ("t2", EntityType.TOPIC)]:
        g.add_node(node(nid, nid.upper(), etype))
    g.add_triple(triple("r1", "tagged_with", "t1"))
    g.add_triple(triple("r2", "tagged_with", "t2"))

    patterns = detect_patterns(g)
    assert len(patterns) == 1
    p = patterns[0]
    assert p.predicate == "tagged_with"
    assert p.subject_type == "repository"
    assert p.object_type == "topic"
    assert p.count == 2


def test_detect_patterns_sorted_by_frequency() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c", "d"]:
        g.add_node(node(nid, nid.upper()))
    g.add_triple(triple("a", "common", "b"))
    g.add_triple(triple("c", "common", "d"))
    g.add_triple(triple("a", "rare", "c"))
    patterns = detect_patterns(g)
    assert patterns[0].predicate == "common"
    assert patterns[0].count == 2
    assert patterns[1].predicate == "rare"
    assert patterns[1].count == 1


# ── build_subgraph ─────────────────────────────────────────────────────────────────


def test_build_subgraph_k0_seed_only() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(node(nid, nid.upper()))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    sub = build_subgraph(g, seed_ids=["a"], k=0)
    assert set(n.id for n in sub.all_nodes()) == {"a"}


def test_build_subgraph_k1_includes_neighbors() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(node(nid, nid.upper()))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    sub = build_subgraph(g, seed_ids=["a"], k=1)
    assert "a" in {n.id for n in sub.all_nodes()}
    assert "b" in {n.id for n in sub.all_nodes()}
    assert "c" not in {n.id for n in sub.all_nodes()}


def test_build_subgraph_preserves_internal_triples() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(node(nid, nid.upper()))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    sub = build_subgraph(g, seed_ids=["a", "b"], k=0)
    assert len(sub.all_triples()) == 1


# ── build_ai_context ───────────────────────────────────────────────────────────────


def test_build_ai_context_missing_node() -> None:
    g = KnowledgeGraph()
    ctx = GraphRetriever(g).build_ai_context("nonexistent")
    assert "No knowledge available" in ctx


def test_build_ai_context_includes_entity_header() -> None:
    g = KnowledgeGraph()
    g.add_node(node("a", "Alpha", EntityType.WORKFLOW))
    ctx = GraphRetriever(g).build_ai_context("a")
    assert "Alpha" in ctx
    assert "workflow" in ctx


def test_build_ai_context_includes_relationships() -> None:
    g = KnowledgeGraph()
    g.add_node(node("a", "Alpha"))
    g.add_node(node("b", "Beta"))
    g.add_triple(triple("a", "depends_on", "b"))
    ctx = GraphRetriever(g).build_ai_context("a", k=1)
    assert "depends_on" in ctx
    assert "Alpha" in ctx
    assert "Beta" in ctx


def test_build_ai_context_includes_neighbors() -> None:
    g = KnowledgeGraph()
    for nid, label in [("a", "Alpha"), ("b", "Beta"), ("c", "Gamma")]:
        g.add_node(node(nid, label))
    g.add_triple(triple("a", "rel", "b"))
    g.add_triple(triple("b", "rel", "c"))
    ctx = GraphRetriever(g).build_ai_context("a", k=2)
    assert "Nearby entities" in ctx
    assert "Gamma" in ctx
