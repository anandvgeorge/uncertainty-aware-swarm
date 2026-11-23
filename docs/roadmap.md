# Project Roadmap

## Phase 0: Working Multi-Robot Nav2 Baseline

Build up to three independently navigating robots in one shared world using stock Nav2 and Gazebo ground-truth localization. Keep the existing Docker architecture; defer custom navigation algorithms.

**Exit condition:** Three robots reach independent goals from a reproducible configuration. Validate each milestone before proceeding.

### M0.1: GitHub Repository Foundation

Establish the repository, branching strategy, and development workflow.

### M0.2: Docker Environment

Establish a reproducible containerized development and runtime environment.

**Technology stack:**
- Host OS: Ubuntu 22.04
- Container OS: Ubuntu 24.04
- ROS 2: Jazzy
- Gazebo: Harmonic
- C++: C++17
- Container orchestration: Docker Compose

**Container architecture:**

| Service | Responsibility |
|---|---|
| `builder` | Compile ROS 2 packages, run tests, and generate build artifacts |
| `autonomy` | Execute the compiled ROS 2 autonomy stack |
| `gazebo` | Provide the Gazebo Harmonic environment |

**Implementation and validation status:**

| Issue | Scope | Status |
|---|---|---|
| #7 | Define Docker project architecture | Validated |
| #8 | Create ROS 2 Jazzy development container | Validated |
| #9 | Create Gazebo Harmonic container | Validated |
| #11 | Configure Docker Compose orchestration | Validated |
| #12 | Configure workspace and persistent volumes | Validated |
| #13 | Configure GUI and development experience | Validated |
| #14 | Document environment setup and validation | In progress |

ROS-Gazebo integration was removed from M0.2 and is addressed in M0.4.

**M0.2 completion criteria:**
- Docker images build successfully.
- All three services start successfully.
- ROS 2 development and runtime environments are available.
- Workspace mounts and persistent volumes behave as expected.
- GUI access is configured and validated.
- Environment setup and validation instructions are documented.

### M0.3: ROS 2 Workspace

**Status: Complete.**

- Workspace setup: automatic empty-workspace build in Docker, with source mounted at `/workspace/ros2_ws/src` and build artifacts stored in Docker volumes.
- Runtime verification: ROS 2 CLI publisher/subscriber communication verified inside autonomy, with automatic environment sourcing.

Initial package structure is deferred until packages are needed in a later milestone.

### M0.4: Gazebo Integration

**Status: Complete.**

Integrate ROS 2 with Gazebo Harmonic using the ROS-Gazebo integration stack.

- Gazebo Harmonic installation, automatic world launch, and GUI access verified.
- `/clock` communication verified manually; automatic bridge startup now uses `config/ros_gz_bridge.yaml`.
- Automatic startup with the YAML configuration verified: `/clock` timestamps advance without manually starting the bridge.

### M0.5: Multi-robot independent navigation with Nav2

**Status: Single-robot navigation validated; multi-robot navigation pending.**

- Add TurtleBot/Nav2 dependencies, an empty world and ground-truth localization, and `swarm_bringup` for spawning, bridges, localization, and navigation in the existing Gazebo instance.
- Single-robot spawning checkpoint: `swarm_bringup` builds, installs upstream TurtleBot3 assets, and automatically spawns `robot1` in the existing Gazebo world.
- Entity creation, settled pose, shared mesh availability, and ROS clock reception have been verified.
- Namespaced command/state bridges and robot-state publishing are implemented and verified with ROS-commanded motion, odometry, wheel states, TF, and stopping.
- IMU and lidar world systems are enabled, with IMU, wheel joint, and lidar data verified through ROS.
- Gazebo ground-truth odometry and map-free Nav2 are implemented.
- Extending this to multiple robots remains pending.

**Acceptance:** Establish a working multi-robot navigation baseline using Nav2.

### M0.6: Continuous Integration

Establish automated build and test workflows.

## Phase 1: Collision Avoidance

Implement and evaluate baseline collision-avoidance algorithms such as RVO and ORCA.

Use interchangeable algorithm libraries independent of Nav2.

## Phase 2: State Estimation

Integrate EKF-based state estimation and validate covariance estimates against simulation ground truth.

## Phase 3: Uncertainty-Aware Collision Avoidance

Develop collision-avoidance methods that explicitly account for state-estimation uncertainty.

## Phase 4: Decentralized Coordination

Implement decentralized robot-state exchange and coordination without a central decision-making node.

Keep supervision limited to orchestration; add custom interfaces when needed.

## Phase 5: Experimental Evaluation

Benchmark the proposed methods under different localization uncertainties, robot densities, and communication conditions.
