#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

ros2 --version
echo "ROS_DISTRO=${ROS_DISTRO:-unset}"
