# Research_Repo

> A daily AI research agent that discovers, scores, and reports on relevant LLM and AI GitHub repositories.

Research_Repo is a Python-based research automation project that searches GitHub for AI repositories, scores them for research relevance, generates Markdown reports, and can deliver those reports by email or GitHub Gist.

---

## Features

- Automated GitHub repository discovery
- LLM-based repository scoring
- Markdown report generation
- Optional email delivery
- Optional GitHub Gist publishing
- Policy and terms analysis via AI-Policy-Terms-Analyzer

---

## Project structure

```text
Research_Repo/
├── agent.py
├── selector.py
├── report.py
├── email_sender.py
├── gist_uploader.py
├── policy_analysis.py
├── external/
│   └── AI-Policy-Terms-Analyzer/
└── requirements.txt
```

---

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key
- GitHub personal access token
- SMTP-enabled email account (optional)

### Installation

```bash
git clone --recurse-submodules https://github.com/9TEVE-O/Research_Repo.git
cd Research_Repo
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | GitHub repository search and Gist access |
| `OPENAI_API_KEY` | LLM scoring |
| `REPORT_RECIPIENT` | Report delivery email |
| `SMTP_SERVER` | SMTP host |
| `SMTP_PORT` | SMTP port |
| `SMTP_USER` | SMTP login |
| `SMTP_PASSWORD` | SMTP password |
| `GIST_ID` | Optional Gist update target |

---

## Usage

```bash
export GITHUB_TOKEN="your-token"
export OPENAI_API_KEY="your-openai-key"
python agent.py
```

---

## How it works

1. Fetch candidate AI repositories from GitHub.
2. Score repositories for research relevance.
3. Select the strongest results.
4. Generate a Markdown report.
5. Optionally enrich results with policy analysis.
6. Deliver the report via email or GitHub Gist.

---

## Policy and terms analysis

The project can enrich repositories with lightweight policy and privacy analysis using the vendored AI-Policy-Terms-Analyzer submodule.

The analyser attaches:

- privacy summaries
- privacy concern severity counts
- third-party service mentions
- data-sharing references
- detected technologies

---

## Security note

Do not commit real API keys, SMTP credentials, tokens, or private report data.

Use environment variables or GitHub Actions secrets for sensitive configuration.

---

## License

This project is licensed under the MIT License.
