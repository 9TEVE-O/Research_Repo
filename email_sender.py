"""Send the daily research report via email using smtplib."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown as md

logger = logging.getLogger(__name__)


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

    html_body = md.markdown(report_markdown, extensions=["tables", "fenced_code"])

    message = MIMEMultipart("alternative")
    message["Subject"] = "📰 Daily Research Report"
    message["From"] = smtp_user
    message["To"] = recipient

    message.attach(MIMEText(report_markdown, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, message.as_string())
        logger.info("Report successfully sent to %s.", recipient)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "SMTP authentication failed for user '%s': %s", smtp_user, exc
        )
        raise
    except smtplib.SMTPException as exc:
        logger.error("Failed to send report email: %s", exc)
        raise
