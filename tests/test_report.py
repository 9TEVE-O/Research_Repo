"""Tests for report.py."""

from models import ScoredRepo
from report import build_markdown_report


def _repo(name="owner/repo", score=80) -> ScoredRepo:
    return ScoredRepo(
        name=name,
        url=f"https://github.com/{name}",
        relevance_score=score,
        summary="A useful summary.",
        reason="Very relevant.",
    )


class TestBuildMarkdownReport:
    def test_contains_date_in_header(self):
        md = build_markdown_report([_repo()], "2024-01-15")
        assert "2024-01-15" in md

    def test_contains_repo_name(self):
        md = build_markdown_report([_repo("myorg/myrepo")], "2024-01-15")
        assert "myorg/myrepo" in md

    def test_contains_relevance_score(self):
        md = build_markdown_report([_repo(score=92)], "2024-01-15")
        assert "92/100" in md

    def test_contains_summary_and_reason(self):
        repo = _repo()
        md = build_markdown_report([repo], "2024-01-15")
        assert repo.summary in md
        assert repo.reason in md

    def test_table_of_contents_has_correct_count(self):
        repos = [_repo("a/b"), _repo("c/d"), _repo("e/f")]
        md = build_markdown_report(repos, "2024-01-15")
        assert md.count("📋 Table of Contents") == 1
        for repo in repos:
            assert repo.name in md

    def test_empty_repos_returns_header_and_footer(self):
        md = build_markdown_report([], "2024-01-15")
        assert "Daily Research Report" in md
        assert "Daily Research Agent" in md

    def test_repo_url_linked(self):
        repo = _repo("owner/repo")
        md = build_markdown_report([repo], "2024-01-15")
        assert repo.url in md
