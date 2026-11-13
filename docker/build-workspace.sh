#!/usr/bin/env bash
set -euo pipefail

cd /workspace/ros2_ws
colcon build "$@"
echo "Build finished"
