#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

source .venv/bin/activate
python backend/groot_smoke_test.py
