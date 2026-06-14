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

source "$ROS_SETUP"
cd ros2_ws
colcon build
source install/setup.bash

echo "ROS 2 workspace built and sourced."
