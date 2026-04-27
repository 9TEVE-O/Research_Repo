"""Core data models: nodes, triples, evidence, and permissions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    PERSON = "person"
    PROJECT = "project"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    CLAIM = "claim"
    RISK = "risk"
    TOOL = "tool"
    POLICY = "policy"
    REPOSITORY = "repository"
    TOPIC = "topic"
    ORGANIZATION = "organization"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


@dataclass
class Evidence:
    """Provenance record attached to a triple."""

    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    quote: str = ""
    page: str = ""

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence}"
            )


@dataclass
class PermissionMask:
    """Access-control mask for a knowledge node."""

    can_view_original: list[str] = field(default_factory=list)
    can_view_summary: list[str] = field(default_factory=list)
    can_view_metadata: list[str] = field(default_factory=list)
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC


@dataclass
class KnowledgeNode:
    """An entity in the knowledge graph."""

    id: str
    label: str
    entity_type: EntityType
    summary: str = ""
    properties: dict = field(default_factory=dict)
    privacy: PermissionMask = field(default_factory=PermissionMask)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "entity_type": self.entity_type.value,
            "summary": self.summary,
            "properties": self.properties,
            "privacy_level": self.privacy.privacy_level.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Triple:
    """The atomic unit of knowledge: subject -> predicate -> object."""

    subject_id: str
    predicate: str
    object_id: str
    evidence: Optional[Evidence] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def id(self) -> str:
        return f"{self.subject_id}|{self.predicate}|{self.object_id}"

    def to_dict(self) -> dict:
        result: dict = {
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_id": self.object_id,
            "created_at": self.created_at.isoformat(),
        }
        if self.evidence:
            result["evidence"] = {
                "source": self.evidence.source,
                "timestamp": self.evidence.timestamp.isoformat(),
                "confidence": self.evidence.confidence,
                "quote": self.evidence.quote,
            }
        return result
