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
| State estimation | EKF |
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

- Phase 0: Development infrastructure and environment.
- Phase 1: Multi-robot navigation baseline.
- Phase 2: Collision-avoidance baseline.
- Phase 3: State estimation and uncertainty modelling.
- Phase 4: Uncertainty-aware collision avoidance.
- Phase 5: Decentralized coordination.
- Phase 6: Experiments and evaluation.

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

## 8. Project Status

The project is currently in Phase 0: Development Infrastructure.

The M0.2 Docker environment has been implemented and validated. Documentation is being finalized before closing the milestone.

M0.3 is complete: automatic workspace builds and ROS 2 CLI publisher/subscriber communication inside autonomy have been verified.

M0.4 is complete: Gazebo startup, GUI access, and the automatic YAML-configured `/clock` bridge have been verified. See [Docker integration details](docs/architecture/docker-architecture.md#9-ros-gazebo-integration) for configuration and verification.
