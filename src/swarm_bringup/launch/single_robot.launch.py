"""Spawn one official TurtleBot3 Burger in the Gazebo server run by Compose."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    simulation_share = get_package_share_directory('turtlebot3_gazebo')
    # create sends this filename to the Gazebo server in the other container.
    # Both containers can read the unchanged model from the shared install volume.
    model = os.path.join(
        get_package_share_directory('swarm_bringup'),
        'simulation', 'turtlebot3_burger', 'model.sdf',
    )
    with open(os.path.join(
        simulation_share, 'urdf', 'turtlebot3_burger.urdf',
    ), encoding='utf-8') as description_file:
        robot_description = description_file.read()

    namespace = LaunchConfiguration('namespace')
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='empty'),
        DeclareLaunchArgument('robot_name', default_value='robot1'),
        DeclareLaunchArgument('namespace', default_value=LaunchConfiguration('robot_name')),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.01'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        # The official single-robot model uses global Gazebo topics. The
        # bridge exposes them under the ROS namespace and shares /clock.
        Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            name='robot_bridge', namespace=namespace,
            parameters=[{
                'config_file': os.path.join(
                    simulation_share, 'params', 'turtlebot3_burger_bridge.yaml',
                ),
                'use_sim_time': True,
            }],
            remappings=[('clock', '/clock')],
            output='screen',
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            namespace=namespace,
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
            remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
            output='screen',
        ),
        Node(
            package='tf2_ros', executable='static_transform_publisher',
            name='imu_frame_alias', namespace=namespace,
            arguments=[
                '--frame-id', 'imu_link',
                '--child-frame-id', PathJoinSubstitution([
                    LaunchConfiguration('robot_name'), 'imu_link', 'tb3_imu',
                ]),
            ],
            parameters=[{'use_sim_time': True}],
            remappings=[('/tf_static', 'tf_static')],
            output='screen',
        ),
        Node(
            package='ros_gz_sim', executable='create', output='screen',
            arguments=[
                '-world', LaunchConfiguration('world'),
                '-name', LaunchConfiguration('robot_name'),
                '-allow_renaming', 'false', '-file', model,
                '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                '-z', LaunchConfiguration('z'), '-Y', LaunchConfiguration('yaw'),
            ],
        ),
    ])
