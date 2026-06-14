#!/usr/bin/env bash
set -euo pipefail

echo "== Checkpoint A: NVIDIA GPU =="
nvidia-smi

echo
echo "== Checkpoint A.1: CUDA toolkit =="
nvcc --version || true

echo
echo "If nvidia-smi fails, the GB10 runtime is not ready for GR00T or Isaac Sim."
echo "If nvcc is missing, verify whether CUDA toolkit setup is required for your GR00T install path."
