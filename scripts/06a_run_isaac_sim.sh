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

ROS_SETUP="/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"
if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file missing: ${ROS_SETUP}"
  exit 1
fi

ISAAC_ROOT="$(cd "$(dirname "${ISAAC_SIM_PYTHON}")" && pwd)"
LAUNCHER=""

for candidate in \
  "${ISAAC_ROOT}/isaac-sim.sh" \
  "${ISAAC_ROOT}/runapp.sh" \
  "${ISAAC_ROOT}/AppRun"; do
  if [[ -x "${candidate}" ]]; then
    LAUNCHER="${candidate}"
    break
  fi
done

if [[ -z "${LAUNCHER}" ]]; then
  echo "Could not find an Isaac Sim launcher next to ${ISAAC_SIM_PYTHON}."
  echo "Checked: isaac-sim.sh, runapp.sh, AppRun"
  exit 1
fi

set +u
source "${ROS_SETUP}"
set -u

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-${TRASHBOT_ROS_DOMAIN_ID:-42}}"

echo "Launching Isaac Sim with:"
echo "  launcher: ${LAUNCHER}"
echo "  ROS setup: ${ROS_SETUP}"
echo "  ROS_DOMAIN_ID: ${ROS_DOMAIN_ID}"
echo
echo "Inside Isaac Sim:"
echo "  1. Enable omni.isaac.ros2_bridge if it is not already enabled."
echo "  2. Open Script Editor."
echo "  3. Run isaac/create_trashbot_scene.py once."
echo "  4. Run isaac/g1_joint_replay_executor.py to subscribe to /trashbot/groot_action."
echo

exec "${LAUNCHER}"
