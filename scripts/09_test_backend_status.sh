#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

HOST="${BACKEND_HOST:-127.0.0.1}"
PORT="${BACKEND_PORT:-8000}"

curl -sS "http://${HOST}:${PORT}/status"
echo
echo
curl -sS "http://${HOST}:${PORT}/system/status"
echo
