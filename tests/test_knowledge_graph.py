"""Tests for the knowledge graph architecture."""

import pytest

from knowledge_graph.audit import AuditEvent, AuditLog
from knowledge_graph.extractor import extract_graph_from_repos
from knowledge_graph.graph import KnowledgeGraph
from knowledge_graph.models import (
    EntityType,
    Evidence,
    KnowledgeNode,
    PermissionMask,
    PrivacyLevel,
    Triple,
)
from knowledge_graph.retrieval import GraphRetriever


# ── Helpers ──────────────────────────────────────────────────────────────────


def make_node(
    node_id: str,
    label: str,
    entity_type: EntityType = EntityType.REPOSITORY,
) -> KnowledgeNode:
    return KnowledgeNode(id=node_id, label=label, entity_type=entity_type)


def make_triple(sub: str, pred: str, obj: str) -> Triple:
    return Triple(subject_id=sub, predicate=pred, object_id=obj)


class FakeRepo:
    def __init__(
        self,
        name: str,
        url: str,
        score: int,
        summary: str,
        reason: str,
    ) -> None:
        self.name = name
        self.url = url
        self.relevance_score = score
        self.summary = summary
        self.reason = reason
        self.policy_flags: list[str] = []


# ── Evidence ──────────────────────────────────────────────────────────────────


def test_evidence_valid_confidence() -> None:
    e = Evidence(source="test", confidence=0.85)
    assert e.confidence == 0.85


def test_evidence_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        Evidence(source="test", confidence=1.5)


# ── KnowledgeGraph – entity layer ───────────────────────────────────────────────


def test_add_and_get_node() -> None:
    g = KnowledgeGraph()
    node = make_node("n1", "Node 1")
    g.add_node(node)
    assert g.get_node("n1") is node


def test_add_node_duplicate_is_ignored() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("n1", "Original"))
    g.add_node(make_node("n1", "Duplicate"))
    assert g.get_node("n1").label == "Original"


def test_get_node_missing_returns_none() -> None:
    g = KnowledgeGraph()
    assert g.get_node("nonexistent") is None


def test_nodes_by_type() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("r1", "Repo 1", EntityType.REPOSITORY))
    g.add_node(make_node("t1", "Topic 1", EntityType.TOPIC))
    repos = g.nodes_by_type(EntityType.REPOSITORY)
    assert len(repos) == 1
    assert repos[0].id == "r1"


# ── KnowledgeGraph – relationship layer ───────────────────────────────────────────


def test_add_triple_and_retrieve() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    g.add_node(make_node("b", "B"))
    t = make_triple("a", "relates_to", "b")
    g.add_triple(t)
    assert t in g.triples_from("a")
    assert t in g.triples_to("b")


def test_add_triple_missing_subject_raises() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("b", "B"))
    with pytest.raises(ValueError, match="Subject"):
        g.add_triple(make_triple("nonexistent", "rel", "b"))


def test_add_triple_missing_object_raises() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    with pytest.raises(ValueError, match="Object"):
        g.add_triple(make_triple("a", "rel", "nonexistent"))


def test_triples_by_predicate() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(make_node(nid, nid.upper()))
    g.add_triple(make_triple("a", "causes", "b"))
    g.add_triple(make_triple("b", "causes", "c"))
    g.add_triple(make_triple("a", "references", "c"))
    assert len(g.triples_by_predicate("causes")) == 2
    assert len(g.triples_by_predicate("references")) == 1


# ── k-hop retrieval ────────────────────────────────────────────────────────────────


def test_k_hop_neighbors_one_hop() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(make_node(nid, nid.upper()))
    g.add_triple(make_triple("a", "rel", "b"))
    g.add_triple(make_triple("a", "rel", "c"))
    assert g.k_hop_neighbors("a", k=1) == {"b", "c"}


def test_k_hop_neighbors_two_hops() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c", "d"]:
        g.add_node(make_node(nid, nid.upper()))
    g.add_triple(make_triple("a", "rel", "b"))
    g.add_triple(make_triple("b", "rel", "c"))
    g.add_triple(make_triple("c", "rel", "d"))
    neighbors_2 = g.k_hop_neighbors("a", k=2)
    assert "b" in neighbors_2
    assert "c" in neighbors_2
    assert "d" not in neighbors_2


def test_path_between_exists() -> None:
    g = KnowledgeGraph()
    for nid in ["a", "b", "c"]:
        g.add_node(make_node(nid, nid.upper()))
    g.add_triple(make_triple("a", "leads_to", "b"))
    g.add_triple(make_triple("b", "leads_to", "c"))
    assert g.path_between("a", "c") == ["a", "b", "c"]


