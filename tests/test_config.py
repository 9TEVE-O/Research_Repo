"""Tests for config.py."""

import pytest

from config import Config, load_config, missing_required_vars


REQUIRED_ENV = {
    "GITHUB_TOKEN": "gh_tok",
    "OPENAI_API_KEY": "sk-key",
    "REPORT_RECIPIENT": "you@example.com",
    "SMTP_SERVER": "smtp.example.com",
    "SMTP_USER": "sender@example.com",
    "SMTP_PASSWORD": "secret",
}


class TestLoadConfig:
    def test_valid_config(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        cfg = load_config()
        assert cfg.is_valid()

    def test_is_invalid_when_vars_missing(self, monkeypatch):
        for k in REQUIRED_ENV:
            monkeypatch.delenv(k, raising=False)
        cfg = load_config()
        assert not cfg.is_valid()

    def test_defaults(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        cfg = load_config()
        assert cfg.smtp_port == 587
        assert cfg.top_k == 3
        assert cfg.score_threshold == 50
        assert cfg.llm_model == "gpt-4o-mini"
        assert cfg.gist_id == ""

    def test_blank_optional_port_uses_default(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("SMTP_PORT", "")
        cfg = load_config()
        assert cfg.smtp_port == 587

    def test_blank_optional_integers_use_defaults(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("SEARCH_PER_PAGE", "")
        monkeypatch.setenv("TOP_K", "")
        monkeypatch.setenv("SCORE_THRESHOLD", "")
        cfg = load_config()
        assert cfg.search_per_page == 20
        assert cfg.top_k == 3
        assert cfg.score_threshold == 50

    def test_gist_token_falls_back_to_github_token(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("GITHUB_GIST_TOKEN", raising=False)
        cfg = load_config()
        assert cfg.gist_token == cfg.github_token

    def test_gist_token_uses_dedicated_var_when_set(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("GITHUB_GIST_TOKEN", "gist-scoped-tok")
        cfg = load_config()
        assert cfg.gist_token == "gist-scoped-tok"
        assert cfg.gist_token != cfg.github_token

    def test_optional_overrides(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("SMTP_PORT", "465")
        monkeypatch.setenv("TOP_K", "5")
        monkeypatch.setenv("GIST_ID", "abc123")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        cfg = load_config()
        assert cfg.smtp_port == 465
        assert cfg.top_k == 5
        assert cfg.gist_id == "abc123"
        assert cfg.llm_model == "gpt-4o"


class TestMissingRequiredVars:
    def test_returns_empty_when_all_set(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        assert missing_required_vars() == []

    def test_returns_missing_names(self, monkeypatch):
        for k in REQUIRED_ENV:
            monkeypatch.delenv(k, raising=False)
        missing = missing_required_vars()
        assert set(missing) == set(REQUIRED_ENV.keys())

    def test_partial_missing(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)
        missing = missing_required_vars()
        assert missing == ["SMTP_PASSWORD"]
