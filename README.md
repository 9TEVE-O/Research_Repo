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
├── agent.py                           # Main pipeline: fetch → score → select → report → send
├── selector.py                        # Filters and ranks repositories by relevance score
├── report.py                          # Builds the Markdown report from scored repositories
├── email_sender.py                    # Sends the report via SMTP
├── gist_uploader.py                   # Uploads the report to a GitHub Gist
├── policy_analysis.py                 # Enriches scored repos with privacy/terms analysis
├── external/
│   └── AI-Policy-Terms-Analyzer/      # Git submodule — upstream PolicyAnalyzer library
└── requirements.txt                   # Python dependencies
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
git clone --recurse-submodules https://github.com/9TEVE-O/Research_Repo.git
cd Research_Repo
pip install -r requirements.txt
```

> **Note:** This repository vendors
> [AI-Policy-Terms-Analyzer](https://github.com/9TEVE-O/AI-Policy-Terms-Analyzer)
> as a git submodule under `external/`. If you cloned without
> `--recurse-submodules`, fetch it now:
>
> ```bash
> git submodule update --init --recursive
> ```

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

## Policy & Terms Analysis (new)

Each scored repository is now enriched with a lightweight privacy / terms
analysis powered by the vendored
[AI-Policy-Terms-Analyzer](https://github.com/9TEVE-O/AI-Policy-Terms-Analyzer)
library (included as a git submodule at `external/AI-Policy-Terms-Analyzer`).

**How to initialize the submodule** (one-time, after clone):

```bash
git submodule update --init --recursive
```

**What it does.** After the LLM has scored each candidate, the agent calls
`policy_analysis.annotate_with_policy()`, which for every scored repo:

1. Fetches the repository's README from the GitHub API
   (`/repos/{owner}/{repo}/readme` with `Accept: application/vnd.github.raw`).
2. Runs the README text through `PolicyAnalyzer.analyze()`.
3. Attaches a condensed `policy` dict to the repo with these fields:

   | Field                  | Description                                          |
   |------------------------|------------------------------------------------------|
   | `summary`              | Plain-English privacy summary (≤ 500 chars)          |
   | `privacy_concerns`     | Counts keyed by severity: `high` / `medium` / `low`  |
   | `third_party_services` | Deduped list of mentioned third-party services (≤10) |
   | `data_sharing`         | Entities data is shared with (≤10)                   |
   | `technologies`         | Detected technologies/trackers (≤10)                 |
   | `analyzed_chars`       | How many README chars were analyzed                  |
   | `error`                | Populated only when analysis failed for this repo    |

`report.py` renders these fields as a new **🛡️ Policy & Terms Analysis**
subsection inside each repository block of the Markdown report. Failures for a
single repo are isolated — the original pipeline output is unchanged whenever
the analyzer cannot run.

---

## License

This project is licensed under the [MIT License](LICENSE).
