"""Daily research agent — thin CLI entry point.

Fetches candidate GitHub repositories, scores them with an LLM, selects the
top results, persists them to SQLite, builds a Markdown report, sends it by
email, and uploads it to a GitHub Gist.

Environment variables required:
    GITHUB_TOKEN     – GitHub personal access token (search + gist scopes)
    OPENAI_API_KEY   – OpenAI API key
    SMTP_SERVER      – SMTP hostname
    SMTP_PORT        – SMTP port (default 587)
    SMTP_USER        – Sender email / SMTP login
    SMTP_PASSWORD    – Sender SMTP password
    REPORT_RECIPIENT – Email address to send the report to

Optional environment variables:
    GIST_ID          – ID of the Gist to update; if unset, Gist upload is skipped
    SEARCH_QUERY     – GitHub search query (default: "topic:llm topic:research stars:>50")
    SEARCH_PER_PAGE  – Results per search page (default: 20)
    TOP_K            – Number of top repos to select (default: 3)
    LLM_MODEL        – OpenAI model name (default: "gpt-4o-mini")
"""

import logging

from pipeline import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    run()

