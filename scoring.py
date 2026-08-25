"""Deterministic pre-filtering and LLM-based scoring of repositories."""

import json
import logging
import re

import openai

from models import ScoredRepo

logger = logging.getLogger(__name__)

LLM_SYSTEM_PROMPT = (
    "You are a research assistant.  Given a GitHub repository's name, "
    "description and topics, respond with:\n"
    "1. relevance_score: integer 0–100 for AI/LLM research relevance.\n"
    "2. summary: one-paragraph summary (2–4 sentences).\n"
    "3. reason: one sentence explaining the score.\n\n"
    "You MUST reply ONLY with a valid JSON object and no other text:\n"
    '{"relevance_score": <int>, "summary": "<str>", "reason": "<str>"}'
)

# Maximum character lengths for LLM-returned text fields.
_MAX_SUMMARY_LEN = 1000
_MAX_REASON_LEN = 500


def score_repository(
    repo: dict,
    openai_client: openai.OpenAI,
    model: str = "gpt-4o-mini",
) -> ScoredRepo | None:
    """Call the OpenAI API to score a single repository.

    Args:
        repo:          Raw repository dict from the GitHub Search API.
        openai_client: Authenticated OpenAI client instance.
        model:         Chat completion model to use.

    Returns:
        A :class:`ScoredRepo` on success, or ``None`` if the API call or
        JSON parsing fails.
    """
    description = repo.get("description") or "N/A"
    topics = repo.get("topics")
    if not isinstance(topics, list):
        topics = []

    user_message = (
        f"Repository: {repo.get('full_name', '')}\n"
        f"Description: {description}\n"
        f"Topics: {', '.join(topics)}\n"
        f"Stars: {repo.get('stargazers_count', 0)}"
    )

    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present. response_format already
        # constrains the API to emit a bare JSON object, but this keeps the
        # parser tolerant of mocked/older responses that still fence it.
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)

        # Validate types and ranges on all returned fields so that a
        # prompt-injection payload cannot smuggle out-of-range scores or
        # non-string content into the rest of the pipeline. Reject bool
        # (a JSON true/false is technically an int subclass in Python) and
        # non-integral floats explicitly rather than silently truncating
        # them with int().
        raw_score = data["relevance_score"]
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            raise TypeError(
                f"relevance_score must be an integer, got {type(raw_score).__name__}"
            )
        if isinstance(raw_score, float) and not raw_score.is_integer():
            raise ValueError(f"relevance_score {raw_score} is not an integer")
        score = int(raw_score)
        if not 0 <= score <= 100:
            raise ValueError("relevance_score must be between 0 and 100")

        summary = str(data["summary"])[:_MAX_SUMMARY_LEN]
        reason = str(data["reason"])[:_MAX_REASON_LEN]

        return ScoredRepo(
            name=repo.get("full_name", ""),
            url=repo.get("html_url", ""),
            relevance_score=score,
            summary=summary,
            reason=reason,
        )
    except (
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        openai.OpenAIError,
    ) as exc:
        logger.warning(
            "Failed to score repository '%s': %s",
            repo.get("full_name", "unknown"),
            exc,
        )
        return None


def score_all(
    candidates: list[dict],
    openai_client: openai.OpenAI,
    model: str = "gpt-4o-mini",
) -> list[ScoredRepo]:
    """Score every candidate in *candidates*, skipping failures.

    Args:
        candidates:    List of raw repository dicts.
        openai_client: Authenticated OpenAI client instance.
        model:         Chat completion model to use.

    Returns:
        List of successfully scored :class:`ScoredRepo` objects.
    """
    scored = []
    for repo in candidates:
        result = score_repository(repo, openai_client, model=model)
        if result is not None:
            scored.append(result)

    logger.info(
        "Successfully scored %d / %d candidates.", len(scored), len(candidates)
    )
    return scored
