"""Select the top-k repository candidates by relevance score."""

import logging
from typing import List

from models import ScoredRepo

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 50
_SCORE_MIN = 0
_SCORE_MAX = 100


def dict_to_scored_repo(repo_dict: dict) -> ScoredRepo:
    """Convert a repository dict to a ScoredRepo object."""
    return ScoredRepo(
        name=repo_dict.get("name", ""),
        url=repo_dict.get("url", ""),
        relevance_score=repo_dict.get("relevance_score", 0),
        summary=repo_dict.get("summary", ""),
        reason=repo_dict.get("reason", ""),
        policy=repo_dict.get("policy"),
    )


def select_top_k(
    candidates: List,
    k: int = 3,
    threshold: int = SCORE_THRESHOLD,
) -> List[ScoredRepo]:
    """Return up to k candidates sorted by relevance_score descending.

    Rules:
    - Candidates with scores outside the valid range 0-100 are discarded.
    - Candidates with score <= threshold are excluded.
    - If the number of qualifying candidates is less than k, return all
      that meet the threshold and emit a warning.
    - If no candidates meet the threshold, return an empty list and log
      a message.

    Args:
        candidates: List of scored repo dicts or ScoredRepo objects, each
                   containing a ``relevance_score`` attribute/key.
        k:          Maximum number of results to return (default 3).
        threshold:  Minimum relevance score to qualify (default 50).

    Returns:
        A list of up to k ScoredRepo objects sorted by score descending.
    """
    # Convert dicts to ScoredRepo objects if needed
    scored_repos = []
    for c in candidates:
        if isinstance(c, dict):
            scored_repos.append(dict_to_scored_repo(c))
        else:
            scored_repos.append(c)

    valid = []
    for c in scored_repos:
        score = c.relevance_score
        if not (_SCORE_MIN <= score <= _SCORE_MAX):
            logger.warning(
                "Discarding candidate '%s': relevance_score %s is outside "
                "the valid range %d–%d.",
                c.name,
                score,
                _SCORE_MIN,
                _SCORE_MAX,
            )
            continue
        valid.append(c)

    qualified = [c for c in valid if c.relevance_score > threshold]
    qualified.sort(key=lambda c: c.relevance_score, reverse=True)

    if not qualified:
        logger.warning(
            "No candidates met the minimum relevance threshold of %d. "
            "Returning empty list.",
            threshold,
        )
        return []

    if len(qualified) < k:
        logger.warning(
            "Only %d candidate(s) met the relevance threshold of %d "
            "(requested k=%d). Returning all qualifying candidates.",
            len(qualified),
            threshold,
            k,
        )
        return qualified

    return qualified[:k]
