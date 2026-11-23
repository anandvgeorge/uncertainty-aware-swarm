#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
if [ -f /workspace/ros2_ws/install/setup.bash ]; then
    source /workspace/ros2_ws/install/setup.bash
fi

# Spawn one official TurtleBot3 Burger and start its ROS interfaces.
exec ros2 launch swarm_bringup single_robot.launch.py
