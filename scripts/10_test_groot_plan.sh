#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ "${GROOT_SMOKE_ONLY:-0}" == "1" ]]; then
  echo "GROOT_SMOKE_ONLY=1 is enabled; use ./scripts/10_test_groot_smoke.sh instead." >&2
  exit 1
fi

HOST="${BACKEND_HOST:-127.0.0.1}"
PORT="${BACKEND_PORT:-8000}"

curl -sS \
  -X POST \
  "http://${HOST}:${PORT}/plan" \
  -H "Content-Type: application/json" \
  -d '{"command":"Pick up trash in the room and put it in the dustbin"}'
echo
