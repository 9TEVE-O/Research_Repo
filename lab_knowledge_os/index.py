from __future__ import annotations
import json
import re
from pathlib import Path

from .storage import KnowledgeStore


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rebuild_indexes(store: KnowledgeStore) -> dict:
    """Build an inverted token index over all wiki notes.

    Writes to 05_logs/search_index.json.
    Returns {token: [note_id, ...]}
    """
    index: dict[str, list[str]] = {}

    for note_type in ("entity", "claim", "summary"):
        for note in store.list_notes(note_type):
            tokens = _tokenize(note.content_markdown)
            if hasattr(note, "claim_text"):
                tokens |= _tokenize(note.claim_text)
            for token in tokens:
                index.setdefault(token, [])
                if note.id not in index[token]:
                    index[token].append(note.id)

    index_path = store.root / "05_logs" / "search_index.json"
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def search_index(store: KnowledgeStore, query: str) -> list[str]:
    """Return sorted note IDs matching all query tokens (AND search)."""
    index_path = store.root / "05_logs" / "search_index.json"
    if not index_path.exists():
        rebuild_indexes(store)
        index_path = store.root / "05_logs" / "search_index.json"

    index: dict[str, list[str]] = json.loads(index_path.read_text(encoding="utf-8"))

    tokens = list(_tokenize(query))
    if not tokens:
        return []

    sets = [set(index.get(t, [])) for t in tokens]
    matches = sets[0]
    for s in sets[1:]:
        matches &= s
    return sorted(matches)
