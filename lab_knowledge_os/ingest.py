from __future__ import annotations
import hashlib
from datetime import datetime
from pathlib import Path

from .models import Source
from .storage import KnowledgeStore


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest_file(
    store: KnowledgeStore,
    file_path: str | Path,
    source_url: str = "",
    mime_type: str = "text/plain",
) -> tuple[Source, bool]:
    """Ingest a file into the raw source layer.

    Returns (source, was_new). was_new=False means a duplicate hash was detected.
    Rule 1: raw sources are immutable — duplicates are silently skipped.
    """
    path = Path(file_path)
    raw_bytes = path.read_bytes()
    content_hash = _sha256(raw_bytes)

    existing_id = store.source_id_for_hash(content_hash)
    if existing_id:
        return store.load_source(existing_id), False

    source_id = Source.new_id()
    source = Source(
        source_id=source_id,
        hash=content_hash,
        ingested_at=datetime.utcnow(),
        original_path=str(path),
        mime_type=mime_type,
        source_url=source_url,
        immutable=True,
    )
    store.save_source(source, raw_bytes)
    return source, True


def ingest_bytes(
    store: KnowledgeStore,
    raw_bytes: bytes,
    original_path: str,
    source_url: str = "",
    mime_type: str = "text/plain",
) -> tuple[Source, bool]:
    """Ingest raw bytes directly (for web-clipped or in-memory content)."""
    content_hash = _sha256(raw_bytes)

    existing_id = store.source_id_for_hash(content_hash)
    if existing_id:
        return store.load_source(existing_id), False

    source_id = Source.new_id()
    source = Source(
        source_id=source_id,
        hash=content_hash,
        ingested_at=datetime.utcnow(),
        original_path=original_path,
        mime_type=mime_type,
        source_url=source_url,
        immutable=True,
    )
    store.save_source(source, raw_bytes)
    return source, True
