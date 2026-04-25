"""Integration layer for the AI-Policy-Terms-Analyzer library.

This module wraps the third-party ``PolicyAnalyzer`` (vendored as a git
submodule under ``external/AI-Policy-Terms-Analyzer``) so that scored
repository dicts produced by :mod:`agent` can be enriched with a
condensed privacy / terms analysis of each repository's README.

The enrichment is best-effort: any single repository whose analysis
fails is annotated with an ``error`` message but never raises, so the
rest of the pipeline continues unaffected.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ── Vendored submodule bootstrap ─────────────────────────────────────────────

_VENDORED_PATH = Path(__file__).parent / "external" / "AI-Policy-Terms-Analyzer"

if not _VENDORED_PATH.is_dir():
    raise RuntimeError(
        "AI-Policy-Terms-Analyzer submodule is missing at "
        f"{_VENDORED_PATH}. Run `git submodule update --init --recursive` "
        "from the repository root to fetch it."
    )

if str(_VENDORED_PATH) not in sys.path:
    sys.path.insert(0, str(_VENDORED_PATH))

from policy_analyzer import PolicyAnalyzer  # noqa: E402  (path injected above)
from document_scanner import DocumentScanner  # noqa: E402,F401  (re-exported)

# ── Constants ────────────────────────────────────────────────────────────────

_GITHUB_README_URL = "https://api.github.com/repos/{owner}/{repo}/readme"
_REQUEST_TIMEOUT_SECS = 15
_SUMMARY_MAX_CHARS = 500
_LIST_MAX_ITEMS = 10


# ── Helpers ──────────────────────────────────────────────────────────────────


def _flatten_unique(mapping: dict | None, limit: int = _LIST_MAX_ITEMS) -> list[str]:
    """Flatten a ``{category: [items]}`` mapping into an order-preserving unique list.

    Args:
        mapping: Dict whose values are iterables of strings; ``None`` is treated
            as empty.
        limit: Maximum number of items to return.

    Returns:
        Deduplicated list of stringified items, preserving first-seen order
        and truncated to ``limit`` elements.
    """
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
    """Deduplicate a list (preserving order) and truncate to ``limit`` items.

    Args:
        values: Input list; ``None`` is treated as empty.
        limit: Maximum number of items to return.

    Returns:
        Deduplicated, truncated list of strings.
    """
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


def _fetch_readme_text(
    full_name: str, github_token: str, max_chars: int
) -> str:
    """Fetch a repository's README as decoded text from the GitHub API.

    Args:
        full_name: Repository slug in ``"owner/repo"`` form.
        github_token: GitHub token used for ``Authorization: Bearer``.
        max_chars: Maximum number of characters to return; the response body
            is sliced to this length.

    Returns:
        The raw README text, truncated to ``max_chars``.

    Raises:
        ValueError: If ``full_name`` is not in ``owner/repo`` form.
        requests.RequestException: On any network / HTTP error.
    """
    if "/" not in full_name:
        raise ValueError("Expected repo name in 'owner/repo' form, got %r" % full_name)
    owner, repo = full_name.split("/", 1)

    headers = {
        "Accept": "application/vnd.github.raw",
        "Authorization": f"Bearer {github_token}",
        "User-Agent": "Research_Repo-policy-analyzer",
    }
    url = _GITHUB_README_URL.format(owner=owner, repo=repo)

    response = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT_SECS)
    response.raise_for_status()
    return response.text[:max_chars]


def _empty_policy(error: str | None = None) -> dict:
    """Return a policy block with all list/count fields empty.

    Args:
        error: Optional human-readable error message to attach.

    Returns:
        A dict matching the ``repo['policy']`` schema with empty defaults.
    """
    return {
        "summary": "",
        "privacy_concerns": {"high": 0, "medium": 0, "low": 0},
        "third_party_services": [],
        "data_sharing": [],
        "technologies": [],
        "analyzed_chars": 0,
        "error": error,
    }


# ── Public API ───────────────────────────────────────────────────────────────


def annotate_with_policy(
    repos: list[dict],
    github_token: str,
    max_text_chars: int = 20000,
) -> list[dict]:
    """Enrich scored repos with policy/terms analysis.

    For each repo dict (must contain ``'name'`` like ``'owner/repo'`` and
    ``'url'``), fetches the repository README via the GitHub API, runs
    :meth:`PolicyAnalyzer.analyze`, and attaches a ``'policy'`` key to the
    dict with a condensed result::

        repo['policy'] = {
            'summary': str,                 # short human-readable summary
            'privacy_concerns': {'high': int, 'medium': int, 'low': int},
            'third_party_services': list[str],  # flattened, deduped, <=10
            'data_sharing': list[str],          # shared_with, <=10
            'technologies': list[str],          # flattened, <=10
            'analyzed_chars': int,
            'error': str | None,
        }

    Failures for a single repo are logged as warnings and represented with
    ``error`` populated and other fields empty; the repo dict is always
    returned.

    Args:
        repos: List of scored repo dicts from the agent pipeline.
        github_token: GitHub token used to authenticate README fetches.
        max_text_chars: Maximum number of README characters to analyze
            per repository.

    Returns:
        The same list of dicts, each mutated to include a ``'policy'`` key.
    """
    analyzer = PolicyAnalyzer()

    for repo in repos:
        full_name = repo.get("name", "")
        try:
            text = _fetch_readme_text(full_name, github_token, max_text_chars)
        except requests.RequestException as exc:
            logger.warning(
                "Failed to fetch README for %s: %s", full_name or "<unknown>", exc
            )
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
                "technologies": _flatten_unique(
                    analysis.get("technologies_detected")
                ),
                "analyzed_chars": len(text),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 — never crash the batch
            logger.warning(
                "PolicyAnalyzer failed for %s: %s", full_name or "<unknown>", exc
            )
            repo["policy"] = _empty_policy(error=str(exc))

    return repos
