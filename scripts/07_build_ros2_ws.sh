#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"
if [[ ! -f "$ROS_SETUP" ]]; then
  echo "ROS setup file missing: $ROS_SETUP"
  exit 1
fi

set +u
source "$ROS_SETUP"
set -u
cd ros2_ws
colcon build
set +u
source install/setup.bash
set -u

echo "ROS 2 workspace built and sourced."
