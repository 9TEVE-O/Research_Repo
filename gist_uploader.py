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
    """Update an existing Gist with the report, or create a new one.

    The file inside the Gist is named ``daily-report-YYYY-MM-DD.md`` using
    today's date.

    Args:
        report_markdown: Markdown content of the report.
        gist_id:         ID of an existing Gist to update.  If the Gist
                         cannot be found a new public Gist is created.
        github_token:    Personal access token with ``gist`` scope.

    Returns:
        The HTML URL of the Gist.

    Raises:
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
        logger.warning(
            "Gist '%s' not found. Creating a new Gist instead.", gist_id
        )
        gist = g.get_user().create_gist(
            public=True,
            files=file_payload,
            description="Daily Research Report",
        )
        logger.info("Created new Gist → %s", gist.html_url)
    except GithubException as exc:
        logger.error("GitHub API error while uploading Gist: %s", exc)
        raise

    return gist.html_url
