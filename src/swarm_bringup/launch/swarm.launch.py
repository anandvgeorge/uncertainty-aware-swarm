"""Start three independent Burger/Nav2 instances in the shared Gazebo world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    single_robot_launch = os.path.join(
        get_package_share_directory('swarm_bringup'), 'launch', 'single_robot.launch.py',
    )
    robots = [('robot1', '0.0', '0.0'),
              ('robot2', '0.0', '2.0'),
              ('robot3', '0.0', '-2.0')]
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='empty'),
        *[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(single_robot_launch),
                launch_arguments={
                    'world': LaunchConfiguration('world'),
                    'robot_name': name, 'namespace': name,
                    'x': x, 'y': y,
                    'start_clock_bridge': 'true' if index == 0 else 'false',
                }.items(),
            )
            for index, (name, x, y) in enumerate(robots)
        ],
    ])
