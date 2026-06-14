#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

export MODEL_BACKEND=groot
source .venv/bin/activate
echo "Backend expects a GR00T policy server at tcp://${GROOT_SERVER_HOST:-127.0.0.1}:${GROOT_SERVER_PORT:-5555}"
cd backend
uvicorn app:app --host "${BACKEND_HOST:-0.0.0.0}" --port "${BACKEND_PORT:-8000}" --reload
