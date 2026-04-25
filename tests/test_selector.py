"""Tests for selector.py."""

import pytest

from models import ScoredRepo
from selector import SCORE_THRESHOLD, select_top_k


def _repo(name: str, score: int) -> ScoredRepo:
    return ScoredRepo(
        name=name,
        url=f"https://github.com/{name}",
        relevance_score=score,
        summary="summary",
        reason="reason",
    )


class TestSelectTopK:
    def test_returns_top_k_sorted(self):
        candidates = [_repo("a", 70), _repo("b", 90), _repo("c", 80)]
        result = select_top_k(candidates, k=2)
        assert len(result) == 2
        assert result[0].name == "b"
        assert result[1].name == "c"

    def test_excludes_below_threshold(self):
        candidates = [_repo("a", SCORE_THRESHOLD), _repo("b", 55)]
        result = select_top_k(candidates, k=3)
        assert len(result) == 1
        assert result[0].name == "b"

    def test_empty_input_returns_empty(self):
        assert select_top_k([], k=3) == []

    def test_all_below_threshold_returns_empty(self):
        candidates = [_repo("a", 10), _repo("b", SCORE_THRESHOLD)]
        assert select_top_k(candidates) == []

    def test_fewer_than_k_returns_all_qualifying(self):
        candidates = [_repo("a", 60), _repo("b", 70)]
        result = select_top_k(candidates, k=5)
        assert len(result) == 2

    def test_default_k_is_3(self):
        candidates = [_repo(str(i), 55 + i) for i in range(10)]
        result = select_top_k(candidates)
        assert len(result) == 3

    def test_sort_order_descending(self):
        candidates = [_repo("low", 60), _repo("mid", 75), _repo("high", 95)]
        result = select_top_k(candidates, k=3)
        scores = [r.relevance_score for r in result]
        assert scores == sorted(scores, reverse=True)
