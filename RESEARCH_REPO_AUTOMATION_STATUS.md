# Research Repo Automation Status

automation_status: implemented
implementation_status: verified
github_actions_found: found
scripts_found: found
evidence_boundary: .github/workflows/research-agent.yml, agent.py, pipeline.py
final_authority: Steven Lees

## Status rule

This repository is an automated daily research agent. It searches GitHub for
LLM/AI repositories, scores them with OpenAI, selects the top-k results,
builds a Markdown report, sends it by email, and uploads it to a GitHub Gist.

## Evidence

Verified implementation evidence:

- `.github/workflows/research-agent.yml` — GitHub Actions cron workflow (daily, 8 AM UTC)
- `agent.py` — primary entry point
- `pipeline.py` — alternate orchestration entry point with knowledge graph and storage
- `scoring.py`, `selector.py`, `report.py`, `email_sender.py`, `gist_uploader.py` — supporting modules

## Review control

Final approving authority remains Steven Lees.
