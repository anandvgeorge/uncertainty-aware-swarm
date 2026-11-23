# Docker Architecture

## 1. Overview

The project uses Docker to provide a reproducible ROS 2 and Gazebo development environment, independent of the host OS installation.

| Component | Version |
|---|---|
| Host OS | Ubuntu 22.04 |
| Container OS | Ubuntu 24.04 |
| ROS 2 | Jazzy |
| Gazebo | Harmonic |
| C++ | C++17 |
| Container orchestration | Docker Compose |

The host does not require a ROS installation.

## 2. Container Architecture

The system consists of three containers with distinct responsibilities.

| Container | Responsibility | Lifecycle |
|---|---|---|
| `builder` | Compile ROS 2 packages, run tests, and generate build artifacts | On demand |
| `autonomy` | Execute the compiled ROS 2 autonomy stack | Long-running |
| `gazebo` | Provide the Gazebo Harmonic environment | Long-running |

The builder and autonomy containers use compatible ROS environments. The builder contains development dependencies, while autonomy contains runtime dependencies.

A single Gazebo server will eventually host multiple simulated robots. Individual robot containers are not required.

## 3. Workspace and Storage

The Git repository remains on the host. The ROS workspace exists inside the containers.

### Host repository

```text
uncertainty-aware-swarm/
├── docker/
├── docs/
├── scripts/
├── src/
├── tests/
├── docker-compose.yml
└── README.md
```

### Builder workspace

```text
/workspace/ros2_ws/
├── src/       # Bind-mounted from host
├── build/     # Docker named volume
├── install/   # Docker named volume
└── log/       # Docker named volume
```

The builder container uses the following mounts:

| Host or Docker volume | Container path | Purpose |
|---|---|---|
| `./src` | `/workspace/ros2_ws/src` | Source code |
| `ros_build` | `/workspace/ros2_ws/build` | Build artifacts |
| `ros_install` | `/workspace/ros2_ws/install` | Installed packages |
| `ros_log` | `/workspace/ros2_ws/log` | Build logs |

Build artifacts persist through Docker named volumes and are not stored in the Git repository.

The autonomy container mounts the install volume read-only. It does not require access to the source repository or build tools.

## 4. Build and Runtime Workflow

Building and execution are separate operations.

```text
Host source changes
       |
       v
Builder container
       |
       v
    colcon build
       |
       v
Persistent install volume
       |
       v
Autonomy container
       |
       v
Execute ROS 2 stack
```

- On Compose startup, the builder runs `docker/build-workspace.sh` to execute `colcon build`, then exits.
- Autonomy waits for the build to complete successfully before starting.
- Colcon handles incremental builds.
- The autonomy container executes the packages available in the install volume.
- Source changes require rebuilding before the updated stack is executed.

The existence of build artifacts alone is not considered proof that they are up to date.

Interactive Bash shells in builder and autonomy source ROS 2 and the workspace overlay when available. Use plain `colcon build`: symlink installs may reference source/build paths unavailable in autonomy.

## 5. Docker Compose Configuration

Docker Compose orchestrates the three services.

### Builder

- Builds from `docker/Dockerfile.builder`.
- Uses the repository root as the build context.
- Mounts source code and persistent build, install, and log volumes.
- Uses host networking.
- Receives a configurable `ROS_DOMAIN_ID`, defaulting to `1`.

### Autonomy

- Builds from `docker/Dockerfile.autonomy`.
- Uses host networking.
- Mounts the install volume read-only.
- Receives the same configurable `ROS_DOMAIN_ID`.
- Depends on Gazebo starting and the builder completing successfully.
- Runs `docker/start-autonomy.sh`, which sources ROS and the workspace before launching `swarm_bringup swarm.launch.py` (one shared clock bridge and three robot/Nav2 instances).
- Mounts `config/` read-only at `/workspace/config` for bridge configuration.

### Gazebo

