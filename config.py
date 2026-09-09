"""Environment parsing and application defaults."""

import os
from dataclasses import dataclass

# Names of all required environment variables (used for validation).
REQUIRED_ENV_VARS: tuple[str, ...] = (
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
    "REPORT_RECIPIENT",
    "SMTP_SERVER",
    "SMTP_USER",
    "SMTP_PASSWORD",
)


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, treating blank/missing as default."""
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


def missing_required_vars() -> list[str]:
    """Return names of required environment variables that are not set."""
    return [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]


@dataclass
class Config:
    """All runtime configuration sourced from environment variables."""

    github_token: str
    openai_api_key: str
    report_recipient: str
    smtp_server: str
    smtp_user: str
    smtp_password: str
    smtp_port: int = 587
    gist_id: str = ""
    gist_token: str = ""
    search_query: str = "topic:llm topic:research stars:>50"
    search_per_page: int = 20
    top_k: int = 3
    score_threshold: int = 50
    llm_model: str = "gpt-4o-mini"

    def is_valid(self) -> bool:
        """Return True when all required variables are present."""
        return all(
            [
                bool(self.github_token),
                bool(self.openai_api_key),
                bool(self.report_recipient),
                bool(self.smtp_server),
                bool(self.smtp_user),
                bool(self.smtp_password),
            ]
        )


def load_config() -> Config:
    """Read configuration from environment variables and return a Config.

    Required variables:
        GITHUB_TOKEN, OPENAI_API_KEY, REPORT_RECIPIENT,
        SMTP_SERVER, SMTP_USER, SMTP_PASSWORD

    Optional variables:
        SMTP_PORT (default 587), GIST_ID, GITHUB_GIST_TOKEN, SEARCH_QUERY,
        SEARCH_PER_PAGE, TOP_K, SCORE_THRESHOLD, LLM_MODEL

    GITHUB_GIST_TOKEN, when set, is used for Gist uploads instead of
    GITHUB_TOKEN so that the search token (public_repo scope) need not
    also carry gist scope. Falls back to GITHUB_TOKEN when unset.
    """
    github_token = os.environ.get("GITHUB_TOKEN", "")
    return Config(
        github_token=github_token,
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        report_recipient=os.environ.get("REPORT_RECIPIENT", ""),
        smtp_server=os.environ.get("SMTP_SERVER", ""),
        smtp_user=os.environ.get("SMTP_USER", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        smtp_port=_env_int("SMTP_PORT", 587),
        gist_id=os.environ.get("GIST_ID", ""),
        gist_token=os.environ.get("GITHUB_GIST_TOKEN") or github_token,
        search_query=os.environ.get(
            "SEARCH_QUERY", "topic:llm topic:research stars:>50"
        ),
        search_per_page=_env_int("SEARCH_PER_PAGE", 20),
        top_k=_env_int("TOP_K", 3),
        score_threshold=_env_int("SCORE_THRESHOLD", 50),
        llm_model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    )

