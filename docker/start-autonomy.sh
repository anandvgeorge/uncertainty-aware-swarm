#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
if [ -f /workspace/ros2_ws/install/setup.bash ]; then
    source /workspace/ros2_ws/install/setup.bash
fi

# Start three independently namespaced Burger/Nav2 instances.
exec ros2 launch swarm_bringup swarm.launch.py