- Builds from `docker/Dockerfile.gazebo`.
- Uses host networking.
- Receives the host `DISPLAY` and X11 authorization configuration.
- Mounts the X11 socket and Xauthority file.
- Maps `/dev/dri` for GPU access and launches the installed `swarm_bringup/worlds/empty.sdf`.

Compose starts Gazebo, one clock bridge, and three TurtleBot3 Burgers named `robot1`, `robot2`, and `robot3` automatically.

### Named volumes

The following Docker named volumes are declared:

```yaml
volumes:
  ros_build:
  ros_install:
  ros_log:
```

These volumes persist independently of the lifecycle of individual containers.

## 6. Networking

Docker host networking is used for all three containers.

- Containers share the host network namespace and IP address.
- No macvlan or ipvlan configuration is required.
- ROS 2 DDS discovery can use the host network directly.
- No Docker port mapping is required.
- Port conflicts must be avoided.
- `ROS_DOMAIN_ID` is configurable through the environment.

The default domain ID is `1` when `ROS_DOMAIN_ID` is not set.

## 7. GUI Configuration

The Gazebo container receives the host display configuration through environment variables and mounted X11 resources.

| Variable or mount | Purpose |
|---|---|
| `DISPLAY` | Host display identifier |
| `XAUTHORITY` | X11 authorization file inside the container |
| `QT_X11_NO_MITSHM` | Disables Qt MIT-SHM usage |
| `/tmp/.X11-unix` | X11 Unix socket |
| Host Xauthority file | Read-only mount at `/tmp/.Xauthority` |

The Compose configuration uses X11 forwarding to provide GUI access from the container.

The host's Xauthority file must exist and be accessible to Docker when starting the Gazebo service.

## 8. Environment Commands

Build all images:

```bash
docker compose build
```

Start the services:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps -a
```

View service logs:

```bash
docker compose logs
```

Open a shell in a service:

```bash
docker compose run --rm builder bash
docker compose exec autonomy bash
docker compose exec gazebo bash
```

Verify ROS 2 communication in two separate terminals:

```bash
# Terminal 1
docker compose exec autonomy bash
ros2 topic pub /test_topic std_msgs/msg/String "{data: 'hello'}" --rate 1
```

```bash
# Terminal 2
docker compose exec autonomy bash
ros2 topic echo /test_topic std_msgs/msg/String
```

Expect repeated `hello` messages. The empty-workspace build and this communication check were verified for M0.3.

Stop the services:

```bash
docker compose down
```

The named volumes are retained when the containers are stopped or removed. To remove the named volumes as well:

```bash
docker compose down -v
```

**Warning:** `docker compose down -v` deletes the persistent build, install, and log volumes.

## 9. ROS-Gazebo Integration

ROS-Gazebo integration is not part of M0.2.

`swarm.launch.py`, started by `docker/start-autonomy.sh`, includes `single_robot.launch.py` for each robot. The reusable robot launch reads the installed `turtlebot3_gazebo/params/turtlebot3_burger_bridge.yaml`, prefixes its mappings with the robot namespace, and starts the robot bridge using those topic arguments. Only the first instance starts the global `/clock` bridge. The earlier `config/ros_gz_bridge.yaml` clock-only configuration remains in the repository as the M0.4 baseline.

After changing the startup script, reset the runtime services for a fresh world:

```bash
docker compose stop autonomy gazebo
docker compose up -d
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /clock'
```

Expect advancing timestamps while simulation is running. ROS nodes using simulation time must set `use_sim_time: true`.

The intended architecture is:

```text
Autonomy Container             Gazebo Container
+--------------------+         +--------------------+
| ROS 2 Jazzy        |         | Gazebo Harmonic    |
|                    |         |                    |
| Autonomy Nodes     |         | Gazebo Server      |
| ros_gz_bridge      |<------->|                    |
+--------------------+         +--------------------+
          Shared Host Network
