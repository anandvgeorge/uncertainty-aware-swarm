"""Spawn one official TurtleBot3 Burger in the Gazebo server run by Compose."""

import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    simulation_share = get_package_share_directory('turtlebot3_gazebo')
    # Reuse the official model and add Gazebo's ground-truth odometry system.
    model = os.path.join(
        get_package_share_directory('swarm_bringup'),
        'simulation', 'turtlebot3_burger', 'model.sdf',
    )
    bringup_share = get_package_share_directory('swarm_bringup')
    sdf = ET.parse(model)
    robot = sdf.getroot().find('model')
    drive = robot.find("plugin[@name='gz::sim::systems::DiffDrive']")
    # Keep wheel odometry separate from the ground-truth navigation source.
    drive.find('odom_topic').text = '/wheel_odom'
    drive.find('tf_topic').text = '/wheel_tf'
    robot.append(ET.parse(os.path.join(
        bringup_share, 'config', 'ground_truth_odometry.sdf',
    )).getroot())
    nav2_params = os.path.join(bringup_share, 'config', 'nav2.yaml')
    navigation_nodes = [
        ('nav2_controller', 'controller_server'),
        ('nav2_planner', 'planner_server'),
        ('nav2_behaviors', 'behavior_server'),
        ('nav2_bt_navigator', 'bt_navigator'),
    ]
    with open(os.path.join(
        simulation_share, 'urdf', 'turtlebot3_burger.urdf',
    ), encoding='utf-8') as description_file:
        robot_description = description_file.read()

    namespace = LaunchConfiguration('namespace')
    configured_nav2_params = ParameterFile(RewrittenYaml(
        source_file=nav2_params, root_key=namespace,
        # Costmap nodes have their own subnamespace; both scan sources must
        # subscribe to the robot's sensor topic rather than costmap/scan.
        param_rewrites={'topic': PathJoinSubstitution(['/', namespace, 'scan'])},
        convert_types=True,
    ))
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
                '-allow_renaming', 'false',
                '-string', ET.tostring(sdf.getroot(), encoding='unicode'),
                '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                '-z', LaunchConfiguration('z'), '-Y', LaunchConfiguration('yaw'),
            ],
        ),
        GroupAction([
            PushRosNamespace(namespace),
            *[
                Node(
                    package=package, executable=name, name=name,
                    parameters=[configured_nav2_params, {'use_sim_time': True}],
                    remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
                    output='screen',
                )
                for package, name in navigation_nodes
            ],
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                parameters=[{
                    'use_sim_time': True, 'autostart': True,
                    'node_names': [name for _, name in navigation_nodes],
                }],
                output='screen',
            ),
        ]),
    ])
