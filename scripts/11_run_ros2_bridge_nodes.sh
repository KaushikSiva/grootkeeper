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
source ros2_ws/install/setup.bash
set -u

echo "ROS 2 bridge nodes are ready."
echo "Run in separate GB10 terminals:"
echo "  ros2 run trashbot_bridge scene_state_listener"
echo "  ros2 run trashbot_bridge isaac_execution_listener"
echo
echo "If you want a quick publisher diagnostic:"
echo "  ros2 run trashbot_bridge groot_action_publisher"
