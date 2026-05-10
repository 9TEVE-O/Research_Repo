from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .models import ClaimNote
from .storage import KnowledgeStore


@dataclass
class LintReport:
    orphan_pages: list = field(default_factory=list)
    stale_claims: list = field(default_factory=list)
    missing_evidence: list = field(default_factory=list)
    unreferenced_sources: list = field(default_factory=list)
    stale_threshold_days: int = 60

    @property
    def is_clean(self) -> bool:
        return not (
            self.orphan_pages
            or self.stale_claims
            or self.missing_evidence
            or self.unreferenced_sources
        )

    def summary(self) -> str:
        parts = []
        if self.orphan_pages:
            parts.append(f"{len(self.orphan_pages)} orphan page(s)")
        if self.stale_claims:
            parts.append(f"{len(self.stale_claims)} stale claim(s) (>{self.stale_threshold_days}d, unreviewed)")
        if self.missing_evidence:
            parts.append(f"{len(self.missing_evidence)} claim(s) missing evidence (Rule 3 violation)")
        if self.unreferenced_sources:
            parts.append(f"{len(self.unreferenced_sources)} unreferenced source(s)")
        return "Clean." if not parts else "; ".join(parts)


def _check_orphan_pages(store: KnowledgeStore) -> list:
    orphans = []
    for note_type in ("entity", "claim", "summary"):
        for note in store.list_notes(note_type):
            if not getattr(note, "source_ids", []):
                orphans.append(note.id)
    return orphans


def _check_stale_claims(store: KnowledgeStore, threshold_days: int) -> list:
    cutoff = datetime.utcnow() - timedelta(days=threshold_days)
    stale = []
    for note in store.list_notes("claim"):
        if isinstance(note, ClaimNote):
            if not note.human_reviewed and note.last_updated < cutoff:
                stale.append(note.id)
    return stale


def _check_missing_evidence(store: KnowledgeStore) -> list:
    missing = []
    for note in store.list_notes("claim"):
        if isinstance(note, ClaimNote):
            if not note.evidence:
                missing.append(note.id)
    return missing


def _check_unreferenced_sources(store: KnowledgeStore) -> list:
    all_source_ids = {s.source_id for s in store.list_sources()}
    cited_ids: set = set()
    for note_type in ("entity", "claim", "summary"):
        for note in store.list_notes(note_type):
            for sid in getattr(note, "source_ids", []):
                cited_ids.add(sid)
    return sorted(all_source_ids - cited_ids)


def run_health_check(store: KnowledgeStore, stale_threshold_days: int = 60) -> LintReport:
    return LintReport(
        orphan_pages=_check_orphan_pages(store),
        stale_claims=_check_stale_claims(store, stale_threshold_days),
        missing_evidence=_check_missing_evidence(store),
        unreferenced_sources=_check_unreferenced_sources(store),
        stale_threshold_days=stale_threshold_days,
    )
