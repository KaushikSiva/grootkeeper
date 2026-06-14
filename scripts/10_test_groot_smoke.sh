#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

HOST="${BACKEND_HOST:-127.0.0.1}"
PORT="${BACKEND_PORT:-8000}"

curl -sS \
  -X POST \
  "http://${HOST}:${PORT}/groot/smoke" \
  -H "Content-Type: application/json" \
  -d '{"command":"Pick up trash in the room and put it in the dustbin"}'
echo
