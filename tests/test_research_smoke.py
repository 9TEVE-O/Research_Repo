"""Regression checks for the no-secret Actions research scan."""
from pathlib import Path
from unittest.mock import patch

from config import Config
from pipeline import run
from scoring import score_metadata


def test_metadata_scoring_is_bounded_deterministic_and_labels_the_basis():
    candidates = [
        {"full_name": "owner/one", "html_url": "https://github.com/owner/one",
         "description": "LLM discovery", "topics": ["llm", "research"], "stargazers_count": 100},
        {"full_name": "owner/two", "html_url": "https://github.com/owner/two",
         "description": None, "topics": [], "stargazers_count": 10},
    ]
    assert score_metadata(candidates) == score_metadata(candidates)
    results = score_metadata(candidates)
    assert len(results) == 2
    assert results[0].relevance_score == 75
    assert all(0 <= r.relevance_score <= 100 for r in results)
    assert "not an AI quality assessment" in results[0].reason
    assert results[1].summary.startswith("No description")


def test_metadata_mode_produces_report_without_openai_or_smtp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = Config(
        github_token="actions-token", openai_api_key="",
        report_recipient="", smtp_server="", smtp_user="", smtp_password="",
        search_per_page=2, top_k=1,
    )
    with (
        patch("pipeline.fetch_candidates", return_value=[
            {"full_name": "owner/one", "html_url": "https://github.com/owner/one",
             "description": "An LLM research project", "topics": ["llm", "research"]},
        ]) as fetch,
        patch("pipeline.openai.OpenAI") as openai_client,
        patch("pipeline.send_report_via_email") as email,
        patch("pipeline.upload_to_gist") as gist,
        patch("pipeline.save_repos") as save,
        patch("policy_analysis.annotate_with_policy", side_effect=lambda repos, token: repos),
    ):
        run(cfg)
    body = Path("reports/latest.md").read_text(encoding="utf-8")
    assert "owner/one" in body
    assert "GitHub metadata-only heuristic (no AI evaluation)" in body
    fetch.assert_called_once()
    openai_client.assert_not_called()
    email.assert_not_called()
    gist.assert_not_called()
    save.assert_called_once()


def test_partial_email_config_does_not_fetch_or_create_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = Config(
        github_token="actions-token", openai_api_key="",
        report_recipient="you@example.com", smtp_server="",
        smtp_user="", smtp_password="",
    )
    with patch("pipeline.fetch_candidates") as fetch:
        run(cfg)
    fetch.assert_not_called()
    assert not Path("reports/latest.md").exists()
