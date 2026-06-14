#!/usr/bin/env bash
set -uo pipefail

failures=0

run_step() {
  local label="$1"
  local script_path="$2"

  echo
  echo "========== ${label} =========="
  if "$script_path"; then
    echo "[PASS] ${label}"
  else
    echo "[FAIL] ${label}"
    failures=$((failures + 1))
  fi
}

run_step "01 GPU" ./scripts/01_check_gb10_gpu.sh
run_step "04 GR00T smoke" ./scripts/04_groot_smoke_test.sh
run_step "05 ROS 2" ./scripts/05_check_ros2.sh
run_step "06 Isaac Sim" ./scripts/06_check_isaac_sim.sh
run_step "09 backend status" ./scripts/09_test_backend_status.sh
run_step "10 GR00T plan" ./scripts/10_test_groot_plan.sh

echo
echo "Checkpoint failures: ${failures}"
if [[ "$failures" -gt 0 ]]; then
  exit 1
fi
