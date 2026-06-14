#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate

echo "Using Python: $(python --version)"
echo "Using pip: $(python -m pip --version)"
echo
echo "Active pip-related environment:"
env | grep -E '^(PIP_|UV_)' || true
echo
echo "Active pip config:"
python -m pip config debug || true

python -m pip install --upgrade pip

if [[ -n "${PIP_INDEX_URL:-}" ]]; then
  echo
  echo "Installing backend requirements with PIP_INDEX_URL=${PIP_INDEX_URL}"
  python -m pip install --no-cache-dir -r backend/requirements.txt
else
  echo
  echo "Installing backend requirements with default pip index configuration"
  if ! python -m pip install --no-cache-dir -r backend/requirements.txt; then
    echo
    echo "Default pip index failed."
    echo "Retrying once against https://pypi.org/simple"
    PIP_INDEX_URL="https://pypi.org/simple" python -m pip install --no-cache-dir -r backend/requirements.txt
  fi
fi

echo "Python backend environment ready in .venv"
