#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${GROOT_REPO_DIR:-}" ]]; then
  echo "GROOT_REPO_DIR is not set. Copy configs/env.example to .env and edit it first."
  exit 1
fi

if [[ -d "$GROOT_REPO_DIR" ]]; then
  echo "OK: GROOT_REPO_DIR exists at $GROOT_REPO_DIR"
else
  echo "Isaac-GR00T repo not found."
  echo "Clone it with:"
  echo "git clone https://github.com/NVIDIA/Isaac-GR00T.git \"$GROOT_REPO_DIR\""
  echo
  echo "Follow the official repo install instructions."
  echo "Do not fake install."
  exit 1
fi
