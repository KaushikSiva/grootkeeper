#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${GROOT_REPO_DIR:-}" ]]; then
  echo "GROOT_REPO_DIR must be set in .env" >&2
  exit 1
fi

cd "${GROOT_REPO_DIR}"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "Expected ${GROOT_REPO_DIR}/.venv/bin/activate" >&2
  exit 1
fi

source .venv/bin/activate

if [[ "$(uname -m)" == "aarch64" && -f "scripts/activate_spark.sh" ]]; then
  source scripts/activate_spark.sh
fi

ARGS=(
  gr00t/eval/run_gr00t_server.py
  --host "${GROOT_SERVER_HOST:-0.0.0.0}"
  --port "${GROOT_SERVER_PORT:-5555}"
  --device "${GROOT_SERVER_DEVICE:-cuda}"
  --embodiment-tag "${GROOT_EMBODIMENT_TAG:-new_embodiment}"
)

if [[ -n "${GROOT_CHECKPOINT:-}" ]]; then
  ARGS+=(--model-path "${GROOT_CHECKPOINT}")
fi

if [[ -n "${GROOT_MODALITY_CONFIG_PATH:-}" ]]; then
  ARGS+=(--modality-config-path "${GROOT_MODALITY_CONFIG_PATH}")
fi

exec python "${ARGS[@]}"