```

Robot spawning, command/state/sensor bridges, TF, ground-truth odometry, and map-free Nav2 bringup are implemented independently for three robots.

### Single-robot spawning

`swarm_bringup` installs the official `turtlebot3_gazebo` model assets into the shared install volume. Gazebo mounts that volume read-only and uses `GZ_SIM_RESOURCE_PATH` to resolve the model's `model://` mesh URIs. Gazebo waits for the builder to finish before starting. The project-owned `worlds/empty.sdf` supplies physics, entity creation, scene broadcasting, the IMU system, and the Ogre2 sensor rendering system. It is installed into the shared volume alongside the launch files.

`single_robot.launch.py` loads the official Burger SDF, redirects differential-drive odometry/TF to each robot's Gazebo `wheel_odom` and `wheel_tf` topics, adds Gazebo's built-in `OdometryPublisher` system, and passes the resulting SDF string to `ros_gz_sim create` against world `empty`. The source model assets remain unchanged. The spawner waits for the world's creation service. The default entity is `robot1`, at `(0, 0, 0.01)` metres with zero yaw. The robot bridge and robot-state publisher stay running after the spawner exits. The robot namespace defaults to its entity name, giving `/robot1/cmd_vel`, `/robot1/odom`, `/robot1/joint_states`, `/robot1/tf`, and `/robot1/tf_static`. TF frame IDs remain local names such as `odom` and `base_footprint`, with TF topics isolated per namespace.

Start from the repository root with valid `DISPLAY` and `XAUTHORITY`:

```bash
docker compose up --build -d
docker compose logs autonomy
docker compose exec gazebo gz model --list
docker compose exec gazebo gz model -m robot1 --pose
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /clock'
```

Expect three successful entity creations, `robot1`, `robot2`, and `robot3` alongside `ground_plane`, and advancing clock timestamps. In the Gazebo GUI, select `robot1` in the entity tree and move the camera to it to inspect the robot at the origin.

After editing package source, rebuild and reset both runtime services:

```bash
docker compose run --rm --no-deps builder
docker compose stop autonomy gazebo
docker compose up -d
```

The robot name is fixed and automatic renaming is disabled. Restarting only autonomy while the same Gazebo world is running attempts to spawn an existing name and is rejected; reset both runtime services as above for a fresh world. Docker volumes are retained.

The reusable single-robot launch exposes `world`, `robot_name`, `namespace`, `start_clock_bridge`, `x`, `y`, `z`, and `yaw` arguments. Each model's IMU, lidar, command, joint-state, and odometry/TF topic names receive the robot namespace before spawning. The bridge applies the same namespace to the upstream YAML mappings. The official Burger URDF supplies robot-state publishing.

The robot accepts `geometry_msgs/msg/TwistStamped` commands. Test at low speed while the simulation is running, then explicitly send zero velocity to stop:

```bash
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic pub --once -w 1 /robot1/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.1}}}"'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /robot1/odom --once'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic pub --once -w 1 /robot1/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}"'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /robot1/joint_states --once'
```

Navigation odometry and `odom → base_footprint` come from Gazebo's `OdometryPublisher`, configured in `config/ground_truth_odometry.sdf`. The differential-drive plugin retains wheel odometry on separate Gazebo topics. Each robot bridge forwards its Gazebo ground-truth odometry and TF into the same ROS namespace. IMU and lidar world systems are enabled in the project-owned world.

Validation: the workspace built successfully; Compose startup reported successful entity creation; Gazebo listed `ground_plane` and `robot1`; the robot settled near `(0, 0, 0.01)`; mesh files were present at the configured resource path; ROS received simulation clock messages. The command/state integration check moved the robot over 5 cm through `/robot1/cmd_vel`, received both wheel joint states and odometry plus wheel TF, verified one clock publisher, and stopped the robot with zero velocity. GUI appearance has not been visually inspected. The installed model emits SDF extension warnings for `gz_frame_id`; these did not prevent spawning.

