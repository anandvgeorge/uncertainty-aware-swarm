# Uncertainty-Aware Swarm Navigation

A ROS 2-based research and engineering project exploring uncertainty-aware collision avoidance and decentralized navigation in multi-robot systems.

## 1. Objective

Develop a decentralized multi-robot navigation framework in which robots account for state-estimation uncertainty when making collision-avoidance decisions.

The project investigates how localization uncertainty affects collision avoidance, navigation performance, and multi-robot coordination.

## 2. Key Objectives

- Implement multi-robot navigation using ROS 2 and Nav2.
- Develop a modular collision-avoidance framework.
- Integrate state estimation using EKF.
- Incorporate state covariance into collision-avoidance decisions.
- Explore decentralized coordination and information sharing.
- Evaluate performance under different uncertainty and communication conditions.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Containerization | Docker |
| Container OS | Ubuntu 24.04 |
| Middleware | ROS 2 Jazzy |
| Simulation | Gazebo Harmonic |
| Navigation | Nav2 |
| Localization / state estimation | Gazebo ground-truth baseline; EKF in a later phase |
| Language | C++17 |
| Build system | CMake, colcon |
| Testing | GoogleTest |

Host environment: Ubuntu 22.04.

The development environment is containerized. A ROS installation on the host is not required.

## 4. Repository Structure

```text
.
├── .github/       # CI and PR templates
├── docker/        # Container configurations
├── src/           # ROS 2 packages and other libraries
├── docs/          # Architecture and documentation
├── scripts/       # Utility scripts
├── tests/         # Integration tests
├── docker-compose.yml
├── README.md
└── CONTRIBUTING.md
```

The ROS 2 workspace is maintained inside the containers. The repository's `src/` directory is mounted into the workspace.

## 5. Development Roadmap

- Phase 0: Working multi-robot Nav2 baseline, including infrastructure.
- Phase 1: Collision-avoidance baseline.
- Phase 2: State estimation and uncertainty modelling.
- Phase 3: Uncertainty-aware collision avoidance.
- Phase 4: Decentralized coordination.
- Phase 5: Experiments and evaluation.

See [docs/roadmap.md](docs/roadmap.md) for milestone details and progress.

## 6. Development Environment

The Docker environment consists of three services:

- `builder`: ROS 2 development environment for compiling packages and running tests.
- `autonomy`: Runtime environment for executing the compiled ROS 2 stack.
- `gazebo`: Gazebo Harmonic environment.

Build the images and start the environment:

```bash
docker compose up --build -d
```

The builder automatically builds the ROS workspace and exits successfully. Autonomy starts after the build succeeds.

Check their status:

```bash
docker compose ps -a
```

The builder workspace uses persistent Docker volumes for build artifacts. The autonomy container mounts the install volume read-only.

See [docs/architecture/docker-architecture.md](docs/architecture/docker-architecture.md) for the architecture and environment details.

## 7. Development Workflow

The `dev` branch is the integration branch. All feature development should happen in dedicated branches and be merged through Pull Requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

GitHub Actions runs build, configuration and simulation checks on pull requests and pushes to `dev`, and can
also be started manually. It builds all three Docker images, builds the ROS
workspace in a fresh container without development volumes, and verifies the
installed `swarm_bringup` resources and TurtleBot3 assets. Build logs are uploaded
even when a check fails. After configuration and build checks pass, the same runner
executes the headless simulation smoke test. Docker Buildx restores and exports
GitHub Actions layer caches with separate scopes for builder, autonomy and Gazebo.
The first run populates these caches; subsequent runs reuse unchanged layers.
Both test scripts reuse the images loaded by the workflow without rebuilding or
pulling them. Workspace build/install artifacts remain fresh on every run.
Image build logs are available in the Docker action steps; workspace and smoke
logs are uploaded as artifacts.

To run the same build checks locally with Docker:

```bash
bash scripts/ci-build.sh /tmp/swarm-ci-build-logs
```

Use a fresh log directory for each run. The script removes its temporary container
and image tags on exit; Docker build cache is retained. No GUI or running simulation
is required.

