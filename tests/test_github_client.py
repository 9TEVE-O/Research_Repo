"""Tests for github_client.py."""

import pytest
import responses as rsps_lib

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
    @rsps_lib.activate
    def test_returns_items(self):
        rsps_lib.add(
            rsps_lib.GET,
            GITHUB_SEARCH_URL,
            json=SAMPLE_RESPONSE,
            status=200,
        )
        result = fetch_candidates("fake-token")
        assert len(result) == 2
        assert result[0]["full_name"] == "owner/repo-a"

    @rsps_lib.activate
    def test_empty_items(self):
        rsps_lib.add(
            rsps_lib.GET,
            GITHUB_SEARCH_URL,
            json={"total_count": 0, "incomplete_results": False, "items": []},
            status=200,
        )
        result = fetch_candidates("fake-token")
        assert result == []

    @rsps_lib.activate
    def test_http_error_raises(self):
        import requests

        rsps_lib.add(
            rsps_lib.GET,
            GITHUB_SEARCH_URL,
            json={"message": "Bad credentials"},
            status=401,
        )
        with pytest.raises(requests.HTTPError):
            fetch_candidates("bad-token")

    @rsps_lib.activate
    def test_uses_provided_query_and_per_page(self):
        rsps_lib.add(
            rsps_lib.GET,
            GITHUB_SEARCH_URL,
            json=SAMPLE_RESPONSE,
            status=200,
        )
        fetch_candidates("tok", query="topic:agent", per_page=10)
        req = rsps_lib.calls[0].request
        assert "topic%3Aagent" in req.url or "topic:agent" in req.url
        assert "per_page=10" in req.url