### Three-robot bringup

The existing Compose startup invokes `swarm.launch.py`, which reuses the single-robot launch three times. Default spawn poses are defined in that launch file:

| Robot | Spawn XY (m) | Goal action |
|---|---|---|
| `robot1` | `(0, 0)` | `/robot1/navigate_to_pose` |
| `robot2` | `(0, 2)` | `/robot2/navigate_to_pose` |
| `robot3` | `(0, -2)` | `/robot3/navigate_to_pose` |

All spawn at `z = 0.01` m with zero yaw. Each instance has its own Gazebo and ROS sensor/command/state topics, ground-truth publisher, robot-state publisher, IMU frame alias, costmaps, Nav2 servers, and lifecycle manager. TF frame IDs are local to each instance's `/<robot>/tf` and `/<robot>/tf_static` topics. Each `odom` coordinate system aligns with the same Gazebo world coordinates, so a goal at `(1.5, 2.0)` for `robot2` is a world position rather than an offset from its spawn point.

One clock bridge is started by `robot1`; the other two instances set `start_clock_bridge:=false`. Isolated Gazebo topic names ensure that one robot's velocity commands cannot drive another robot.

Inside the autonomy shell, submit separate goals:

```bash
ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: odom}, pose: {position: {x: 1.0, y: 0.5}, orientation: {w: 1.0}}}}'
ros2 action send_goal /robot2/navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: odom}, pose: {position: {x: 1.5, y: 2.0}, orientation: {w: 1.0}}}}'
ros2 action send_goal /robot3/navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: odom}, pose: {position: {x: 0.75, y: -2.5}, orientation: {w: 1.0}}}}'
```

These CLI commands wait for each result. Use separate terminals or asynchronous action clients for concurrent goals. After a fresh startup, three action clients submitted the above goals concurrently, and all three returned `SUCCEEDED` with `error_code: 0`.

| Robot | Measured final XY (m) | Goal error (m) |
|---|---|---|
| `robot1` | `(0.9163, 0.4384)` | `0.1039` |
| `robot2` | `(1.4037, 2.0000)` | `0.0963` |
| `robot3` | `(0.6894, -2.4340)` | `0.0896` |

For each robot, validation checked fresh IMU/lidar/wheel-state/odometry timestamps, 360 lidar samples, wheel positions and velocities, complete TF to the lidar and actual IMU message frame, active Nav2 lifecycle state, and one odometry/scan publisher per namespace. All robots stopped after their goals; `/clock` had exactly one publisher.

### Map-free Nav2 navigation

`single_robot.launch.py` starts the stock Nav2 planner, controller, behavior server, BT navigator, and lifecycle manager under each robot's namespace. The lifecycle manager activates the servers automatically as the simulation and TF become available. `config/nav2.yaml` configures NavFn planning and the Regulated Pure Pursuit controller for the Burger, with a 0.15 m robot radius and 0.15 m/s desired forward velocity.

The global planning frame is `odom`, aligned with Gazebo world coordinates. The built-in ground-truth plugin publishes pose, body-frame velocity, and the sole Gazebo odometry transform on each robot's namespaced `tf` topic at 30 Hz with zero added noise. The ROS transform chain is `odom → base_footprint → base_link → sensor links`. Wheel joint measurements remain available separately.

The global costmap is a fixed 20 × 20 m region with origin `(-10, -10)` and 0.05 m resolution. The local costmap is a 3 × 3 m rolling window. Both use lidar obstacle and inflation layers. Unobserved space is initialized as free, so this is a baseline for the empty world and sensor-visible obstacles. Goals and routes must fit inside the configured global costmap. Enlarging the world experiment requires adjusting these bounds. This configuration starts without a map server, AMCL, or a `map → odom` transform.

Start with the existing Compose entry point, then send a goal through Nav2's action interface:

