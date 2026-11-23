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
- Runs `docker/start-autonomy.sh`, which sources ROS and the workspace before launching `swarm_bringup single_robot.launch.py` (clock bridge and one robot).
- Mounts `config/` read-only at `/workspace/config` for bridge configuration.

### Gazebo

- Builds from `docker/Dockerfile.gazebo`.
- Uses host networking.
- Receives the host `DISPLAY` and X11 authorization configuration.
- Mounts the X11 socket and Xauthority file.
- Maps `/dev/dri` for GPU access and launches the installed `swarm_bringup/worlds/empty.sdf`.

Compose starts Gazebo, the clock bridge, and one TurtleBot3 Burger named `robot1` automatically.

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

`single_robot.launch.py`, started by `docker/start-autonomy.sh`, loads the installed `turtlebot3_gazebo/params/turtlebot3_burger_bridge.yaml` directly. This provides the robot command/state/sensor mappings and one global `/clock` bridge. The earlier `config/ros_gz_bridge.yaml` clock-only configuration remains in the repository as the M0.4 baseline.

After changing the startup script, restart autonomy:

```bash
docker compose restart autonomy
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

Robot spawning, namespaced command/state bridges, and robot-state publishing are implemented. Ground-truth localization and Nav2 bringup are subsequent work.

### Single-robot spawning

`swarm_bringup` installs the official `turtlebot3_gazebo` model assets into the shared install volume. Gazebo mounts that volume read-only and uses `GZ_SIM_RESOURCE_PATH` to resolve the model's `model://` mesh URIs. Gazebo waits for the builder to finish before starting. The project-owned `worlds/empty.sdf` supplies physics, entity creation, scene broadcasting, the IMU system, and the Ogre2 sensor rendering system. It is installed into the shared volume alongside the launch files.

Autonomy launches `single_robot.launch.py`. It passes the official `models/turtlebot3_burger/model.sdf` directly to `ros_gz_sim create` against world `empty`. The spawner waits for the world's creation service. The default entity is `robot1`, at `(0, 0, 0.01)` metres with zero yaw. The upstream bridge and robot-state publisher stay running after the spawner exits. The robot namespace defaults to its entity name, giving `/robot1/cmd_vel`, `/robot1/odom`, `/robot1/joint_states`, `/robot1/tf`, and `/robot1/tf_static`. TF frame IDs remain local names such as `odom` and `base_footprint`, with TF topics isolated per namespace.

Start from the repository root with valid `DISPLAY` and `XAUTHORITY`:

```bash
docker compose up --build -d
docker compose logs autonomy
docker compose exec gazebo gz model --list
docker compose exec gazebo gz model -m robot1 --pose
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /clock'
```

Expect `Entity creation successful`, one `robot1` alongside `ground_plane`, and advancing clock timestamps. In the Gazebo GUI, select `robot1` in the entity tree and move the camera to it to inspect the robot at the origin.

After editing package source, rebuild and reset both runtime services:

```bash
docker compose run --rm --no-deps builder
docker compose stop autonomy gazebo
docker compose up -d
```

The robot name is fixed and automatic renaming is disabled. Restarting only autonomy while the same Gazebo world is running attempts to spawn an existing name and is rejected; reset both runtime services as above for a fresh world. Docker volumes are retained.

The launch exposes `world`, `robot_name`, `namespace`, `x`, `y`, `z`, and `yaw` arguments. This bringup spawns one robot. The official model uses global Gazebo topics, which the supplied YAML bridges into the ROS namespace. The bridge's clock output is remapped to `/clock`. The official Burger URDF supplies robot-state publishing.

The robot accepts `geometry_msgs/msg/TwistStamped` commands. Test at low speed while the simulation is running, then explicitly send zero velocity to stop:

```bash
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic pub --once -w 1 /robot1/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.1}}}"'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /robot1/odom --once'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic pub --once -w 1 /robot1/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}"'
docker compose exec autonomy bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic echo /robot1/joint_states --once'
```

Odometry comes from the Gazebo differential-drive plugin. Ground-truth localization and Nav2 goal navigation remain pending. IMU and lidar world systems are enabled in the project-owned world.

Validation: the workspace built successfully; Compose startup reported successful entity creation; Gazebo listed `ground_plane` and `robot1`; the robot settled near `(0, 0, 0.01)`; mesh files were present at the configured resource path; ROS received simulation clock messages. The command/state integration check moved the robot over 5 cm through `/robot1/cmd_vel`, received both wheel joint states and odometry plus wheel TF, verified one clock publisher, and stopped the robot with zero velocity. GUI appearance has not been visually inspected. The installed model emits SDF extension warnings for `gz_frame_id`; these did not prevent spawning.

### Sensor streams

| ROS topic | Message type | Measurements | Configured simulation rate |
|---|---|---|---|
| `/robot1/imu` | `sensor_msgs/msg/Imu` | Orientation, angular velocity, linear acceleration | 200 Hz |
| `/robot1/joint_states` | `sensor_msgs/msg/JointState` | Left/right wheel joint positions in radians and velocities in radians/second | Upstream plugin default |
| `/robot1/scan` | `sensor_msgs/msg/LaserScan` | 360 lidar ranges in metres, frame `base_scan` | 5 Hz |

Wheel joint states provide simulated encoder-style measurements. Encoder tick quantization is a separate model that has not been added. The differential-drive plugin supplies `/robot1/odom` alongside these readings. Message rates above use simulation time, so wall-clock rates depend on simulation performance.

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
