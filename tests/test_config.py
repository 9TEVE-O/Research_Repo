"""Tests for config.py."""

import pytest

from config import Config, load_config


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
        assert cfg.missing_vars == []

    def test_missing_vars_captured(self, monkeypatch):
        for k in REQUIRED_ENV:
            monkeypatch.delenv(k, raising=False)
        cfg = load_config()
        assert not cfg.is_valid()
        assert set(cfg.missing_vars) == set(REQUIRED_ENV)

    def test_defaults(self, monkeypatch):
        for k, v in REQUIRED_ENV.items():
            monkeypatch.setenv(k, v)
        cfg = load_config()
        assert cfg.smtp_port == 587
        assert cfg.top_k == 3
        assert cfg.score_threshold == 50
        assert cfg.llm_model == "gpt-4o-mini"
        assert cfg.gist_id == ""

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
