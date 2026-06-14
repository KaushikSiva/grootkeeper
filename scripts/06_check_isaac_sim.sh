#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${ISAAC_SIM_PYTHON:-}" ]]; then
  echo "ISAAC_SIM_PYTHON is not set. Edit .env first."
  exit 1
fi

if [[ -x "$ISAAC_SIM_PYTHON" || -f "$ISAAC_SIM_PYTHON" ]]; then
  echo "Isaac Sim python runtime found: $ISAAC_SIM_PYTHON"
else
  echo "ISAAC_SIM_PYTHON does not exist: $ISAAC_SIM_PYTHON"
  echo "Point it at Isaac Sim's python.sh on the GB10 runtime machine."
  exit 1
fi
