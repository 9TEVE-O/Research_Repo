"""Daily research agent — CLI entrypoint.

Thin wrapper around :func:`pipeline.run`, which loads configuration from
environment variables and executes the full pipeline (fetch, score, annotate,
select, build knowledge graph, persist, report, email, gist).

Environment variables required:
    GITHUB_TOKEN        - GitHub personal access token (search scope)
    OPENAI_API_KEY      - OpenAI API key
    SMTP_SERVER         - SMTP hostname
    SMTP_PORT           - SMTP port (default 587)
    SMTP_USER           - Sender email / SMTP login
    SMTP_PASSWORD       - Sender SMTP password
    REPORT_RECIPIENT    - Email address to send the report to

Optional environment variables:
    GIST_ID             - ID of the Gist to update; if unset, Gist upload is
                           skipped
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
