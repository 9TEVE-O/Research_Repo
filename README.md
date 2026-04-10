# Research_Repo

> A daily AI research agent that automatically discovers, scores, and reports on the top LLM/AI GitHub repositories.

GitHub hosts 4M+ AI projects, with LLM research up 178% yearly. This agent achieves its goals via an autonomous loop: it fetches candidate repositories, scores them with an LLM (evaluator-optimizer), selects the top results, and delivers a formatted report by email and GitHub Gist — autonomously improving through reflection.

---

## Features

- 🔍 **Automated Discovery** — Searches GitHub daily for trending LLM/AI research repositories
- 🤖 **LLM Scoring** — Uses OpenAI GPT-4o-mini to score each repository for research relevance (0–100)
- 📰 **Markdown Reports** — Generates structured daily reports with summaries and relevance scores
- 📧 **Email Delivery** — Sends reports as formatted HTML emails with plain-text fallback
- 📌 **Gist Upload** — Publishes each report to a GitHub Gist for easy sharing

---

## Project Structure

```
Research_Repo/
├── agent.py           # Thin CLI entry point
├── pipeline.py        # Orchestrates the full run
├── config.py          # Environment variable parsing + defaults
├── models.py          # Typed dataclasses / schemas
├── storage.py         # SQLite persistence
├── github_client.py   # Candidate repository fetch
├── scoring.py         # Deterministic + LLM scoring
├── selector.py        # Top-k selection
├── report.py          # Markdown report builder
├── email_sender.py    # Email delivery via SMTP
├── gist_uploader.py   # GitHub Gist delivery
├── tests/             # Unit tests
└── requirements.txt   # Python dependencies
```

---

## Setup

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [GitHub personal access token](https://github.com/settings/tokens) with `repo` and `gist` scopes
- An SMTP-enabled email account (e.g. Gmail with App Password)

### Installation

```bash
git clone https://github.com/9TEVE-O/Research_Repo.git
cd Research_Repo
pip install -r requirements.txt
```

### Environment Variables

Copy and export the following variables before running the agent:

| Variable           | Required | Description                                          |
|--------------------|----------|------------------------------------------------------|
| `GITHUB_TOKEN`     | ✅       | GitHub PAT for repository search and Gist access     |
| `OPENAI_API_KEY`   | ✅       | OpenAI API key for LLM scoring                       |
| `REPORT_RECIPIENT` | ✅       | Email address to receive the daily report            |
| `SMTP_SERVER`      | ✅       | SMTP hostname (e.g. `smtp.gmail.com`)                |
| `SMTP_PORT`        | ❌       | SMTP port (default: `587`)                           |
| `SMTP_USER`        | ✅       | Sender email address / SMTP login                    |
| `SMTP_PASSWORD`    | ✅       | Sender SMTP password or app password                 |
| `GIST_ID`          | ❌       | GitHub Gist ID to update; skips Gist upload if unset |

---

## Usage

```bash
export GITHUB_TOKEN="ghp_..."
export OPENAI_API_KEY="sk-..."
export REPORT_RECIPIENT="you@example.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="sender@gmail.com"
export SMTP_PASSWORD="your-app-password"
# Optional:
export GIST_ID="your-gist-id"

python agent.py
```

---

## How It Works

1. **Fetch** — Queries the GitHub Search API for repositories tagged with `topic:llm` and `topic:research` having more than 50 stars.
2. **Score** — Each repository is evaluated by the LLM, which returns a relevance score (0–100), a summary, and a reason.
3. **Select** — The top 3 repositories above the relevance threshold are chosen.
4. **Report** — A Markdown report is generated with a table of contents, repository details, and scores.
5. **Deliver** — The report is sent via email and optionally uploaded to a GitHub Gist.

---

## License

This project is licensed under the [MIT License](LICENSE).
