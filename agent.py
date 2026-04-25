<<<<<<< HEAD
"""
Research Agent
==============
Daily pipeline:
  1. Search GitHub for new / recently-updated AI-agent repos.
  2. Deduplicate against previously-seen repos (semantic + hash).
  3. Score each candidate with an LLM (0-100).
  4. Select the top-3 highest-scoring repos.
  5. Build a Markdown report and write it to reports/latest.md.
  6. Send the report by email.

Required environment variables
-------------------------------
  GITHUB_TOKEN    – GitHub personal access token (classic PAT: `public_repo` for public repos or `repo` for private repos; fine-grained token: read access to repository contents/metadata)
  OPENAI_API_KEY  – OpenAI API key
  SMTP_PASSWORD   – Password for the outbound SMTP account
  SMTP_HOST       – SMTP server hostname  (default: smtp.gmail.com)
  SMTP_PORT       – SMTP server port      (default: 587)
  SMTP_USER       – SMTP sender address
  EMAIL_TO        – Recipient address for the daily report
"""

from __future__ import annotations

import json
import math
import os
import smtplib
import traceback
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import openai
from github import Github

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
SMTP_HOST: str = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
_smtp_port: str = os.environ.get("SMTP_PORT", "587")
SMTP_PORT: int = int(_smtp_port) if _smtp_port.isdigit() else 587
SMTP_USER: str = os.environ.get("SMTP_USER", "")
EMAIL_TO: str = os.environ.get("EMAIL_TO", "")

STATE_PATH = Path("state/seen_repos.json")
REPORT_PATH = Path("reports/latest.md")
TOP_N = 3
SIMILARITY_THRESHOLD = 0.9  # cosine-similarity threshold for semantic dedup

# GitHub search queries that define the research profile.
SEARCH_QUERIES: list[str] = [
    "autonomous AI agent topic:llm pushed:>2024-01-01",
    "LLM agent framework topic:ai-agent pushed:>2024-01-01",
    "multi-agent AI orchestration pushed:>2024-01-01",
    "self-improving AI agent reinforcement pushed:>2024-01-01",
    "agentic AI workflow automation pushed:>2024-01-01",
]

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


def load_state() -> dict[str, Any]:
    """Load persistent state (seen repo hashes and embeddings)."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {"seen_hashes": [], "seen_embeddings": [], "keyword_boosts": {}}


def _round_embedding_value(value: Any, precision: int = 4) -> Any:
    """Reduce persisted embedding precision to keep state compact."""
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, list):
        return [_round_embedding_value(item, precision) for item in value]
    if isinstance(value, dict):
        return {
            key: _round_embedding_value(item, precision) for key, item in value.items()
        }
    return value


def _state_for_persistence(state: dict[str, Any]) -> dict[str, Any]:
    """Return a compact copy of state suitable for JSON persistence."""
    persisted_state = dict(state)
    if "seen_embeddings" in persisted_state:
        persisted_state["seen_embeddings"] = _round_embedding_value(
            persisted_state["seen_embeddings"]
        )
    return persisted_state


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    persisted_state = _state_for_persistence(state)
    STATE_PATH.write_text(json.dumps(persisted_state, separators=(",", ":")))


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------


def search_repos(gh: Github, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a list of candidate repo dicts not yet seen."""
    seen_hashes: set[str] = set(state.get("seen_hashes", []))
    candidates: list[dict[str, Any]] = []

    for query in SEARCH_QUERIES:
        try:
            results = gh.search_repositories(query=query, sort="updated", order="desc")
            for repo in results[:20]:  # cap per-query to avoid rate-limit burn
                commit_hash = _latest_commit_hash(repo)
                dedup_key = f"{repo.full_name}@{commit_hash}"
                if dedup_key in seen_hashes:
                    continue
                readme = _safe_readme(repo)
                candidates.append(
                    {
                        "full_name": repo.full_name,
                        "html_url": repo.html_url,
                        "description": repo.description or "",
                        "stars": repo.stargazers_count,
                        "commit_hash": commit_hash,
                        "dedup_key": dedup_key,
                        "readme": readme,
                    }
                )
        except Exception:
            traceback.print_exc()

    return candidates


def _stable_repo_marker(repo: Any) -> str:
    repo_id = getattr(repo, "id", None)
    repo_name = getattr(repo, "full_name", None) or getattr(repo, "name", None) or "unknown-repo"
    repo_marker = f"repo-{repo_id}" if repo_id is not None else repo_name

    activity_at = getattr(repo, "pushed_at", None) or getattr(repo, "updated_at", None)
    if isinstance(activity_at, datetime):
        activity_marker = activity_at.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")
    elif activity_at is None:
        activity_marker = None
    else:
        activity_marker = str(activity_at)

    if activity_marker is not None:
        return f"{repo_marker}-{activity_marker}"

    return repo_marker


def _latest_commit_hash(repo: Any) -> str:
    stable_marker = _stable_repo_marker(repo)
    if stable_marker.endswith("-None"):
        stable_marker = stable_marker[:-5]

    activity_at = getattr(repo, "pushed_at", None) or getattr(repo, "updated_at", None)
    if activity_at is not None:
        return stable_marker

    try:
        commits = repo.get_commits()
        return commits[0].sha[:12]
    except Exception:  # noqa: BLE001
        return stable_marker


def _safe_readme(repo: Any) -> str:
    try:
        return repo.get_readme().decoded_content.decode("utf-8", errors="ignore")[:3000]
    except Exception:  # noqa: BLE001
        return ""


