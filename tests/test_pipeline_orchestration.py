"""Integration-style tests for pipeline.run()'s orchestration wiring.

Unlike tests/test_pipeline.py (which covers the unrelated src/pipeline.py
visual-search-answer agent), these exercise the root pipeline.py module that
agent.py actually delegates to in production: config validation, the
fetch -> score -> select -> persist -> report -> deliver sequence, and that a
delivery failure propagates instead of being swallowed.
"""

from unittest.mock import MagicMock, patch

from config import Config
from models import ScoredRepo


def _valid_config(**overrides) -> Config:
    defaults = dict(
        github_token="gh-token",
        openai_api_key="oa-key",
        report_recipient="dest@example.com",
        smtp_server="smtp.example.com",
        smtp_user="user",
        smtp_password="pw",
        gist_id="",
    )
    defaults.update(overrides)
    return Config(**defaults)


def _scored_repo() -> ScoredRepo:
    return ScoredRepo(
        name="owner/repo",
        url="https://github.com/owner/repo",
        relevance_score=90,
        summary="A great repo.",
        reason="Very relevant.",
    )


class TestConfigValidation:
    def test_invalid_config_exits_before_any_side_effect(self):
        from pipeline import run

        cfg = Config(
            github_token="",
            openai_api_key="",
            report_recipient="",
            smtp_server="",
            smtp_user="",
            smtp_password="",
        )
        with patch("pipeline.fetch_candidates") as fetch_mock:
            run(cfg)
        fetch_mock.assert_not_called()


@patch("policy_analysis.annotate_with_policy", side_effect=lambda repos, token: repos)
@patch("pipeline.upload_to_gist", return_value="https://gist.example.com/1")
@patch("pipeline.send_report_via_email")
@patch("pipeline.save_repos")
@patch("pipeline.score_all", return_value=[_scored_repo()])
@patch("pipeline.fetch_candidates", return_value=[{"full_name": "owner/repo"}])
@patch("openai.OpenAI")
class TestHappyPath:
    def test_full_pipeline_wires_fetch_through_delivery(
        self,
        mock_openai,
        mock_fetch,
        mock_score_all,
        mock_save_repos,
        mock_send_email,
        mock_upload_gist,
        mock_annotate,
    ):
        from pipeline import run

        cfg = _valid_config()
        run(cfg)

        mock_fetch.assert_called_once_with(
            cfg.github_token, query=cfg.search_query, per_page=cfg.search_per_page
        )
        mock_score_all.assert_called_once()
        mock_save_repos.assert_called_once()
        mock_send_email.assert_called_once()
        mock_upload_gist.assert_not_called()

    def test_gist_uploaded_when_gist_id_configured(
        self,
        mock_openai,
        mock_fetch,
        mock_score_all,
        mock_save_repos,
        mock_send_email,
        mock_upload_gist,
        mock_annotate,
    ):
        from pipeline import run

        cfg = _valid_config(gist_id="abc123", gist_token="gist-tok")
        run(cfg)

        mock_upload_gist.assert_called_once()
        args, _ = mock_upload_gist.call_args
        assert args[1] == "abc123"
        assert args[2] == "gist-tok"

    def test_email_failure_is_re_raised(
        self,
        mock_openai,
        mock_fetch,
        mock_score_all,
        mock_save_repos,
        mock_send_email,
        mock_upload_gist,
        mock_annotate,
    ):
        from pipeline import run
        import pytest

        mock_send_email.side_effect = RuntimeError("smtp down")
        cfg = _valid_config()
        with pytest.raises(RuntimeError, match="smtp down"):
            run(cfg)
        mock_upload_gist.assert_not_called()

    def test_gist_failure_is_re_raised(
        self,
        mock_openai,
        mock_fetch,
        mock_score_all,
        mock_save_repos,
        mock_send_email,
        mock_upload_gist,
        mock_annotate,
    ):
        from pipeline import run
        import pytest

        mock_upload_gist.side_effect = RuntimeError("gist api down")
        cfg = _valid_config(gist_id="abc123")
        with pytest.raises(RuntimeError, match="gist api down"):
            run(cfg)