def test_path_between_no_path() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    g.add_node(make_node("b", "B"))
    assert g.path_between("a", "b") is None


def test_path_between_same_node() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    assert g.path_between("a", "a") == ["a"]


# ── Graph stats ──────────────────────────────────────────────────────────────────


def test_stats() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("r1", "Repo 1", EntityType.REPOSITORY))
    g.add_node(make_node("t1", "Topic 1", EntityType.TOPIC))
    g.add_triple(make_triple("r1", "tagged_with", "t1"))
    stats = g.stats()
    assert stats["node_count"] == 2
    assert stats["triple_count"] == 1
    assert stats["entities_by_type"]["repository"] == 1
    assert stats["predicates"]["tagged_with"] == 1


# ── Audit log ──────────────────────────────────────────────────────────────────


def test_audit_records_node_additions() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("n1", "N1"))
    events = g.audit.events_by_type("add_node")
    assert len(events) == 1
    assert events[0].target_id == "n1"


def test_audit_records_triple_additions() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    g.add_node(make_node("b", "B"))
    g.add_triple(make_triple("a", "links", "b"))
    events = g.audit.events_by_type("add_triple")
    assert len(events) == 1


def test_audit_events_for_specific_node() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("n1", "N1"))
    g.add_node(make_node("n2", "N2"))
    assert len(g.audit.events_for("n1")) == 1
    assert len(g.audit.events_for("n2")) == 1


# ── Extractor ──────────────────────────────────────────────────────────────────


def test_extract_graph_from_repos_basic() -> None:
    repos = [
        FakeRepo(
            "org/high-relevance",
            "https://github.com/org/high-relevance",
            85,
            "Great repo",
            "Very relevant",
        ),
        FakeRepo(
            "org/low-relevance",
            "https://github.com/org/low-relevance",
            40,
            "Meh repo",
            "Not very relevant",
        ),
    ]
    graph = extract_graph_from_repos(repos)
    assert graph.get_node("repo:org_high_relevance") is not None
    assert graph.get_node("repo:org_low_relevance") is not None


def test_extract_high_relevance_creates_claim_triple() -> None:
    repos = [
        FakeRepo(
            "org/awesome",
            "https://github.com/org/awesome",
            90,
            "Awesome",
            "Top tier",
        )
    ]
    graph = extract_graph_from_repos(repos)
    assert graph.get_node("claim:ai_llm_research_relevance") is not None
    supports = graph.triples_by_predicate("supports")
    assert len(supports) == 1
    assert supports[0].evidence.confidence == pytest.approx(0.9)


def test_extract_low_relevance_no_claim_triple() -> None:
    repos = [
        FakeRepo(
            "org/weak",
            "https://github.com/org/weak",
            50,
            "Weak",
            "Low score",
        )
    ]
    graph = extract_graph_from_repos(repos)
    assert len(graph.triples_by_predicate("supports")) == 0


def test_extract_policy_flags() -> None:
    repo = FakeRepo(
        "org/risky",
        "https://github.com/org/risky",
        80,
        "Risky",
        "Has PII",
    )
    repo.policy_flags = ["pii_detected", "license_restriction"]
    graph = extract_graph_from_repos([repo])
    flagged = graph.triples_by_predicate("flagged_with")
    assert len(flagged) == 2


# ── GraphRetriever ────────────────────────────────────────────────────────────────


def test_retriever_context_for() -> None:
    g = KnowledgeGraph()
    g.add_node(make_node("a", "A"))
    g.add_node(make_node("b", "B"))
    g.add_triple(make_triple("a", "rel", "b"))
    result = GraphRetriever(g).context_for("a", k=1)
    assert result is not None
    assert result.node.id == "a"
    assert "b" in result.neighbor_ids


def test_retriever_context_for_missing_node() -> None:
    g = KnowledgeGraph()
    assert GraphRetriever(g).context_for("nonexistent") is None


def test_retriever_answer_relevance_query() -> None:
    repos = [
        FakeRepo("org/top", "https://github.com/org/top", 95, "Top", "Best"),
        FakeRepo("org/mid", "https://github.com/org/mid", 72, "Mid", "Good"),
        FakeRepo("org/low", "https://github.com/org/low", 55, "Low", "Meh"),
    ]
    graph = extract_graph_from_repos(repos)
    relevant = GraphRetriever(graph).answer_relevance_query(min_confidence=0.7)
    assert len(relevant) == 2
    assert relevant[0].properties["relevance_score"] > relevant[1].properties["relevance_score"]
