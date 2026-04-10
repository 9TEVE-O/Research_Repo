"""Environment parsing and application defaults."""

import os
from dataclasses import dataclass, field


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
    search_query: str = "topic:llm topic:research stars:>50"
    search_per_page: int = 20
    top_k: int = 3
    score_threshold: int = 50
    llm_model: str = "gpt-4o-mini"
    missing_vars: list = field(default_factory=list, init=False, repr=False)

    def is_valid(self) -> bool:
        """Return True when all required variables are present."""
        return len(self.missing_vars) == 0


def load_config() -> Config:
    """Read configuration from environment variables and return a Config.

    Required variables:
        GITHUB_TOKEN, OPENAI_API_KEY, REPORT_RECIPIENT,
        SMTP_SERVER, SMTP_USER, SMTP_PASSWORD

    Optional variables:
        SMTP_PORT (default 587), GIST_ID, SEARCH_QUERY,
        SEARCH_PER_PAGE, TOP_K, SCORE_THRESHOLD, LLM_MODEL
    """
    required = {
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "REPORT_RECIPIENT": os.environ.get("REPORT_RECIPIENT", ""),
        "SMTP_SERVER": os.environ.get("SMTP_SERVER", ""),
        "SMTP_USER": os.environ.get("SMTP_USER", ""),
        "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
    }
    missing = [k for k, v in required.items() if not v]

    cfg = Config(
        github_token=required["GITHUB_TOKEN"],
        openai_api_key=required["OPENAI_API_KEY"],
        report_recipient=required["REPORT_RECIPIENT"],
        smtp_server=required["SMTP_SERVER"],
        smtp_user=required["SMTP_USER"],
        smtp_password=required["SMTP_PASSWORD"],
        smtp_port=int(os.environ.get("SMTP_PORT", 587)),
        gist_id=os.environ.get("GIST_ID", ""),
        search_query=os.environ.get(
            "SEARCH_QUERY", "topic:llm topic:research stars:>50"
        ),
        search_per_page=int(os.environ.get("SEARCH_PER_PAGE", 20)),
        top_k=int(os.environ.get("TOP_K", 3)),
        score_threshold=int(os.environ.get("SCORE_THRESHOLD", 50)),
        llm_model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    )
    cfg.missing_vars = missing
    return cfg
