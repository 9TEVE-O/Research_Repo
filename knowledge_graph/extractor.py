"""Extract a KnowledgeGraph from ScoredRepo objects."""

from __future__ import annotations

import re
from datetime import datetime

from .graph import KnowledgeGraph
from .models import EntityType, Evidence, KnowledgeNode, Triple


def _slugify(text: str) -> str:
    """Convert arbitrary text to a safe, lowercase node-id fragment."""
    return re.sub(r"[^a-z0-9_]", "_", text.lower().strip())[:64]


def _make_node_id(prefix: str, label: str) -> str:
    return f"{prefix}:{_slugify(label)}"


def extract_graph_from_repos(repos: list) -> KnowledgeGraph:
    """Build a KnowledgeGraph from a list of ScoredRepo objects.

    Each repo becomes a REPOSITORY node.  Topics (if present) become TOPIC
    nodes connected via ``tagged_with`` triples.  Repos scoring >= 70 get a
    shared CLAIM node connected via ``supports`` triples whose confidence
    equals ``relevance_score / 100``.  Policy flags (if present) become RISK
    nodes connected via ``flagged_with`` triples.
    """
    graph = KnowledgeGraph()
    source = "github_research_agent"
    ts = datetime.utcnow()

    for repo in repos:
        repo_id = _make_node_id("repo", repo.name)

        graph.add_node(
            KnowledgeNode(
                id=repo_id,
                label=repo.name,
                entity_type=EntityType.REPOSITORY,
                summary=repo.summary,
                properties={
                    "url": repo.url,
                    "relevance_score": repo.relevance_score,
                    "reason": repo.reason,
                },
            )
        )

        # Topic nodes ─ only present when the repo carries a ``properties`` dict
        topics: list[str] = []
        if hasattr(repo, "properties") and isinstance(repo.properties, dict):
            topics = repo.properties.get("topics", [])
        for topic in topics:
            topic_id = _make_node_id("topic", topic)
            if not graph.get_node(topic_id):
                graph.add_node(
                    KnowledgeNode(
                        id=topic_id,
                        label=topic,
                        entity_type=EntityType.TOPIC,
                    )
                )
            graph.add_triple(
                Triple(
                    subject_id=repo_id,
                    predicate="tagged_with",
                    object_id=topic_id,
                    evidence=Evidence(source=source, timestamp=ts, confidence=1.0),
                )
            )

        # High-relevance repos support the shared AI/LLM research claim
        if repo.relevance_score >= 70:
            claim_id = "claim:ai_llm_research_relevance"
            if not graph.get_node(claim_id):
                graph.add_node(
                    KnowledgeNode(
                        id=claim_id,
                        label="AI/LLM Research Relevance",
                        entity_type=EntityType.CLAIM,
                        summary=(
                            "Repository demonstrates strong relevance to "
                            "AI/LLM research."
                        ),
                    )
                )
            graph.add_triple(
                Triple(
                    subject_id=repo_id,
                    predicate="supports",
                    object_id=claim_id,
                    evidence=Evidence(
                        source=source,
                        timestamp=ts,
                        confidence=repo.relevance_score / 100.0,
                        quote=repo.reason,
                    ),
                )
            )

        # Policy risk nodes ─ present when the repo has a ``policy_flags`` attr
        policy_flags: list[str] = getattr(repo, "policy_flags", [])
        for flag in policy_flags:
            risk_id = _make_node_id("risk", flag)
            if not graph.get_node(risk_id):
                graph.add_node(
                    KnowledgeNode(
                        id=risk_id,
                        label=flag,
                        entity_type=EntityType.RISK,
                        summary=f"Policy risk: {flag}",
                    )
                )
            graph.add_triple(
                Triple(
                    subject_id=repo_id,
                    predicate="flagged_with",
                    object_id=risk_id,
                    evidence=Evidence(source=source, timestamp=ts, confidence=0.9),
                )
            )

    return graph
