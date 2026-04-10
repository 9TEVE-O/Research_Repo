"""Tests for models.py."""

import pytest

from models import ScoredRepo


def _make_repo(**kwargs) -> ScoredRepo:
    defaults = dict(
        name="owner/repo",
        url="https://github.com/owner/repo",
        relevance_score=75,
        summary="A great repo.",
        reason="Highly relevant to LLM research.",
    )
    defaults.update(kwargs)
    return ScoredRepo(**defaults)


class TestScoredRepo:
    def test_to_dict_roundtrip(self):
        repo = _make_repo()
        assert ScoredRepo.from_dict(repo.to_dict()) == repo

    def test_to_dict_keys(self):
        repo = _make_repo()
        d = repo.to_dict()
        assert set(d) == {"name", "url", "relevance_score", "summary", "reason"}

    def test_from_dict_coerces_score_to_int(self):
        data = {
            "name": "a/b",
            "url": "https://example.com",
            "relevance_score": "82",
            "summary": "s",
            "reason": "r",
        }
        repo = ScoredRepo.from_dict(data)
        assert repo.relevance_score == 82
        assert isinstance(repo.relevance_score, int)

    def test_from_dict_missing_key_raises(self):
        with pytest.raises(KeyError):
            ScoredRepo.from_dict({"name": "a/b"})
