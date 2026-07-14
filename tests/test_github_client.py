"""Tests for github_client.py."""

import pytest
from unittest.mock import Mock, patch

from github_client import GITHUB_SEARCH_URL, fetch_candidates


SAMPLE_RESPONSE = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [
        {
            "full_name": "owner/repo-a",
            "html_url": "https://github.com/owner/repo-a",
            "description": "Repo A",
            "topics": ["llm"],
            "stargazers_count": 200,
        },
        {
            "full_name": "owner/repo-b",
            "html_url": "https://github.com/owner/repo-b",
            "description": "Repo B",
            "topics": ["research"],
            "stargazers_count": 150,
        },
    ],
}


class TestFetchCandidates:
    @patch("github_client.requests.get")
    def test_returns_items(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_get.return_value = mock_response

        result = fetch_candidates("fake-token")
        assert len(result) == 2
        assert result[0]["full_name"] == "owner/repo-a"

    @patch("github_client.requests.get")
    def test_empty_items(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        }
        mock_get.return_value = mock_response

        result = fetch_candidates("fake-token")
        assert result == []

    @patch("github_client.requests.get")
    def test_http_error_raises(self, mock_get):
        import requests

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "401 Client Error"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            fetch_candidates("bad-token")

    @patch("github_client.requests.get")
    def test_uses_provided_query_and_per_page(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_get.return_value = mock_response

        fetch_candidates("tok", query="topic:agent", per_page=10)

        mock_get.assert_called_once()
        assert mock_get.call_args.kwargs["params"] == {
            "q": "topic:agent",
            "sort": "stars",
            "per_page": 10,
        }
