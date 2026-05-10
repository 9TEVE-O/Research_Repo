import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from lab_knowledge_os.models import ClaimNote, ContradictionLog, Evidence, Source, WikiNote
from lab_knowledge_os.storage import KnowledgeStore
from lab_knowledge_os.ingest import ingest_bytes, ingest_file
from lab_knowledge_os.wiki import create_claim_note, create_entity_note, create_summary_note, update_note_content
from lab_knowledge_os.index import rebuild_indexes, search_index
from lab_knowledge_os.lint import LintReport, run_health_check
from lab_knowledge_os.exporters import export_chatgpt_context, export_claude_context, export_source_index


@pytest.fixture
def store(tmp_path):
    return KnowledgeStore(tmp_path)


@pytest.fixture
def sample_source(store):
    raw = b"This is a test source document about machine learning."
    src, _ = ingest_bytes(store, raw, "test.txt")
    return src


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def test_source_new_id():
    sid = Source.new_id()
    assert sid.startswith("src_")
    assert len(sid) == 16  # "src_" + 12 hex chars


def test_evidence_roundtrip():
    ev = Evidence(source_id="src_abc123456789", quote="hello", location="p.1")
    assert Evidence.from_dict(ev.to_dict()) == ev


def test_wiki_note_invalid_confidence_high():
    with pytest.raises(ValueError):
        WikiNote(
            id="ent_x", type="entity", content_markdown="x",
            generated_by="test", generated_at=datetime.utcnow(),
            source_ids=[], confidence=1.5,
        )


def test_wiki_note_invalid_confidence_negative():
    with pytest.raises(ValueError):
        WikiNote(
            id="ent_x", type="entity", content_markdown="x",
            generated_by="test", generated_at=datetime.utcnow(),
            source_ids=[], confidence=-0.1,
        )


def test_wiki_note_roundtrip():
    note = WikiNote(
        id="ent_abc123456789", type="entity", content_markdown="# Test",
        generated_by="pytest", generated_at=datetime.utcnow(),
        source_ids=["src_aaa111222333"], confidence=0.9,
    )
    restored = WikiNote.from_dict(note.to_dict())
    assert restored.id == note.id
    assert restored.confidence == note.confidence
    assert restored.type == "entity"


def test_claim_note_invalid_confidence():
    with pytest.raises(ValueError):
        ClaimNote(
            id="clm_x", claim_text="x", evidence=[Evidence("src_a")],
            status="proposed", content_markdown="y", generated_by="t",
            generated_at=datetime.utcnow(), source_ids=["src_a"], confidence=-0.1,
        )


def test_contradiction_log_roundtrip():
    c = ContradictionLog(
        id="ctr_abc", claim_a_id="clm_1", claim_b_id="clm_2",
        detected_at=datetime.utcnow(), resolution=None,
    )
    assert ContradictionLog.from_dict(c.to_dict()).claim_a_id == "clm_1"


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def test_save_source_immutable(store):
    raw = b"immutable data"
    src, was_new = ingest_bytes(store, raw, "doc.txt")
    assert was_new
    src2, was_new2 = ingest_bytes(store, raw, "doc.txt")
    assert not was_new2
    assert src2.source_id == src.source_id


def test_load_source(store, sample_source):
    loaded = store.load_source(sample_source.source_id)
    assert loaded is not None
    assert loaded.source_id == sample_source.source_id
    assert loaded.immutable is True


def test_source_content(store, sample_source):
    content = store.source_content(sample_source.source_id)
    assert content == b"This is a test source document about machine learning."


def test_list_sources(store, sample_source):
    sources = store.list_sources()
    assert len(sources) == 1


def test_save_and_load_note(store, sample_source):
    note = WikiNote(
        id="ent_test123456789", type="entity", content_markdown="# Entity",
        generated_by="pytest", generated_at=datetime.utcnow(),
        source_ids=[sample_source.source_id], confidence=0.8,
    )
    store.save_note(note)
    loaded = store.load_note("entity", "ent_test123456789")
    assert loaded is not None
    assert loaded.content_markdown == "# Entity"


def test_update_log_on_save(store, sample_source):
    note = WikiNote(
        id="ent_log1234567890", type="entity", content_markdown="v1",
        generated_by="pytest", generated_at=datetime.utcnow(),
        source_ids=[sample_source.source_id], confidence=0.7,
    )
    store.save_note(note)
    note.content_markdown = "v2"
    store.save_note(note)
    log = store.read_log("update.jsonl")
    assert len(log) == 2
    assert log[0]["old_hash"] is None
    assert log[1]["old_hash"] is not None


def test_save_contradiction(store):
    c = ContradictionLog(
        id="ctr_abc123456789", claim_a_id="clm_1", claim_b_id="clm_2",
        detected_at=datetime.utcnow(),
    )
    store.save_contradiction(c)
    results = store.list_contradictions()
    assert len(results) == 1
    assert results[0].claim_a_id == "clm_1"


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

def test_ingest_file(store, tmp_path):
    f = tmp_path / "article.txt"
    f.write_bytes(b"Article content here")
    src, was_new = ingest_file(store, f)
    assert was_new
    assert src.original_path == str(f)


