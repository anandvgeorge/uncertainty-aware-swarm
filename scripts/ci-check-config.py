#!/usr/bin/env python3
"""Static configuration checks; requires Python 3, PyYAML and Docker Compose.

Does not import ROS, launch processes, or require a Docker daemon/display.
Runtime bridge mappings and namespace isolation belong in the smoke test.
"""

import ast
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently discarding values."""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in keys:
                raise ValueError(f"duplicate YAML key {key!r} at {key_node.start_mark}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_repository(root):
    yaml_paths = sorted(
        path for directory in (root / 'src', root / 'config', root / '.github')
        for path in directory.rglob('*') if path.suffix in {'.yaml', '.yml'}
    ) + sorted(root.glob('*compose*.y*ml'))
    documents = {}
    for path in yaml_paths:
        documents[path] = yaml.load(path.read_text(), Loader=UniqueKeyLoader)
        print(f"PASS YAML: {path.relative_to(root)}")

    for path in sorted((root / 'src').rglob('*')):
        if path.suffix == '.py':
            # compile checks syntax without importing ROS or writing __pycache__.
            compile(path.read_text(), str(path), 'exec')
            print(f"PASS Python syntax: {path.relative_to(root)}")
        elif path.suffix in {'.xml', '.sdf', '.urdf'}:
            ET.parse(path)
            print(f"PASS XML: {path.relative_to(root)}")

    package = root / 'src/swarm_bringup'
    for relative in ('package.xml', 'launch/swarm.launch.py',
                     'launch/single_robot.launch.py', 'config/nav2.yaml',
                     'config/ground_truth_odometry.sdf', 'worlds/empty.sdf'):
        require((package / relative).is_file(), f"Missing bringup resource: {relative}")

    # This baseline deliberately declares its three spawn poses as a literal
    # list. If that representation changes, update this static contract too.
    tree = ast.parse((package / 'launch/swarm.launch.py').read_text())
    declarations = [node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'robots'
                            for target in node.targets)]
    require(len(declarations) == 1, 'Expected one literal robots declaration')
    robots = ast.literal_eval(declarations[0])
    require(len(robots) == 3, 'The baseline requires three robots')
    names, poses = set(), set()
    for name, x, y in robots:
        require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name),
                f'Invalid robot name/namespace: {name!r}')
        require(name not in names, f'Duplicate robot name/namespace: {name}')
        names.add(name)
        pose = (float(x), float(y))
        require(all(math.isfinite(value) for value in pose), f'Invalid pose: {pose}')
        require(pose not in poses, f'Duplicate robot spawn position: {pose}')
        poses.add(pose)
    print('PASS three unique robot declarations and spawn positions')

    bridge = documents[root / 'config/ros_gz_bridge.yaml']
    require(bridge == [{
        'ros_topic_name': '/clock', 'gz_topic_name': '/clock',
        'ros_type_name': 'rosgraph_msgs/msg/Clock', 'gz_type_name': 'gz.msgs.Clock',
        'direction': 'GZ_TO_ROS',
    }], 'Shared bridge configuration must contain the single Gazebo-to-ROS clock mapping')

    nav2 = documents[package / 'config/nav2.yaml']
    odometry = ET.parse(package / 'config/ground_truth_odometry.sdf').getroot()
    for node in ('bt_navigator', 'local_costmap', 'global_costmap'):
        config = nav2[node] if node == 'bt_navigator' else nav2[node][node]
        params = config['ros__parameters']
        require(params['global_frame'] == odometry.findtext('odom_frame'),
                f'{node}: global frame must match ground-truth odometry')
        require(params['robot_base_frame'] == odometry.findtext('robot_base_frame'),
                f'{node}: base frame must match ground-truth odometry')
        if node != 'bt_navigator':
            require(params['use_sim_time'] is True, f'{node}: use_sim_time must be true')
            require(params['obstacle_layer']['scan']['topic'] == 'scan',
                    f'{node}: scan topic must remain relative for per-robot rewriting')
    print('PASS shared clock mapping and Nav2/odometry frame consistency')

    # Supply desktop placeholders only for interpolation. `compose config`
    # validates the model without checking devices or starting any services.
    env = dict(os.environ, DISPLAY=':0', XAUTHORITY='/tmp/swarm-ci.Xauthority',
               ROS_DOMAIN_ID='1')
    result = subprocess.run(
        ['docker', 'compose', '--project-directory', str(root),
         '-f', str(root / 'docker-compose.yml'), 'config', '--format', 'json'],
        env=env, check=True, capture_output=True, text=True,
    )
    compose = json.loads(result.stdout)
    require(set(compose['services']) == {'builder', 'autonomy', 'gazebo'},
            'Expected builder, autonomy and gazebo services')
    for name, service in compose['services'].items():
        build = service['build']
        require((Path(build['context']) / build['dockerfile']).is_file(),
                f'{name}: Dockerfile does not exist')
        for volume in service.get('volumes', []):
            if volume['type'] == 'bind':
                source = Path(volume['source'])
                if source.is_relative_to(root):
                    require(source.exists(), f'{name}: missing repository mount {source}')
    print('PASS resolved Compose configuration, Dockerfiles and repository mounts')


if __name__ == '__main__':
    try:
        check_repository(Path(__file__).resolve().parents[1])
    except (ValueError, KeyError, TypeError, OSError, SyntaxError,
            ET.ParseError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stderr, file=sys.stderr)
        sys.exit(1)
