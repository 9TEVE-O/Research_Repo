"""Tests for scoring.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from models import ScoredRepo
from scoring import score_all, score_repository


def _raw_repo(**kwargs) -> dict:
    defaults = {
        "full_name": "owner/repo",
        "html_url": "https://github.com/owner/repo",
        "description": "An LLM research tool",
        "topics": ["llm", "research"],
        "stargazers_count": 120,
    }
    defaults.update(kwargs)
    return defaults


def _make_llm_response(score=85, summary="A great repo.", reason="Very relevant.") -> str:
    return json.dumps(
        {"relevance_score": score, "summary": summary, "reason": reason}
    )


def _mock_client(content: str) -> MagicMock:
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    client.chat.completions.create.return_value.choices = [choice]
    return client


class TestScoreRepository:
    def test_successful_score(self):
        client = _mock_client(_make_llm_response())
        result = score_repository(_raw_repo(), client)
        assert isinstance(result, ScoredRepo)
        assert result.relevance_score == 85
        assert result.name == "owner/repo"

    def test_strips_markdown_fences(self):
        content = "```json\n" + _make_llm_response() + "\n```"
        client = _mock_client(content)
        result = score_repository(_raw_repo(), client)
        assert isinstance(result, ScoredRepo)

    def test_returns_none_on_invalid_json(self):
        client = _mock_client("not valid json")
        result = score_repository(_raw_repo(), client)
        assert result is None

    def test_returns_none_on_missing_key(self):
        client = _mock_client(json.dumps({"relevance_score": 80}))
        result = score_repository(_raw_repo(), client)
        assert result is None

    def test_returns_none_on_openai_error(self):
        import openai

        client = MagicMock()
        client.chat.completions.create.side_effect = openai.OpenAIError("err")
        result = score_repository(_raw_repo(), client)
        assert result is None


class TestScoreAll:
    def test_skips_failed_repos(self):
        good_client = _mock_client(_make_llm_response())
        bad_client = _mock_client("bad json")

        repos = [_raw_repo(full_name="a/good"), _raw_repo(full_name="b/bad")]
        # Use good client but bad JSON for second call
        call_count = 0
        original = good_client.chat.completions.create.side_effect

        responses = [
            MagicMock(choices=[MagicMock(message=MagicMock(content=_make_llm_response()))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="bad json"))]),
        ]
        good_client.chat.completions.create.side_effect = responses

        result = score_all(repos, good_client)
        assert len(result) == 1
        assert result[0].name == "a/good"

    def test_empty_input_returns_empty(self):
        client = MagicMock()
        result = score_all([], client)
        assert result == []
