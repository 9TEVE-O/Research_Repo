"""Build a formatted Markdown daily research report."""


def build_markdown_report(repos: list, date: str) -> str:
    """Return a formatted Markdown string for the daily research report.

    Args:
        repos: List of repository dicts, each containing:
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
        anchor = repo["name"].lower().replace(" ", "-").replace("/", "")
        lines.append(f"{i}. [{repo['name']}](#{anchor})")
    lines.append("")

    # ── Repository Sections ─────────────────────────────────────────────────
    lines.append("---\n")
    for i, repo in enumerate(repos, start=1):
        anchor = repo["name"].lower().replace(" ", "-").replace("/", "")
        lines.append(f"## {i}. 🔗 [{repo['name']}]({repo['url']}) {{#{anchor}}}\n")
        lines.append(f"**⭐ Relevance Score:** `{repo['relevance_score']}/100`\n")
        lines.append(f"**💡 Why this repo?**\n{repo['reason']}\n")
        lines.append(f"**📝 Summary**\n{repo['summary']}\n")
        lines.append("---\n")

    # ── Footer ──────────────────────────────────────────────────────────────
    lines.append(
        f"*Report generated on {date} by the Daily Research Agent 🤖*"
    )

    return "\n".join(lines)
