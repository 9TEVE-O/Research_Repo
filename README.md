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
└── requirements.lock
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
pip install --require-hashes -r requirements.lock
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

## TypeSafe evidence classification (opt-in)

After recovering a source, assess one claim against its supplied text:

```bash
# Set TYPESAFE_API_KEY in your server environment or secret manager first.
python typesafe_evidence.py examples/typesafe_claim.json > classification.json
```

The example is synthetic. Replace it with a JSON record containing `claim`,
`source_text`, `source_url`, and `source_accessed_at`. Only these four fields are
sent to TypeSafe. Use text authorised for transmission to that external service.
The command does not retrieve sources or check their URL, date, or authenticity.

`TYPESAFE_MODEL` (or `--model`) defaults to `jev-latest`. For reproducible trials,
pin a provider-supported model version; receipts retain requested and returned
models, contract version, evaluation time, input hash, raw response and token usage.
The input hash binds the supplied fields; keep the original input separately.

Outcomes are `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT`, or `ABSTAIN`.
These describe the relationship between a claim and the supplied source, not
verified truth or the Newsletter Archaeologist's native evidence taxonomy.
Every outcome has `review_required: true` and `promotion_status: NOT_PROMOTED`.
Human promotion remains a separate decision. No confidence threshold grants
approval. Missing input/key, transport errors and invalid responses fail closed.

This command is separate from automated repository scoring, knowledge-graph
retention, email and Gist delivery. No scheduled workflow enables it. Existing
OpenAI scoring continues independently. No new runtime dependency is required.

API contract checked on 7 October 2026:
[TypeSafe API](https://docs.typesafe.ai/api) and
[citation-check cookbook](https://docs.typesafe.ai/cookbooks/citation_check).
Local transport/schema tests do not establish model accuracy or calibration.
