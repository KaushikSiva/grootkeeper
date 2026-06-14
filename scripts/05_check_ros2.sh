#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

ros2 --help >/dev/null
echo "ROS 2 CLI available"
echo "ROS_DISTRO=${ROS_DISTRO:-unset}"
