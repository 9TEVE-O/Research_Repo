"""Build a formatted Markdown daily research report."""

import html


def build_markdown_report(repos: list, date: str) -> str:
    """Return a formatted Markdown string for the daily research report.

    All LLM-returned text fields (summary, reason) are HTML-escaped before
    being embedded so that injected HTML/script cannot survive the subsequent
    Markdown-to-HTML conversion in the email sender.

    Args:
        repos: List of repository objects, each containing:
               name, url, relevance_score, summary, reason.
        date:  Report date string (e.g. "2024-01-15").

    Returns:
        A Markdown-formatted report string.
    """
    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append(f"# 📰 Daily Research Report — {date}\n")
    lines.append(
        "> Automatically generated summary of the top GitHub repositories "
        "for today.\n"
    )

    # ── Table of Contents ───────────────────────────────────────────────────
    lines.append("---\n")
    lines.append("## 📋 Table of Contents\n")
    for i, repo in enumerate(repos, start=1):
        anchor = repo.name.lower().replace(" ", "-").replace("/", "")
        lines.append(f"{i}. [{repo.name}](#{anchor})")
    lines.append("")

    # ── Repository Sections ─────────────────────────────────────────────────
    lines.append("---\n")
    for i, repo in enumerate(repos, start=1):
        anchor = repo.name.lower().replace(" ", "-").replace("/", "")
        # LLM-returned fields are treated as untrusted plaintext; escape any
        # HTML characters before embedding them in the Markdown source so they
        # cannot inject tags when the Markdown is rendered to HTML.
        safe_summary = html.escape(repo.summary)
        safe_reason = html.escape(repo.reason)
        lines.append(f'<a id="{anchor}"></a>\n')
        lines.append(f"## {i}. 🔗 [{repo.name}]({repo.url})\n")
        lines.append(f"**⭐ Relevance Score:** `{repo.relevance_score}/100`\n")
        lines.append(f"**💡 Why this repo?**\n{safe_reason}\n")
        lines.append(f"**📝 Summary**\n{safe_summary}\n")

        # ── Optional Policy & Terms Analysis subsection ──────────────────
        policy = getattr(repo, 'policy', None)
        if policy:
            lines.append("**🛡️ Policy & Terms Analysis**\n")
            error = policy.get("error") if isinstance(policy, dict) else getattr(policy, 'error', None)
            if error:
                lines.append(
                    f"_Policy analysis unavailable: {html.escape(str(error))}_\n"
                )
            else:
                summary_text = html.escape((policy.get("summary", "") if isinstance(policy, dict) else getattr(policy, 'summary', "")) or "")
                if summary_text:
                    lines.append(f"{summary_text}\n")

                concerns = (policy.get("privacy_concerns", {}) if isinstance(policy, dict) else getattr(policy, 'privacy_concerns', {})) or {}
                high = int(concerns.get("high", 0))
                medium = int(concerns.get("medium", 0))
                low = int(concerns.get("low", 0))
                lines.append(
                    f"**🔐 Privacy concerns:** High: {high} · "
                    f"Medium: {medium} · Low: {low}\n"
                )

                tps = policy.get("third_party_services", []) if isinstance(policy, dict) else getattr(policy, 'third_party_services', [])
                if tps:
                    lines.append("**🔗 Third-party services:**")
                    for item in tps[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

                sharing = policy.get("data_sharing", []) if isinstance(policy, dict) else getattr(policy, 'data_sharing', [])
                if sharing:
                    lines.append("**📤 Data sharing:**")
                    for item in sharing[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

                techs = policy.get("technologies", []) if isinstance(policy, dict) else getattr(policy, 'technologies', [])
                if techs:
                    lines.append("**⚙️ Technologies detected:**")
                    for item in techs[:5]:
                        lines.append(f"- {html.escape(str(item))}")
                    lines.append("")

        lines.append("---\n")

    # ── Footer ──────────────────────────────────────────────────────────────
    lines.append(
        f"*Report generated on {date} by the Daily Research Agent 🤖*"
    )

    return "\n".join(lines)
