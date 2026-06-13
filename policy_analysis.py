"""Policy enrichment for repository scan results."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

import requests

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from policy_analyzer import PolicyAnalyzer
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing policy_analyzer.py in the repository root. "
        "Create policy_analyzer.py or disable policy enrichment."
    ) from exc

_GITHUB_README_URL = "https://api.github.com/repos/{owner}/{repo}/readme"
_REQUEST_TIMEOUT_SECS = 15
_SUMMARY_MAX_CHARS = 500
_LIST_MAX_ITEMS = 10


def _flatten_unique(mapping: dict | None, limit: int = _LIST_MAX_ITEMS) -> list[str]:
    if not mapping:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for values in mapping.values():
        if not values:
            continue
        for item in values:
            text = str(item)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
                if len(out) >= limit:
                    return out
    return out


def _dedup_cap(values: list | None, limit: int = _LIST_MAX_ITEMS) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in values:
        text = str(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
            if len(out) >= limit:
                break
    return out


def _fetch_readme_text(full_name: str, github_token: str, max_chars: int) -> str:
    if "/" not in full_name:
        raise ValueError("Expected repo name in owner/repo form, got %r" % full_name)

    owner, repo = full_name.split("/", 1)
    headers = {
        "Accept": "application/vnd.github.raw",
        "User-Agent": "Research_Repo-policy-analyzer",
    }
    if github_token:
        headers["Authorization"] = "Bearer " + github_token

    url = _GITHUB_README_URL.format(owner=owner, repo=repo)
    response = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT_SECS)
    response.raise_for_status()
    return response.text[:max_chars]


def _empty_policy(error: str | None = None) -> dict:
    return {
        "summary": "",
        "privacy_concerns": {"high": 0, "medium": 0, "low": 0},
        "third_party_services": [],
        "data_sharing": [],
        "technologies": [],
        "analyzed_chars": 0,
        "error": error,
    }


def annotate_with_policy(
    repos: list[dict], github_token: str, max_text_chars: int = 20000
) -> list[dict]:
    analyzer = PolicyAnalyzer()

    for repo in repos:
        full_name = repo.get("name", "")

        try:
            text = _fetch_readme_text(full_name, github_token, max_text_chars)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch README for %s: %s", full_name or "<unknown>", exc)
            repo["policy"] = _empty_policy(error=str(exc))
            continue
        except ValueError as exc:
            logger.warning("Invalid repo name %r: %s", full_name, exc)
            repo["policy"] = _empty_policy(error=str(exc))
            continue

        try:
            analysis = analyzer.analyze(text, company_name=full_name or "Unknown")
            concerns = analysis.get("privacy_concerns") or {}
            summary_text = analyzer.generate_user_summary(analysis) or ""

            repo["policy"] = {
                "summary": summary_text[:_SUMMARY_MAX_CHARS],
                "privacy_concerns": {
                    "high": len(concerns.get("high", []) or []),
                    "medium": len(concerns.get("medium", []) or []),
                    "low": len(concerns.get("low", []) or []),
                },
                "third_party_services": _flatten_unique(
                    analysis.get("third_party_services_categorised")
                ),
                "data_sharing": _dedup_cap(
                    (analysis.get("data_sharing_summary") or {}).get("shared_with")
                ),
                "technologies": _flatten_unique(analysis.get("technologies_detected")),
                "analyzed_chars": len(text),
                "error": None,
            }
        except Exception as exc:
            logger.warning("PolicyAnalyzer failed for %s: %s", full_name or "<unknown>", exc)
            repo["policy"] = _empty_policy(error=str(exc))

    return repos
