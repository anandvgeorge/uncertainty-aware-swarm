#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
if [ -f /workspace/ros2_ws/install/setup.bash ]; then
    source /workspace/ros2_ws/install/setup.bash
fi

# start ros_gz_bridge
exec ros2 run ros_gz_bridge parameter_bridge \
    --ros-args -p config_file:=/workspace/config/ros_gz_bridge.yaml
