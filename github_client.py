"""Fetch candidate GitHub repositories via the Search API."""

import logging

import requests

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


def fetch_candidates(
    github_token: str,
    query: str = "topic:llm topic:research stars:>50",
    per_page: int = 20,
) -> list[dict]:
    """Search GitHub for candidate repositories and return raw repo dicts.

    Args:
        github_token: Personal access token with ``public_repo`` scope.
        query:        GitHub search query string.
        per_page:     Maximum number of results to fetch (1–100).

    Returns:
        A list of raw repository dicts as returned by the GitHub Search API.

    Raises:
        requests.HTTPError: When the GitHub API returns a non-2xx response.
        requests.RequestException: For network-level failures.
    """
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"q": query, "sort": "stars", "per_page": per_page}

    response = requests.get(
        GITHUB_SEARCH_URL, headers=headers, params=params, timeout=15
    )
    response.raise_for_status()

    items = response.json().get("items", [])
    logger.info("Fetched %d candidate repositories from GitHub.", len(items))
    return items
