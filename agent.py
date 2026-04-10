"""Daily research agent.

Fetches candidate GitHub repositories, scores them with an LLM, selects the
top 3, builds a Markdown report, sends it by email, and uploads it to a Gist.

Environment variables required:
    GITHUB_TOKEN        – GitHub personal access token (search scope only)
    GITHUB_GIST_TOKEN   – GitHub personal access token (gist scope only);
                          falls back to GITHUB_TOKEN if not set
    OPENAI_API_KEY      – OpenAI API key
    SMTP_SERVER         – SMTP hostname
    SMTP_PORT           – SMTP port (default 587)
    SMTP_USER           – Sender email / SMTP login
    SMTP_PASSWORD       – Sender SMTP password
    REPORT_RECIPIENT    – Email address to send the report to

Optional environment variables:
    GIST_ID             – ID of the Gist to update; if unset, Gist upload is
                          skipped
"""

import logging
import os
from datetime import date

import openai
import requests

from email_sender import send_report_via_email
from gist_uploader import upload_to_gist
from report import build_markdown_report
from selector import select_top_k

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
SEARCH_QUERY = "topic:llm topic:research stars:>50"
SEARCH_PER_PAGE = 20

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


# ── Step helpers ─────────────────────────────────────────────────────────────


def fetch_candidates(github_token: str) -> list:
    """Search GitHub for candidate repositories and return raw repo dicts."""
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"q": SEARCH_QUERY, "sort": "stars", "per_page": SEARCH_PER_PAGE}

    response = requests.get(
        GITHUB_SEARCH_URL, headers=headers, params=params, timeout=15
    )
    response.raise_for_status()

    items = response.json().get("items", [])
    logger.info("Fetched %d candidate repositories from GitHub.", len(items))
    return items


def score_repository(repo: dict, openai_client: openai.OpenAI) -> dict | None:
    """Call the OpenAI API to score a single repository.

    Returns a dict with keys: name, url, relevance_score, summary, reason,
    or None if the API call or JSON parsing fails.
    """
    import json

    user_message = (
        f"Repository: {repo.get('full_name', '')}\n"
        f"Description: {repo.get('description', 'N/A')}\n"
        f"Topics: {', '.join(repo.get('topics', []))}\n"
        f"Stars: {repo.get('stargazers_count', 0)}"
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()

        data = json.loads(raw)

        # Validate types and ranges on all returned fields so that a
        # prompt-injection payload cannot smuggle out-of-range scores or
        # non-string content into the rest of the pipeline.
        score = int(data["relevance_score"])
        if not (0 <= score <= 100):
            raise ValueError(f"relevance_score {score} outside allowed range 0–100")

        summary = str(data["summary"])[:_MAX_SUMMARY_LEN]
        reason = str(data["reason"])[:_MAX_REASON_LEN]

        return {
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "relevance_score": score,
            "summary": summary,
            "reason": reason,
        }
    except (json.JSONDecodeError, KeyError, ValueError, openai.OpenAIError) as exc:
        logger.warning(
            "Failed to score repository '%s': %s",
            repo.get("full_name", "unknown"),
            exc,
        )
        return None


# ── Main entry point ─────────────────────────────────────────────────────────


def run() -> None:
    """Run the full daily research report pipeline."""
    today = date.today().isoformat()
    logger.info("Starting daily research agent for %s.", today)

    # ── 1. Read configuration from environment ───────────────────────────────
    github_token = os.environ.get("GITHUB_TOKEN", "")
    # Use a separate token for Gist operations (gist scope) so that the
    # search token (public_repo scope) is not over-privileged.  Fall back
    # to GITHUB_TOKEN only when GITHUB_GIST_TOKEN is not configured.
    gist_token = os.environ.get("GITHUB_GIST_TOKEN") or github_token
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    recipient = os.environ.get("REPORT_RECIPIENT", "")
    gist_id = os.environ.get("GIST_ID", "")

    required_vars = ["GITHUB_TOKEN", "OPENAI_API_KEY", "REPORT_RECIPIENT"]
    missing_vars = [name for name in required_vars if not os.environ.get(name)]
    if missing_vars:
        logger.error(
            "Missing required environment variable(s): %s",
            ", ".join(missing_vars),
        )
        return

    openai_client = openai.OpenAI(api_key=openai_api_key)

    # ── 2. Fetch candidate repositories ─────────────────────────────────────
    try:
        raw_candidates = fetch_candidates(github_token)
    except requests.RequestException as exc:
        logger.error("GitHub search request failed: %s", exc)
        return

    if not raw_candidates:
        logger.warning("No candidates returned from GitHub search. Exiting.")
        return

    # ── 3. Score each candidate with the LLM ─────────────────────────────────
    scored = []
    for repo in raw_candidates:
        result = score_repository(repo, openai_client)
        if result is not None:
            scored.append(result)

    logger.info("Successfully scored %d / %d candidates.", len(scored), len(raw_candidates))

    # ── 4. Select top 3 ──────────────────────────────────────────────────────
    top_repos = select_top_k(scored, k=3)

    if not top_repos:
        logger.warning("No repositories passed the relevance threshold. Exiting.")
        return

    # ── 5. Build Markdown report ─────────────────────────────────────────────
    report_markdown = build_markdown_report(top_repos, today)
    logger.info("Markdown report built (%d chars).", len(report_markdown))

    # ── 6. Send email ─────────────────────────────────────────────────────────
    try:
        send_report_via_email(report_markdown, recipient)
    except Exception as exc:
        logger.error("Email delivery failed: %s", exc)
        raise

    # ── 7. Update Gist ────────────────────────────────────────────────────────
    if gist_id:
        try:
            gist_url = upload_to_gist(report_markdown, gist_id, gist_token)
            logger.info("Gist updated: %s", gist_url)
        except Exception as exc:
            logger.error("Gist upload failed: %s", exc)
            raise
    else:
        logger.warning("GIST_ID not set; skipping Gist upload.")

    logger.info("Daily research agent completed for %s.", today)


if __name__ == "__main__":
    run()
