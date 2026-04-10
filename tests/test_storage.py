"""Tests for storage.py."""

import pytest
from pathlib import Path

from models import ScoredRepo
from storage import init_db, load_repos, save_repos


def _repo(name="owner/repo", score=80) -> ScoredRepo:
    return ScoredRepo(
        name=name,
        url=f"https://github.com/{name}",
        relevance_score=score,
        summary="A useful summary.",
        reason="Very relevant.",
    )


@pytest.fixture
def db_path(tmp_path) -> Path:
    return tmp_path / "test.db"


class TestInitDb:
    def test_creates_table(self, db_path):
        init_db(db_path)
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='scored_repos'"
            ).fetchone()
        assert result is not None

    def test_idempotent(self, db_path):
        init_db(db_path)
        init_db(db_path)  # should not raise


class TestSaveAndLoadRepos:
    def test_roundtrip(self, db_path):
        repos = [_repo("a/b", 90), _repo("c/d", 75)]
        save_repos(repos, report_date="2024-01-15", db_path=db_path)
        loaded = load_repos(report_date="2024-01-15", db_path=db_path)
        assert len(loaded) == 2
        names = {r.name for r in loaded}
        assert names == {"a/b", "c/d"}

    def test_loaded_sorted_by_score_desc(self, db_path):
        repos = [_repo("low", 60), _repo("high", 95), _repo("mid", 75)]
        save_repos(repos, report_date="2024-01-15", db_path=db_path)
        loaded = load_repos(report_date="2024-01-15", db_path=db_path)
        scores = [r.relevance_score for r in loaded]
        assert scores == sorted(scores, reverse=True)

    def test_load_different_date_returns_empty(self, db_path):
        save_repos([_repo()], report_date="2024-01-15", db_path=db_path)
        loaded = load_repos(report_date="2024-01-16", db_path=db_path)
        assert loaded == []

    def test_empty_save_returns_empty_load(self, db_path):
        save_repos([], report_date="2024-01-15", db_path=db_path)
        loaded = load_repos(report_date="2024-01-15", db_path=db_path)
        assert loaded == []

    def test_load_creates_db_if_missing(self, db_path):
        loaded = load_repos(report_date="2024-01-15", db_path=db_path)
        assert loaded == []
        assert db_path.exists()