```bash
docker compose up --build -d
docker compose exec autonomy bash
```

Inside the autonomy shell:

```bash
ros2 lifecycle get /robot1/bt_navigator
ros2 action send_goal /robot1/navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: odom}, pose: {position: {x: 1.0, y: 0.5}, orientation: {w: 1.0}}}}' \
  --feedback
```

Wait for lifecycle state `active` before sending a goal. Expect the action result to report `SUCCEEDED` with `error_code: 0`. Goal positions use metres in `odom`; orientation uses a quaternion. Applications can use a standard ROS 2 `NavigateToPose` action client to submit, monitor, and cancel goals.

Direct `/robot1/cmd_vel` commands still use `TwistStamped`. Finish or cancel an active navigation action before taking direct velocity control so that the custom controller and Nav2 do not command the robot simultaneously.

Fresh-start validation succeeded for the goal `(1.0, 0.5)` with final ground-truth position approximately `(0.954, 0.579)` and zero final velocity. Nav2 reported action status `SUCCEEDED` and `error_code: 0`. The physical Gazebo model pose matched the reported odometry. IMU, lidar, wheel states, and odometry continued throughout navigation, and each robot's Gazebo odometry and TF topic had one publisher. A temporary box blocking the direct route was marked as occupied in both costmaps, and the CLI goal command succeeded around it. The box was removed after testing.

### Sensor streams

The examples below use `robot1`; the same topics are available under `/robot2` and `/robot3`.

| ROS topic | Message type | Measurements | Configured simulation rate |
|---|---|---|---|
| `/robot1/imu` | `sensor_msgs/msg/Imu` | Orientation, angular velocity, linear acceleration | 200 Hz |
| `/robot1/joint_states` | `sensor_msgs/msg/JointState` | Left/right wheel joint positions in radians and velocities in radians/second | Upstream plugin default |
| `/robot1/scan` | `sensor_msgs/msg/LaserScan` | 360 lidar ranges in metres, frame `base_scan` | 5 Hz |

Wheel joint states provide simulated encoder-style measurements. Encoder tick quantization is a separate model that has not been added. Gazebo ground-truth odometry supplies `/robot1/odom` alongside these readings. Message rates above use simulation time, so wall-clock rates depend on simulation performance.

The existing launch publishes an identity transform from `imu_link` to the Gazebo IMU message frame `<robot_name>/imu_link/tb3_imu` on the robot's `tf_static` topic. The upstream model and bridge configuration remain the source of the sensor data. This alias connects IMU measurements to the URDF transform tree.

Check actual sensor messages from an autonomy shell:

```bash
ros2 topic echo /robot1/imu --once --qos-reliability best_effort
ros2 topic echo /robot1/joint_states --once --qos-reliability best_effort
ros2 topic echo /robot1/scan --once --qos-reliability best_effort
```

The IMU should measure approximately 9.8 m/s² acceleration magnitude at rest and respond to robot rotation. Wheel positions and velocities should respond to motion commands. In an empty scene, lidar may report infinite ranges for rays without returns, and finite ranges where rays meet the ground or robot geometry. Place an obstacle in Gazebo to inspect nearby returns.

Sensor validation confirmed advancing timestamps on all three streams, both wheel position/velocity arrays, and IMU acceleration magnitude near gravity. A rotation command produced approximately 0.30 rad/s IMU yaw rate and changing wheel angles. A temporary target was used to check lidar distance, then removed. Gazebo may print the known `gz_frame_id` schema warnings while retaining the sensor frame tags.

## 10. Design Principles

- Host-independent development environment.
- Reproducible container builds.
- Source code managed through Git.
- Persistent build artifacts.
- Separation of build-time and runtime dependencies.
- Runtime container does not require compilation tools.
- No ROS installation required on the host.
- No individual containers per simulated robot.
- Simple networking without physical NIC dependencies.
