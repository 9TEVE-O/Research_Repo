from __future__ import annotations
from datetime import datetime
from typing import Optional

from .models import ClaimNote, Evidence, WikiNote
from .storage import KnowledgeStore


def create_entity_note(
    store: KnowledgeStore,
    content_markdown: str,
    generated_by: str,
    source_ids: list[str],
    confidence: float,
    tags: Optional[list[str]] = None,
) -> WikiNote:
    note = WikiNote(
        id=WikiNote.new_id("entity"),
        type="entity",
        content_markdown=content_markdown,
        generated_by=generated_by,
        generated_at=datetime.utcnow(),
        source_ids=source_ids,
        confidence=confidence,
        tags=tags or [],
    )
    store.save_note(note)
    return note


def create_claim_note(
    store: KnowledgeStore,
    claim_text: str,
    evidence: list[Evidence],
    content_markdown: str,
    generated_by: str,
    source_ids: list[str],
    confidence: float,
    status: str = "proposed",
    tags: Optional[list[str]] = None,
) -> ClaimNote:
    """Rule 3: evidence list must not be empty."""
    if not evidence:
        raise ValueError("ClaimNote requires at least one Evidence item (Rule 3)")
    note = ClaimNote(
        id=ClaimNote.new_id(),
        claim_text=claim_text,
        evidence=evidence,
        status=status,
        content_markdown=content_markdown,
        generated_by=generated_by,
        generated_at=datetime.utcnow(),
        source_ids=source_ids,
        confidence=confidence,
        tags=tags or [],
    )
    store.save_note(note)
    return note


def create_summary_note(
    store: KnowledgeStore,
    content_markdown: str,
    generated_by: str,
    source_ids: list[str],
    confidence: float,
    tags: Optional[list[str]] = None,
) -> WikiNote:
    note = WikiNote(
        id=WikiNote.new_id("summary"),
        type="summary",
        content_markdown=content_markdown,
        generated_by=generated_by,
        generated_at=datetime.utcnow(),
        source_ids=source_ids,
        confidence=confidence,
        tags=tags or [],
    )
    store.save_note(note)
    return note


def update_note_content(
    store: KnowledgeStore,
    note_type: str,
    note_id: str,
    content_markdown: str,
    generated_by: str,
    confidence: Optional[float] = None,
) -> Optional[WikiNote | ClaimNote]:
    """Update content of an existing note. Rule 5: audit log records old/new hash."""
    note = store.load_note(note_type, note_id)
    if note is None:
        return None
    note.content_markdown = content_markdown
    note.generated_by = generated_by
    note.last_updated = datetime.utcnow()
    if confidence is not None:
        note.confidence = confidence
    store.save_note(note)
    return note
