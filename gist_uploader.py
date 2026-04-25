"""Upload or update the daily research report as a GitHub Gist."""

import logging
from datetime import date

from github import Github, GithubException, UnknownObjectException

logger = logging.getLogger(__name__)


def upload_to_gist(
    report_markdown: str,
    gist_id: str,
    github_token: str,
) -> str:
    """Update an existing Gist with the report.

    The file inside the Gist is named ``daily-report-YYYY-MM-DD.md`` using
    today's date.

    Args:
        report_markdown: Markdown content of the report.
        gist_id:         ID of an existing Gist to update.
        github_token:    Personal access token with ``gist`` scope.

    Returns:
        The HTML URL of the Gist.

    Raises:
        UnknownObjectException: If the Gist ID is not found.
        GithubException: For unexpected GitHub API errors.
    """
    filename = f"daily-report-{date.today().isoformat()}.md"
    file_payload = {filename: {"content": report_markdown}}

    g = Github(github_token)

    try:
        gist = g.get_gist(gist_id)
        gist.edit(files=file_payload)
        logger.info("Updated existing Gist %s → %s", gist_id, gist.html_url)
    except UnknownObjectException:
        # Do not fall back to creating a new public Gist: an operational
        # error (wrong ID, deleted Gist, insufficient token scope) must not
        # silently become a public disclosure event.  Raise so the caller
        # can surface the failure explicitly.
        logger.error(
            "Gist '%s' not found. Verify GIST_ID and token scopes. "
            "No fallback Gist will be created.",
            gist_id,
        )
        raise
    except GithubException as exc:
        logger.error("GitHub API error while uploading Gist: %s", exc)
        raise

    return gist.html_url
