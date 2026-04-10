"""Select the top-k repository candidates by relevance score."""

import logging

logger = logging.getLogger(__name__)

SCORE_THRESHOLD = 50
_SCORE_MIN = 0
_SCORE_MAX = 100


def select_top_k(candidates: list, k: int = 3) -> list:
    """Return up to k candidates sorted by relevance_score descending.

    Rules:
    - Candidates with scores outside the valid range 0–100 are discarded.
    - Candidates with score <= 50 are excluded.
    - If the number of qualifying candidates is less than k, return all
      that meet the threshold and emit a warning.
    - If no candidates meet the threshold, return an empty list and log
      a message.

    Args:
        candidates: List of dicts each containing a ``relevance_score`` key.
        k:          Maximum number of results to return (default 3).

    Returns:
        A list of up to k candidate dicts sorted by score descending.
    """
    valid = []
    for c in candidates:
        score = c.get("relevance_score", 0)
        if not (_SCORE_MIN <= score <= _SCORE_MAX):
            logger.warning(
                "Discarding candidate '%s': relevance_score %s is outside "
                "the valid range %d–%d.",
                c.get("name", "unknown"),
                score,
                _SCORE_MIN,
                _SCORE_MAX,
            )
            continue
        valid.append(c)

    qualified = [c for c in valid if c.get("relevance_score", 0) > SCORE_THRESHOLD]
    qualified.sort(key=lambda c: c["relevance_score"], reverse=True)

    if not qualified:
        logger.warning(
            "No candidates met the minimum relevance threshold of %d. "
            "Returning empty list.",
            SCORE_THRESHOLD,
        )
        return []

    if len(qualified) < k:
        logger.warning(
            "Only %d candidate(s) met the relevance threshold of %d "
            "(requested k=%d). Returning all qualifying candidates.",
            len(qualified),
            SCORE_THRESHOLD,
            k,
        )
        return qualified

    return qualified[:k]
