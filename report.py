"""Build a formatted Markdown daily research report."""

import html


def _field(repo, key: str, default=""):
    """Get a field from a ScoredRepo dataclass or a plain dict."""
    if hasattr(repo, key):
        return getattr(repo, key)
    if hasattr(repo, "get"):
        return repo.get(key, default)
    return default


def build_markdown_report(repos: list, date: str) -> str:
    """Return a formatted Markdown string for the daily research report.

    All LLM-returned text fields (summary, reason) are HTML-escaped before
    being embedded so that injected HTML/script cannot survive the subsequent
    Markdown-to-HTML conversion in the email sender.

    Args:
        repos: List of repository dicts or ScoredRepo objects, each with
               name, url, relevance_score, summary, reason fields.
        date:  Report date string (e.g. "2024-01-15").

    Returns:
        A Markdown-formatted report string.
    """
    lines = []

    # ── Header ────────────────────────────────────────────────────────────────────────
    lines.append(f"# 📰 Daily Research Report — {date}\n")
    lines.append(
        "> Automatically generated summary of the top GitHub repositories "
        "for today.\n"
    )

    # ── Table of Contents ────────────────────────────────────────────────────────────
    lines.append("---\n")
    lines.append("## 📋 Table of Contents\n")
    for i, repo in enumerate(repos, start=1):
        name = _field(repo, "name")
        anchor = name.lower().replace(" ", "-").replace("/", "")
        lines.append(f"{i}. [{name}](#{anchor})")
    lines.append("")

    # ── Repository Sections ───────────────────────────────────────────────────────────
    lines.append("---\n")
    for i, repo in enumerate(repos, start=1):
        name = _field(repo, "name")
        url = _field(repo, "url")
        score = _field(repo, "relevance_score", 0)
        anchor = name.lower().replace(" ", "-").replace("/", "")
        # LLM-returned fields are treated as untrusted plaintext; escape any
        # HTML characters before embedding them in the Markdown source so they
        # cannot inject tags when the Markdown is rendered to HTML.
        safe_summary = html.escape(_field(repo, "summary"))
        safe_reason = html.escape(_field(repo, "reason"))
        lines.append(f'<a id="{anchor}"></a>\n')
        lines.append(f"## {i}. 🔗 [{name}]({url})\n")
        lines.append(f"**⭐ Relevance Score:** `{score}/100`\n")
        lines.append(f"**💡 Why this repo?**\n{safe_reason}\n")
        lines.append(f"**📝 Summary**\n{safe_summary}\n")

        # ── Optional Policy & Terms Analysis subsection ──────────────────
        policy = _field(repo, "policy", None)
        if policy:
            lines.append("**🛡️ Policy & Terms Analysis**\n")
            error = policy.get("error")
            if error:
                lines.append(
                    f"_Policy analysis unavailable: {html.escape(str(error))}_\n"
                )
            else:
                summary_text = html.escape(policy.get("summary", "") or "")
                if summary_text:
                    lines.append(f"{summary_text}\n")

                concerns = policy.get("privacy_concerns", {}) or {}
                high = int(concerns.get("high", 0))
                medium = int(concerns.get("medium", 0))
                low = int(concerns.get("low", 0))
                lines.append(
                    f"**🔐 Privacy concerns:** High: {high} · "
                    f"Medium: {medium} · Low: {low}\n"
                )

                tps = policy.get("third_party_services") or []
                if tps:
                    lines.append("**🔗 Third-party services:**")
                    for item in tps[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

                sharing = policy.get("data_sharing") or []
                if sharing:
                    lines.append("**📤 Data sharing:**")
                    for item in sharing[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

                techs = policy.get("technologies") or []
                if techs:
                    lines.append("**⚙️ Technologies detected:**")
                    for item in techs[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

        lines.append("---\n")

    # ── Footer ────────────────────────────────────────────────────────────────────────
    lines.append(
        f"*Report generated on {date} by the Daily Research Agent 🤖*"
    )

    return "\n".join(lines)
