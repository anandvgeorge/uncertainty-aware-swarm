#!/usr/bin/env python3
"""Observe the three-robot baseline without sending motion or navigation goals."""

import argparse
import math
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Imu, JointState, LaserScan
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformException


class SmokeTest(Node):
    def __init__(self):
        super().__init__('ci_smoke_test')
        self.streams = {}
        self.buffers = {}
        self.states = {}
        self.state_clients = {}
        self.actions = {}
        self.pending = {}
        self.errors = set()
        self.create_subscription(Clock, '/clock', self.clock, qos_profile_sensor_data)
        static_qos = QoSProfile(depth=100, reliability=ReliabilityPolicy.RELIABLE,
                                durability=DurabilityPolicy.TRANSIENT_LOCAL)
        for robot in ('robot1', 'robot2', 'robot3'):
            self.buffers[robot] = Buffer()
            for topic, message in (('odom', Odometry), ('imu', Imu),
                                   ('scan', LaserScan), ('joint_states', JointState)):
                name = f'/{robot}/{topic}'
                self.create_subscription(
                    message, name, lambda msg, key=name: self.sample(key, msg),
                    qos_profile_sensor_data,
                )
            self.create_subscription(
                TFMessage, f'/{robot}/tf',
                lambda msg, key=robot: self.transforms(key, msg, False), qos_profile_sensor_data,
            )
            self.create_subscription(
                TFMessage, f'/{robot}/tf_static',
                lambda msg, key=robot: self.transforms(key, msg, True), static_qos,
            )
            for server in ('controller_server', 'planner_server', 'behavior_server', 'bt_navigator'):
                name = f'/{robot}/{server}/get_state'
                self.state_clients[name] = self.create_client(GetState, name)
            self.actions[robot] = ActionClient(self, NavigateToPose, f'/{robot}/navigate_to_pose')

    def record(self, name, stamp, message):
        value = stamp.sec * 1_000_000_000 + stamp.nanosec
        previous = self.streams.get(name)
        advances = 0 if previous is None else previous[0] + (value > previous[1])
        advanced_at = (time.monotonic() if previous is None or value > previous[1]
                       else previous[2])
        self.streams[name] = (advances, value, advanced_at, message)

    def clock(self, msg):
        self.record('/clock', msg.clock, msg)

    def sample(self, name, msg):
        self.record(name, msg.header.stamp, msg)
        if isinstance(msg, LaserScan):
            valid = bool(msg.ranges) and msg.range_max > msg.range_min
            valid = valid and all(not math.isnan(value) for value in msg.ranges)
        elif isinstance(msg, JointState):
            valid = len(msg.name) >= 2 and len(msg.position) == len(msg.name)
        elif isinstance(msg, Imu):
            valid = all(math.isfinite(value) for value in (
                msg.linear_acceleration.x, msg.linear_acceleration.y,
                msg.linear_acceleration.z, msg.angular_velocity.z))
        else:
            valid = (msg.header.frame_id == 'odom' and msg.child_frame_id == 'base_footprint'
                     and all(math.isfinite(value) for value in (
                         msg.pose.pose.position.x, msg.pose.pose.position.y)))
        if not valid:
            self.errors.add(f'invalid message data on {name}')

    def transforms(self, robot, msg, static):
        for transform in msg.transforms:
            if static:
                self.buffers[robot].set_transform_static(transform, 'ci')
            else:
                self.buffers[robot].set_transform(transform, 'ci')

    def poll_states(self):
        for name, client in self.state_clients.items():
            future = self.pending.get(name)
            if future is not None and future.done():
                self.states[name] = (future.result().current_state.id, time.monotonic())
                del self.pending[name]
            if name not in self.pending and client.service_is_ready():
                self.pending[name] = client.call_async(GetState.Request())

    def problems(self):
        now = time.monotonic()
        problems = list(self.errors)
        expected = ['/clock'] + [f'/{robot}/{topic}' for robot in self.buffers
                                 for topic in ('odom', 'imu', 'scan', 'joint_states')]
        for name in expected:
            sample = self.streams.get(name)
            if sample is None or sample[0] < 2 or now - sample[2] > 10:
                problems.append(f'{name}: need fresh messages with advancing timestamps')
            publishers = self.get_publishers_info_by_topic(name)
            if len(publishers) != 1:
                problems.append(f'{name}: expected one publisher, found {len(publishers)}')
            if name != '/clock':
                namespace = '/' + name.split('/')[1]
                if any(endpoint.node_namespace != namespace for endpoint in publishers):
                    problems.append(f'{name}: publisher outside robot namespace')
                if any(endpoint.node_namespace.startswith('/robot')
                       and endpoint.node_namespace.split('/')[1] != namespace[1:]
                       for endpoint in self.get_subscriptions_info_by_topic(name)):
                    problems.append(f'{name}: cross-robot subscriber')
        for name, client in self.state_clients.items():
            state, seen = self.states.get(name, (None, 0))
            if state != 3 or now - seen > 10:
                problems.append(f'{name}: lifecycle node is not active')
        for robot, buffer in self.buffers.items():
            if not self.actions[robot].server_is_ready():
                problems.append(f'{robot}: NavigateToPose server unavailable')
            frames = ['base_footprint', 'base_link', 'base_scan']
            imu = self.streams.get(f'/{robot}/imu')
            if imu:
                frames.append(imu[3].header.frame_id)
            for frame in frames:
                try:
                    transform = buffer.lookup_transform('odom', frame, Time(), Duration())
                    clock = self.streams.get('/clock')
                    stamp = transform.header.stamp
                    age = clock[1] - (stamp.sec * 1_000_000_000 + stamp.nanosec) if clock else 0
                    # Clock and TF arrive independently; tolerate small skew.
                    if not -1_000_000_000 <= age <= 5_000_000_000:
                        problems.append(f'{robot}: stale transform odom -> {frame}')
                    if frame == 'base_footprint':
                        expected_y = {'robot1': 0, 'robot2': 2, 'robot3': -2}[robot]
                        position = transform.transform.translation
                        if abs(position.x) > 0.25 or abs(position.y - expected_y) > 0.25:
                            problems.append(f'{robot}: TF does not match its spawn position')
                except TransformException:
                    problems.append(f'{robot}: missing transform odom -> {frame}')
        # Ground-truth positions distinguish the three otherwise identical TF trees.
        for robot, expected_y in (('robot1', 0), ('robot2', 2), ('robot3', -2)):
            odom = self.streams.get(f'/{robot}/odom')
            if odom:
                pose = odom[3].pose.pose.position
                if abs(pose.x) > 0.25 or abs(pose.y - expected_y) > 0.25:
                    problems.append(f'{robot}: odometry does not match its spawn position')
        return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=180,
                        help='Readiness deadline in wall-clock seconds (default: 180)')
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be finite and positive')
    rclpy.init()
    node = SmokeTest()
    deadline = time.monotonic() + args.timeout
    stable_since = None
    next_report = 0
    next_progress = 0
    problems = ['No observations yet']
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            now = time.monotonic()
            if now < next_report:
                continue
            next_report = now + 1
            node.poll_states()
            problems = node.problems()
            if problems:
                stable_since = None
                if now >= next_progress:
                    print('Waiting for readiness:\n- ' + '\n- '.join(problems))
                    next_progress = now + 15
            else:
                stable_since = stable_since or now
                if now - stable_since >= 5:
                    print('PASS: clock, sensors, odometry, per-robot TF, lifecycle and action readiness')
                    print('PASS: namespace endpoints and distinct spawn poses; stable for 5 seconds')
                    return 0
        print('FAIL: readiness deadline exceeded:\n- ' + '\n- '.join(problems))
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