# ---------------------------------------------------------------------------
# Semantic deduplication
# ---------------------------------------------------------------------------


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding(client: openai.OpenAI, text: str) -> list[float]:
    # text-embedding-3-small supports up to 8191 tokens; 8000 characters is a
    # conservative character-level approximation that stays safely under that limit.
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return response.data[0].embedding


def is_semantically_duplicate(
    embedding: list[float],
    seen_embeddings: list[list[float]],
) -> bool:
    for seen in seen_embeddings:
        if _cosine_similarity(embedding, seen) > SIMILARITY_THRESHOLD:
            return True
    return False


def deduplicate_semantically(
    candidates: list[dict[str, Any]],
    client: openai.OpenAI,
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Remove candidates whose semantic content is too similar to already-seen repos."""
    seen_embeddings: list[list[float]] = state.get("seen_embeddings", [])
    unique: list[dict[str, Any]] = []
    for candidate in candidates:
        text = f"{candidate['full_name']} {candidate['description']} {candidate['readme']}"
        try:
            emb = get_embedding(client, text)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            unique.append(candidate)
            continue
        if is_semantically_duplicate(emb, seen_embeddings):
            continue
        candidate["embedding"] = emb
        unique.append(candidate)
    return unique


# ---------------------------------------------------------------------------
# LLM scoring
# ---------------------------------------------------------------------------

SCORE_PROMPT_TEMPLATE = """You are a research filter. Given a repository's README and recent commits, rate its relevance to building autonomous AI agents.

Return a JSON object:
{{
  "summary": "one paragraph",
  "relevance_score": integer 0-100,
  "reason": "why this score"
}}

Repo: {name}
Content: {text}"""


def score_repo(client: openai.OpenAI, candidate: dict[str, Any]) -> dict[str, Any]:
    """Ask the LLM to score a candidate repo. Returns the candidate with added score fields."""
    text = f"{candidate['description']}\n\n{candidate['readme']}"
    prompt = SCORE_PROMPT_TEMPLATE.format(name=candidate["full_name"], text=text[:4000])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content)
        candidate["summary"] = data.get("summary", "")
        candidate["relevance_score"] = int(data.get("relevance_score", 0))
        candidate["reason"] = data.get("reason", "")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        candidate.setdefault("summary", "")
        candidate.setdefault("relevance_score", 0)
        candidate.setdefault("reason", "")
    return candidate


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------


def build_report(top_repos: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        f"# Daily Research Report – {now}",
        "",
        f"Top {len(top_repos)} repositories selected from today's scan.",
        "",
    ]
    for i, repo in enumerate(top_repos, 1):
        lines += [
            f"## {i}. [{repo['full_name']}]({repo['html_url']})",
            f"**Stars:** {repo['stars']}  |  **Relevance score:** {repo['relevance_score']}/100",
            "",
            f"**Summary:** {repo['summary']}",
            "",
            f"**Why selected:** {repo['reason']}",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def write_report(content: str) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(content)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------


def send_email(subject: str, body: str) -> None:
    if not SMTP_USER or not EMAIL_TO or not SMTP_PASSWORD:
        print("Email not configured – skipping.")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
        print("Email sent successfully.")
    except Exception:  # noqa: BLE001
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def main() -> None:
    print("=== Research Agent starting ===")

    # Load persistent state
    state = load_state()

    # Initialise API clients
    gh = Github(GITHUB_TOKEN)
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # 1. Search GitHub for candidate repos
    print("Searching GitHub…")
    candidates = search_repos(gh, state)
    print(f"  Found {len(candidates)} new candidates (hash-deduplicated).")

    if not candidates:
        print("No new candidates found. Exiting.")
        write_report("# Daily Research Report\n\nNo new repositories found today.\n")
        return

    # 2. Semantic deduplication
    print("Running semantic deduplication…")
    candidates = deduplicate_semantically(candidates, client, state)
    print(f"  {len(candidates)} candidates after semantic deduplication.")

    if not candidates:
        print("All candidates were semantically duplicate. Exiting.")
        write_report("# Daily Research Report\n\nAll found repositories were similar to previously-reported ones.\n")
        return

    # 3. Score each candidate
    print("Scoring candidates with LLM…")
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        scored.append(score_repo(client, candidate))
        print(f"  {candidate['full_name']} → {candidate.get('relevance_score', 0)}")

    # 4. Select top-3
    scored.sort(key=lambda r: r["relevance_score"], reverse=True)
    top_repos = scored[:TOP_N]
    print(f"Top {TOP_N} repos selected.")

    # 5. Build and write report
    report_text = build_report(top_repos)
    write_report(report_text)
    print(f"Report written to {REPORT_PATH}.")

    # 6. Send email
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    send_email(
        subject=f"[Research Agent] Daily Top-{len(top_repos)} AI Repos – {today}",
        body=report_text,
    )

    # 7. Update persistent state – only record repos that were actually reported
    #    so that scored-but-not-selected repos remain eligible for future runs.
    seen_hashes: list[str] = state.get("seen_hashes", [])
    seen_embeddings: list[list[float]] = state.get("seen_embeddings", [])

    for repo in top_repos:
        seen_hashes.append(repo["dedup_key"])
        if "embedding" in repo:
            seen_embeddings.append(repo["embedding"])

    # Keep the state file from growing without bound
    state["seen_hashes"] = seen_hashes[-5000:]
    state["seen_embeddings"] = seen_embeddings[-500:]

    save_state(state)
    print("State saved. Done.")


if __name__ == "__main__":
    main()
=======
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
from policy_analysis import annotate_with_policy
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

    # ── 3b. Annotate scored repos with policy/terms analysis ────────────────
    scored = annotate_with_policy(scored, github_token)
    logger.info("Annotated %d repositories with policy analysis.", len(scored))

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
>>>>>>> main
