"""Send the daily research report via email using smtplib."""

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown as md
import nh3

logger = logging.getLogger(__name__)

# HTML tags and attributes that are safe to preserve in the email body.
_ALLOWED_TAGS = {
    "a", "b", "blockquote", "br", "code", "em", "h1", "h2", "h3", "h4",
    "hr", "i", "li", "ol", "p", "pre", "strong", "table", "tbody", "td",
    "th", "thead", "tr", "ul",
}
_ALLOWED_ATTRIBUTES = {"a": {"href", "title"}, "td": {"align"}, "th": {"align"}}


def send_report_via_email(report_markdown: str, recipient: str) -> None:
    """Send the Markdown report as an HTML email with a plain-text fallback.

    Reads SMTP credentials from environment variables:
        SMTP_SERVER   – hostname of the SMTP server
        SMTP_PORT     – port number (default 587)
        SMTP_USER     – sender email address / login
        SMTP_PASSWORD – sender password

    Args:
        report_markdown: The report content in Markdown format.
        recipient:       Destination email address.

    Raises:
        EnvironmentError: If required environment variables are missing.
        smtplib.SMTPException: For unexpected SMTP errors after logging.
    """
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    missing = [
        name
        for name, val in [
            ("SMTP_SERVER", smtp_server),
            ("SMTP_USER", smtp_user),
            ("SMTP_PASSWORD", smtp_password),
        ]
        if not val
    ]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    raw_html = md.markdown(report_markdown, extensions=["tables", "fenced_code"])
    # Sanitise the generated HTML against an explicit allowlist so that any
    # HTML/script injected via LLM output or Markdown source is stripped
    # before the message is sent.
    html_body = nh3.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = "📰 Daily Research Report"
    message["From"] = smtp_user
    message["To"] = recipient

    message.attach(MIMEText(report_markdown, "plain"))
    message.attach(MIMEText(html_body, "html"))

    # Use an explicit SSL context so that certificate validation is enforced
    # and STARTTLS cannot be downgraded by a man-in-the-middle.
    tls_context = ssl.create_default_context()

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=tls_context)
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, message.as_string())
        logger.info("Report successfully sent to %s.", recipient)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP authentication failed: %s", exc)
        raise
    except smtplib.SMTPException as exc:
        logger.error("Failed to send report email: %s", exc)
        raise
