from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ClaimNote, ContradictionLog, Source, WikiNote


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


class KnowledgeStore:
    """Filesystem backend for the LAB knowledge OS.

    Layout (under root):
        00_raw_sources/{source_id}/metadata.json
        00_raw_sources/{source_id}/content.original
        03_llm_wiki/entities/{id}.json
        03_llm_wiki/claims/{id}.json
        03_llm_wiki/contradictions/{id}.json
        03_llm_wiki/summaries/{id}.json
        05_logs/ingest.jsonl
        05_logs/update.jsonl
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._make_dirs()

    def _make_dirs(self) -> None:
        for d in [
            "00_raw_sources",
            "03_llm_wiki/entities",
            "03_llm_wiki/claims",
            "03_llm_wiki/contradictions",
            "03_llm_wiki/summaries",
            "05_logs",
        ]:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def _source_dir(self, source_id: str) -> Path:
        return self.root / "00_raw_sources" / source_id

    def _wiki_path(self, note_type: str, note_id: str) -> Path:
        folder_map = {
            "entity": "entities",
            "claim": "claims",
            "contradiction": "contradictions",
            "summary": "summaries",
        }
        folder = folder_map.get(note_type, note_type)
        return self.root / "03_llm_wiki" / folder / f"{note_id}.json"

    def _append_log(self, log_name: str, record: dict) -> None:
        log_path = self.root / "05_logs" / log_name
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    @staticmethod
    def _dict_hash(d: dict) -> str:
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()

    # ------------------------------------------------------------------
    # Source layer (immutable)
    # ------------------------------------------------------------------

    def save_source(self, source: Source, raw_bytes: bytes) -> bool:
        """Persists raw source. Returns False if already exists (immutable)."""
        src_dir = self._source_dir(source.source_id)
        meta_path = src_dir / "metadata.json"
        if meta_path.exists():
            return False
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "content.original").write_bytes(raw_bytes)
        meta_path.write_text(json.dumps(source.to_dict(), indent=2), encoding="utf-8")
        self._append_log("ingest.jsonl", {
            "event": "source_ingested",
            "source_id": source.source_id,
            "hash": source.hash,
            "original_path": source.original_path,
            "timestamp": _utc_now(),
        })
        return True

    def load_source(self, source_id: str) -> Optional[Source]:
        meta_path = self._source_dir(source_id) / "metadata.json"
        if not meta_path.exists():
            return None
        return Source.from_dict(json.loads(meta_path.read_text(encoding="utf-8")))

    def list_sources(self) -> list[Source]:
        sources = []
        src_root = self.root / "00_raw_sources"
        if not src_root.exists():
            return sources
        for entry in sorted(src_root.iterdir()):
            meta = entry / "metadata.json"
            if meta.exists():
                sources.append(Source.from_dict(json.loads(meta.read_text(encoding="utf-8"))))
        return sources

    def source_content(self, source_id: str) -> Optional[bytes]:
        p = self._source_dir(source_id) / "content.original"
        return p.read_bytes() if p.exists() else None

    def source_id_for_hash(self, content_hash: str) -> Optional[str]:
        for src in self.list_sources():
            if src.hash == content_hash:
                return src.source_id
        return None

    # ------------------------------------------------------------------
    # Wiki layer
    # ------------------------------------------------------------------

    def save_note(self, note: WikiNote | ClaimNote) -> None:
        path = self._wiki_path(note.type, note.id)
        old_hash = self._dict_hash(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None
        data = note.to_dict()
        new_hash = self._dict_hash(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._append_log("update.jsonl", {
            "event": "note_updated",
            "note_id": note.id,
            "note_type": note.type,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "timestamp": _utc_now(),
        })

    def load_note(self, note_type: str, note_id: str) -> Optional[WikiNote | ClaimNote]:
        path = self._wiki_path(note_type, note_id)
        if not path.exists():
            return None
        d = json.loads(path.read_text(encoding="utf-8"))
        if note_type == "claim":
            return ClaimNote.from_dict(d)
        return WikiNote.from_dict(d)

    def list_notes(self, note_type: str) -> list[WikiNote | ClaimNote]:
        folder_map = {
            "entity": "entities",
            "claim": "claims",
            "contradiction": "contradictions",
            "summary": "summaries",
        }
        folder = self.root / "03_llm_wiki" / folder_map.get(note_type, note_type)
        notes = []
        if not folder.exists():
            return notes
        for p in sorted(folder.glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            if note_type == "claim":
                notes.append(ClaimNote.from_dict(d))
            else:
                notes.append(WikiNote.from_dict(d))
        return notes

    def save_contradiction(self, log: ContradictionLog) -> None:
        path = self._wiki_path("contradiction", log.id)
        path.write_text(json.dumps(log.to_dict(), indent=2), encoding="utf-8")
        self._append_log("update.jsonl", {
            "event": "contradiction_logged",
            "contradiction_id": log.id,
            "claim_a_id": log.claim_a_id,
            "claim_b_id": log.claim_b_id,
            "timestamp": _utc_now(),
        })

    def list_contradictions(self) -> list[ContradictionLog]:
        folder = self.root / "03_llm_wiki" / "contradictions"
        items = []
        if not folder.exists():
            return items
        for p in sorted(folder.glob("*.json")):
            items.append(ContradictionLog.from_dict(json.loads(p.read_text(encoding="utf-8"))))
        return items

    # ------------------------------------------------------------------
    # Log access
    # ------------------------------------------------------------------

    def read_log(self, log_name: str) -> list[dict]:
        log_path = self.root / "05_logs" / log_name
        if not log_path.exists():
            return []
        records = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records