def test_ingest_dedup(store):
    raw = b"duplicate content"
    s1, new1 = ingest_bytes(store, raw, "a.txt")
    s2, new2 = ingest_bytes(store, raw, "b.txt")
    assert new1 and not new2
    assert s1.source_id == s2.source_id


def test_ingest_logs_event(store):
    ingest_bytes(store, b"logged content", "log_test.txt")
    log = store.read_log("ingest.jsonl")
    assert len(log) == 1
    assert log[0]["event"] == "source_ingested"


# ---------------------------------------------------------------------------
# Wiki
# ---------------------------------------------------------------------------

def test_create_entity_note(store, sample_source):
    note = create_entity_note(store, "# Topic", "pytest", [sample_source.source_id], 0.9)
    assert note.type == "entity"
    loaded = store.load_note("entity", note.id)
    assert loaded.content_markdown == "# Topic"


def test_create_claim_note(store, sample_source):
    ev = Evidence(source_id=sample_source.source_id, quote="test quote", location="p.1")
    note = create_claim_note(
        store, "X causes Y", [ev], "# Claim", "pytest",
        [sample_source.source_id], 0.7,
    )
    assert note.type == "claim"
    assert note.status == "proposed"


def test_create_claim_no_evidence_raises(store, sample_source):
    with pytest.raises(ValueError, match="Rule 3"):
        create_claim_note(store, "X causes Y", [], "# Claim", "pytest", [sample_source.source_id], 0.7)


def test_create_summary_note(store, sample_source):
    note = create_summary_note(store, "# Summary", "pytest", [sample_source.source_id], 0.85)
    assert note.type == "summary"


def test_update_note_content(store, sample_source):
    note = create_entity_note(store, "# v1", "pytest", [sample_source.source_id], 0.8)
    updated = update_note_content(store, "entity", note.id, "# v2", "pytest", confidence=0.9)
    assert updated is not None
    assert updated.content_markdown == "# v2"
    assert updated.confidence == 0.9


def test_update_note_missing_returns_none(store):
    result = update_note_content(store, "entity", "nonexistent", "new content", "pytest")
    assert result is None


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

def test_rebuild_and_search(store, sample_source):
    create_entity_note(store, "machine learning transformers attention", "pytest", [sample_source.source_id], 0.8)
    rebuild_indexes(store)
    results = search_index(store, "machine learning")
    assert len(results) > 0


def test_search_no_match(store, sample_source):
    create_entity_note(store, "quantum entanglement physics", "pytest", [sample_source.source_id], 0.8)
    rebuild_indexes(store)
    results = search_index(store, "blockchain")
    assert results == []


def test_search_empty_query(store, sample_source):
    rebuild_indexes(store)
    results = search_index(store, "")
    assert results == []


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

def test_clean_store(store, sample_source):
    create_entity_note(store, "# Entity", "pytest", [sample_source.source_id], 0.9)
    report = run_health_check(store)
    assert report.unreferenced_sources == []
    assert report.orphan_pages == []
    assert report.missing_evidence == []
    assert report.is_clean


def test_orphan_page(store, sample_source):
    note = WikiNote(
        id="ent_orphan123456", type="entity", content_markdown="orphan",
        generated_by="pytest", generated_at=datetime.utcnow(),
        source_ids=[], confidence=0.5,
    )
    store.save_note(note)
    report = run_health_check(store)
    assert "ent_orphan123456" in report.orphan_pages


def test_missing_evidence_claim(store, sample_source):
    claim = ClaimNote(
        id=ClaimNote.new_id(), claim_text="unsupported claim",
        evidence=[], status="proposed", content_markdown="# Claim",
        generated_by="pytest", generated_at=datetime.utcnow(),
        source_ids=[sample_source.source_id], confidence=0.3,
    )
    store.save_note(claim)
    report = run_health_check(store)
    assert claim.id in report.missing_evidence


def test_unreferenced_source(store, sample_source):
    report = run_health_check(store)
    assert sample_source.source_id in report.unreferenced_sources


def test_lint_summary_issues(store, sample_source):
    report = run_health_check(store)
    assert not report.is_clean
    assert "unreferenced" in report.summary()


def test_lint_report_is_clean(store, sample_source):
    create_entity_note(store, "# Entity", "pytest", [sample_source.source_id], 0.9)
    report = run_health_check(store)
    assert report.is_clean
    assert report.summary() == "Clean."


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------

def test_export_claude_context(store, sample_source):
    create_entity_note(store, "# Entity Page", "pytest", [sample_source.source_id], 0.9)
    md = export_claude_context(store)
    assert "LAB Knowledge OS" in md
    assert "## Entities" in md
    assert sample_source.source_id in md


def test_export_chatgpt_context(store, sample_source):
    create_entity_note(store, "# Entity", "pytest", [sample_source.source_id], 0.9)
    payload = json.loads(export_chatgpt_context(store))
    assert "entities" in payload
    assert len(payload["entities"]) == 1


def test_export_source_index(store, sample_source):
    md = export_source_index(store)
    assert "Source Index" in md
    assert sample_source.source_id in md
    assert sample_source.hash[:12] in md
