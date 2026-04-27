"""Orchestrates the full daily research report pipeline."""

import logging
from datetime import date

import openai
import requests

from config import Config, load_config, missing_required_vars
from github_client import fetch_candidates
from knowledge_graph import GraphRetriever, extract_graph_from_repos
from report import build_markdown_report
from scoring import score_all
from selector import select_top_k
from storage import save_repos
from email_sender import send_report_via_email
from gist_uploader import upload_to_gist

logger = logging.getLogger(__name__)


def run(cfg: Config | None = None) -> None:
    """Run the full daily research report pipeline.

    Args:
        cfg: Pre-built :class:`~config.Config`.  When *None* the config is
             loaded from environment variables via :func:`~config.load_config`.
    """
    loaded_from_env = cfg is None
    if cfg is None:
        cfg = load_config()

    if not cfg.is_valid():
        if loaded_from_env:
            logger.error(
                "Missing required environment variable(s): %s",
                ", ".join(missing_required_vars()),
            )
        else:
            logger.error("Invalid configuration provided to run().")
        return

    today = date.today().isoformat()
    logger.info("Starting daily research agent for %s.", today)

    openai_client = openai.OpenAI(api_key=cfg.openai_api_key)

    # ── 1. Fetch candidate repositories ───────────────────────────────────────────
    try:
        raw_candidates = fetch_candidates(
            cfg.github_token,
            query=cfg.search_query,
            per_page=cfg.search_per_page,
        )
    except requests.RequestException as exc:
        logger.error("GitHub search request failed: %s", exc)
        return

    if not raw_candidates:
        logger.warning("No candidates returned from GitHub search. Exiting.")
        return

    # ── 2. Score each candidate with the LLM ─────────────────────────────────────
    scored = score_all(raw_candidates, openai_client, model=cfg.llm_model)

    # ── 3. Select top-k using the configured relevance threshold ─────────────────
    top_repos = select_top_k(
        scored,
        k=cfg.top_k,
        threshold=cfg.score_threshold,
    )

    if not top_repos:
        logger.warning("No repositories passed the relevance threshold. Exiting.")
        return

    # ── 4. Build knowledge graph from selected repositories ─────────────────────
    kg = extract_graph_from_repos(top_repos)
    retriever = GraphRetriever(kg)
    logger.info(
        "Knowledge graph built. %s",
        retriever.summarize().replace("\n", " | "),
    )

    # ── 5. Persist results ───────────────────────────────────────────────────────
    save_repos(top_repos, report_date=today)

    # ── 6. Build Markdown report ───────────────────────────────────────────────────
    report_markdown = build_markdown_report(top_repos, today)
    logger.info("Markdown report built (%d chars).", len(report_markdown))

    # ── 7. Send email ─────────────────────────────────────────────────────────────
    try:
        send_report_via_email(report_markdown, cfg.report_recipient)
    except Exception as exc:  # noqa: BLE001
        logger.error("Email delivery failed: %s", exc)

    # ── 8. Update Gist ───────────────────────────────────────────────────────────
    if cfg.gist_id:
        try:
            gist_url = upload_to_gist(report_markdown, cfg.gist_id, cfg.github_token)
            logger.info("Gist updated: %s", gist_url)
        except Exception as exc:  # noqa: BLE001
            logger.error("Gist upload failed: %s", exc)
    else:
        logger.warning("GIST_ID not set; skipping Gist upload.")

    logger.info("Daily research agent completed for %s.", today)
