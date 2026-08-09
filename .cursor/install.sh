#!/usr/bin/env bash
# Idempotent Cloud Agent setup for Research_Repo.
#
# Prepares two things:
#   1. A Python virtual environment (.venv) with runtime + test dependencies
#      for the daily research agent.
#   2. Node dependencies for the academic-paper-terminal web app (frontend +
#      Express backend).
#
# Safe to re-run: every step checks/refreshes existing state rather than
# duplicating it.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Ensuring python3-venv is available"
# Ubuntu ships an externally-managed Python; the venv module needs the
# distro package to provide ensurepip.
if ! dpkg -s python3.12-venv >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3.12-venv
fi

echo "==> Creating/refreshing Python virtual environment (.venv)"
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt

echo "==> Initialising optional vendored submodule (best-effort)"
# policy_analyzer.py lives in the repo root, so the pipeline works even if the
# vendored submodule is unavailable. Do not fail the whole install on a network
# hiccup here.
git submodule update --init --recursive || \
  echo "WARN: submodule init failed; continuing (policy analysis is optional)."

echo "==> Installing academic-paper-terminal web app dependencies"
( cd academic-paper-terminal && npm install )
( cd academic-paper-terminal/server && npm install )

echo "==> Install complete."
