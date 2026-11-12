"""Orchestrates the full daily research report pipeline."""

import logging
from datetime import date
from pathlib import Path

import openai
import requests

from config import Config, load_config, missing_required_vars
from github_client import fetch_candidates
from knowledge_graph import GraphRetriever, extract_graph_from_repos
from models import ScoredRepo
from report import build_markdown_report
from scoring import score_all, score_metadata
from selector import select_top_k
from storage import save_repos
from email_sender import send_report_via_email
from gist_uploader import upload_to_gist

logger = logging.getLogger(__name__)

# Location (relative to the working directory) where the generated Markdown
# report is persisted.  The scheduled workflow publishes this file to a Gist
# and treats its absence as a failed run, so the pipeline must write it on the
# success path.
REPORT_PATH = Path("reports/latest.md")


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

    # ── 1. Fetch candidate repositories ──────────────────────────────────────────────
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

    # ── 2. Score with OpenAI when configured, otherwise public GitHub metadata.
    # Do not silently downgrade a configured but failing paid API.
    if cfg.openai_api_key:
        openai_client = openai.OpenAI(api_key=cfg.openai_api_key)
        scored = score_all(raw_candidates, openai_client, model=cfg.llm_model)
        scoring_method = f"OpenAI LLM ({cfg.llm_model})"
    else:
        logger.warning(
            "OPENAI_API_KEY is absent: using deterministic metadata scoring, "
            "not an AI evaluation."
        )
        scored = score_metadata(raw_candidates)
        scoring_method = "GitHub metadata-only heuristic (no AI evaluation)"

    # ── 2b. Annotate with policy / terms analysis (best-effort) ──────────────────────────
    # Import lazily so that a missing submodule does not prevent pipeline
    # import or config validation — policy analysis is entirely optional.
    # Catch Exception broadly: any failure in this optional step (missing
    # submodule, network error, malformed data during re-hydration, etc.)
    # must log and continue rather than crash the pipeline.
    try:
        from policy_analysis import annotate_with_policy  # noqa: PLC0415
        scored_dicts = annotate_with_policy(
            [r.to_dict() for r in scored], cfg.github_token
        )
        scored = [ScoredRepo.from_dict(d) for d in scored_dicts]
        logger.info("Annotated %d repositories with policy analysis.", len(scored))
    except Exception as exc:  # noqa: BLE001 — best-effort, must not crash pipeline
        logger.warning(
            "Policy analysis failed (%s: %s) — skipping.",
            type(exc).__name__,
            exc,
        )

    # ── 3. Select top-k using the configured relevance threshold ─────────────────────────
    top_repos = select_top_k(
        scored,
        k=cfg.top_k,
        threshold=cfg.score_threshold,
    )

    if not top_repos:
        logger.warning("No repositories passed the relevance threshold. Exiting.")
        return

    # ── 4. Build knowledge graph from selected repositories ──────────────────────────────
    kg = extract_graph_from_repos(top_repos)
    retriever = GraphRetriever(kg)
    logger.info(
        "Knowledge graph built. %s",
        retriever.summarize().replace("\n", " | "),
    )

    # ── 5. Persist results ──────────────────────────────────────────────────────────────────
    save_repos(top_repos, report_date=today)

    # ── 6. Build Markdown report ────────────────────────────────────────────────────────────
    report_markdown = build_markdown_report(
        top_repos, today, scoring_method=scoring_method
    )
    logger.info("Markdown report built (%d chars).", len(report_markdown))

    # ── 6b. Persist the report to reports/latest.md ──────────────────────────────────────
    # Write the report to disk before delivery.  The scheduled workflow
    # publishes this file to a Gist and fails the run when it is missing, so a
    # write error must propagate rather than letting the run report success
    # with no persisted report.
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_markdown, encoding="utf-8")
    logger.info("Report written to %s.", REPORT_PATH)

    # ── 7. Send email only if explicitly configured. In Actions, the report
    # is always retained as a downloadable workflow artifact.
    if cfg.report_recipient:
        try:
            send_report_via_email(report_markdown, cfg.report_recipient)
        except Exception as exc:  # noqa: BLE001
            logger.error("Email delivery failed: %s", exc)
            raise
    else:
        logger.info("Email is not configured; report retained on disk.")

    # ── 8. Update Gist ───────────────────────────────────────────────────────────────────
    if cfg.gist_id:
        try:
            gist_url = upload_to_gist(report_markdown, cfg.gist_id, cfg.gist_token)
            logger.info("Gist updated: %s", gist_url)
        except Exception as exc:  # noqa: BLE001
            logger.error("Gist upload failed: %s", exc)
            raise
    else:
        logger.warning("GIST_ID not set; skipping Gist upload.")

    logger.info("Daily research agent completed for %s.", today)
