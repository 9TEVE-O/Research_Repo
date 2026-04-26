"""Select the top-k repository candidates by relevance score."""

import logging

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 50
_SCORE_MIN = 0
_SCORE_MAX = 100


def _get_score(c) -> int:
    """Extract relevance_score from a ScoredRepo dataclass or a plain dict."""
    if hasattr(c, "relevance_score"):
        return c.relevance_score
    return c.get("relevance_score", 0)


def _get_name(c) -> str:
    if hasattr(c, "name"):
        return c.name
    if hasattr(c, "get"):
        return c.get("name", "unknown")
    return "unknown"


def select_top_k(
    candidates: list,
    k: int = 3,
    threshold: int = SCORE_THRESHOLD,
) -> list:
    """Return up to k candidates sorted by relevance_score descending.

    Rules:
    - Candidates with scores outside the valid range 0–100 are discarded.
    - Candidates with score <= threshold are excluded.
    - If the number of qualifying candidates is less than k, return all
      that meet the threshold and emit a warning.
    - If no candidates meet the threshold, return an empty list and log
      a message.

    Args:
        candidates: List of dicts or ScoredRepo objects each with a
                    ``relevance_score`` field.
        k:          Maximum number of results to return (default 3).
        threshold:  Minimum score required (exclusive, default 50).

    Returns:
        A list of up to k candidate objects sorted by score descending.
    """
    valid = []
    for c in candidates:
        score = _get_score(c)
        if not (_SCORE_MIN <= score <= _SCORE_MAX):
            logger.warning(
                "Discarding candidate '%s': relevance_score %s is outside "
                "the valid range %d–%d.",
                _get_name(c),
                score,
                _SCORE_MIN,
                _SCORE_MAX,
            )
            continue
        valid.append(c)

    qualified = [c for c in valid if _get_score(c) > threshold]
    qualified.sort(key=_get_score, reverse=True)

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
