"""Daily research agent — CLI entrypoint.

Thin wrapper around :func:`pipeline.run`, which loads configuration from
environment variables and executes the full pipeline (fetch, score, annotate,
select, build knowledge graph, persist, report, email, gist).

Environment variables required:
    GITHUB_TOKEN        - GitHub token for repository search (Actions provides one)

Optional environment variables:
    OPENAI_API_KEY      - Enables OpenAI scoring; absent means labelled metadata-only mode
    SMTP_SERVER         - SMTP hostname (provide with all other email fields)
    SMTP_PORT           - SMTP port (default 587)
    SMTP_USER           - Sender email / SMTP login
    SMTP_PASSWORD       - Sender SMTP password
    REPORT_RECIPIENT    - Email recipient; requires all SMTP fields
    GIST_ID             - ID of the Gist to update; if unset, Gist upload is
                           skipped
    GITHUB_GIST_TOKEN   - GitHub personal access token (gist scope only);
                          falls back to GITHUB_TOKEN if not set
    SEARCH_QUERY, SEARCH_PER_PAGE, TOP_K, SCORE_THRESHOLD, LLM_MODEL
                         - see config.load_config() for defaults
"""

import logging

from pipeline import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    run()
