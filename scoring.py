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
    "Reply in this exact JSON format:\n"
    '{"relevance_score": <int>, "summary": "<str>", "reason": "<str>"}'
)


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
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        score = int(data["relevance_score"])
        if not 0 <= score <= 100:
            raise ValueError("relevance_score must be between 0 and 100")

        return ScoredRepo(
            name=repo.get("full_name", ""),
            url=repo.get("html_url", ""),
            relevance_score=score,
            summary=data["summary"],
            reason=data["reason"],
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