For an existing set of images named `<prefix>-builder:latest`,
`<prefix>-autonomy:latest` and `<prefix>-gazebo:latest`, set
`SWARM_CI_IMAGE_PREFIX=<prefix>` when running either script to skip image builds.
Missing images fail the check. Supplied images are preserved during cleanup;
default local runs still build and remove their own temporary image tags.

The separate configuration job checks Python syntax, YAML (including duplicate
keys), XML/SDF, three unique robot declarations and spawn positions, the shared
clock bridge configuration, and Nav2/ground-truth frame consistency. It also
resolves Docker Compose and checks Dockerfile and repository bind-mount paths.
Run it locally with Python 3.10+, PyYAML (`python3-yaml` on Ubuntu), and Docker Compose 2.24.4+:

```bash
python3 scripts/ci-check-config.py
```

These checks need no Docker daemon, ROS installation, or display. Desktop values
are supplied only for Compose interpolation; the checks do not validate host GUI
devices. The robot declaration check expects the literal `robots` list in
`swarm.launch.py`. The merged headless Compose configuration is also checked for
missing mounts, host-network use, and GUI/GPU requirements.

Run the simulation smoke test with Docker and Compose 2.24.4+:

```bash
bash scripts/ci-smoke.sh "$(mktemp -d /tmp/swarm-ci-smoke-XXXXXX)"
```

The CI Compose override runs Gazebo with EGL software rendering, without a display
or GPU device. Each run builds a fresh workspace in its own volumes and uses its
own Docker network and Gazebo partition. The observer requires advancing clock,
odometry, IMU, lidar and joint-state timestamps; valid per-robot transforms; active
Nav2 servers; and available navigation action servers. It checks publisher and
subscriber namespaces and compares odometry/TF positions with the distinct spawn
positions, then confirms all three entities in the Gazebo scene. Readiness must
remain satisfied for five seconds within a 180-second wall-clock deadline.

This is a startup/readiness test; it does not send motion commands or navigation
goals. It monitors Gazebo/autonomy container liveness and preserves container,
workspace, observer and scene logs. The script removes its containers, volumes,
network and temporary image tags on exit. GitHub retains the logs for seven days,
including on failure.

## 8. Project Status

The project is currently in Phase 0: Working Multi-Robot Nav2 Baseline. Three TurtleBot3 Burgers have verified independent map-free Nav2 goal navigation using Gazebo ground-truth odometry.

The M0.2 Docker environment has been implemented and validated. Documentation is being finalized before closing the milestone.

M0.3 is complete: automatic workspace builds and ROS 2 CLI publisher/subscriber communication inside autonomy have been verified.

M0.4 is complete: Gazebo startup, GUI access, and the automatic YAML-configured `/clock` bridge have been verified. See [Docker integration details](docs/architecture/docker-architecture.md#9-ros-gazebo-integration) for configuration and verification.

M0.5 now spawns three TurtleBot3 Burgers (`robot1`, `robot2`, and `robot3`) automatically in the shared Gazebo world when the environment starts. The workspace build, entity creation, settled pose, mesh availability, and ROS clock reception have been verified; GUI appearance has not been visually inspected. See [three-robot startup and validation](docs/architecture/docker-architecture.md#three-robot-bringup).

Each robot exposes namespaced ROS command, odometry, joint-state, and TF interfaces using the upstream TurtleBot3 bridge definitions and robot-state publisher. ROS-commanded motion, odometry, wheel joint states, TF, and stopping have been verified.

IMU, wheel joint measurements, and lidar are enabled on `/robot1/imu`, `/robot1/joint_states`, and `/robot1/scan`. See [sensor streams](docs/architecture/docker-architecture.md#sensor-streams) for measurements and checks.

The existing bringup now starts Nav2 automatically. Goals use `/<robot_name>/navigate_to_pose` (`nav2_msgs/action/NavigateToPose`) in frame `odom`. Gazebo ground truth supplies odometry and its TF. Global and local costmaps use lidar without a saved map. See [map-free navigation and goal commands](docs/architecture/docker-architecture.md#map-free-nav2-navigation).

Three separate goals were accepted concurrently and completed successfully after a fresh startup. Each robot retained fresh sensors, odometry, commands, and TF, with one shared `/clock` publisher.

M0.6 build, configuration and headless simulation checks are implemented and have
passed locally. GitHub-hosted execution remains to be verified through the PR.
Next: collision-avoidance experiments.
