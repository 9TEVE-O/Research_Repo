from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
import secrets


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


@dataclass
class Source:
    source_id: str
    hash: str
    ingested_at: datetime
    original_path: str
    mime_type: str = "text/plain"
    source_url: str = ""
    immutable: bool = True

    @staticmethod
    def new_id() -> str:
        return _new_id("src")

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "hash": self.hash,
            "ingested_at": self.ingested_at.isoformat(),
            "original_path": self.original_path,
            "mime_type": self.mime_type,
            "source_url": self.source_url,
            "immutable": self.immutable,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Source":
        return cls(
            source_id=d["source_id"],
            hash=d["hash"],
            ingested_at=datetime.fromisoformat(d["ingested_at"]),
            original_path=d["original_path"],
            mime_type=d.get("mime_type", "text/plain"),
            source_url=d.get("source_url", ""),
            immutable=d.get("immutable", True),
        )


@dataclass
class Evidence:
    source_id: str
    quote: str = ""
    location: str = ""

    def to_dict(self) -> dict:
        return {"source_id": self.source_id, "quote": self.quote, "location": self.location}

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(
            source_id=d["source_id"],
            quote=d.get("quote", ""),
            location=d.get("location", ""),
        )


@dataclass
class WikiNote:
    id: str
    type: Literal["entity", "claim", "contradiction", "summary"]
    content_markdown: str
    generated_by: str
    generated_at: datetime
    source_ids: list
    confidence: float
    human_reviewed: bool = False
    tags: list = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0-1, got {self.confidence}")

    @staticmethod
    def new_id(note_type: str) -> str:
        return _new_id(note_type[:3])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "content_markdown": self.content_markdown,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat(),
            "source_ids": self.source_ids,
            "confidence": self.confidence,
            "human_reviewed": self.human_reviewed,
            "tags": self.tags,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WikiNote":
        return cls(
            id=d["id"],
            type=d["type"],
            content_markdown=d["content_markdown"],
            generated_by=d["generated_by"],
            generated_at=datetime.fromisoformat(d["generated_at"]),
            source_ids=d.get("source_ids", []),
            confidence=d["confidence"],
            human_reviewed=d.get("human_reviewed", False),
            tags=d.get("tags", []),
            last_updated=datetime.fromisoformat(d.get("last_updated", d["generated_at"])),
        )


@dataclass
class ClaimNote:
    id: str
    claim_text: str
    evidence: list
    status: Literal["proposed", "verified", "contested", "deprecated"]
    content_markdown: str
    generated_by: str
    generated_at: datetime
    source_ids: list
    confidence: float
    type: str = "claim"
    human_reviewed: bool = False
    tags: list = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0-1, got {self.confidence}")

    @staticmethod
    def new_id() -> str:
        return _new_id("clm")

    def to_dict(self) -> dict:
        ev_list = []
        for e in self.evidence:
            ev_list.append(e.to_dict() if isinstance(e, Evidence) else e)
        return {
            "id": self.id,
            "type": self.type,
            "claim_text": self.claim_text,
            "evidence": ev_list,
            "status": self.status,
            "content_markdown": self.content_markdown,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat(),
            "source_ids": self.source_ids,
            "confidence": self.confidence,
            "human_reviewed": self.human_reviewed,
            "tags": self.tags,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ClaimNote":
        evidence = [Evidence.from_dict(e) for e in d.get("evidence", [])]
        return cls(
            id=d["id"],
            claim_text=d["claim_text"],
            evidence=evidence,
            status=d["status"],
            content_markdown=d["content_markdown"],
            generated_by=d["generated_by"],
            generated_at=datetime.fromisoformat(d["generated_at"]),
            source_ids=d.get("source_ids", []),
            confidence=d["confidence"],
            type=d.get("type", "claim"),
            human_reviewed=d.get("human_reviewed", False),
            tags=d.get("tags", []),
            last_updated=datetime.fromisoformat(d.get("last_updated", d["generated_at"])),
        )


@dataclass
class ContradictionLog:
    id: str
    claim_a_id: str
    claim_b_id: str
    detected_at: datetime
    resolution: Optional[str] = None

    @staticmethod
    def new_id() -> str:
        return _new_id("ctr")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
            "detected_at": self.detected_at.isoformat(),
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContradictionLog":
        return cls(
            id=d["id"],
            claim_a_id=d["claim_a_id"],
            claim_b_id=d["claim_b_id"],
            detected_at=datetime.fromisoformat(d["detected_at"]),
            resolution=d.get("resolution"),
        )
