# Docker Architecture

## 1. Overview

The project uses Docker to provide a reproducible ROS 2 and Gazebo development environment, independent of the host OS installation.

**Host:** Ubuntu 22.04  
**Container OS:** Ubuntu 24.04

## 2. Technology Stack

| Component | Version |
|---|---|
| ROS 2 | Jazzy |
| Gazebo | Harmonic |
| Ubuntu | 24.04 |
| C++ | C++17 |
| Container orchestration | Docker Compose |

## 3. Container Architecture

The system consists of three containers with distinct responsibilities.

| Container | Responsibility | Lifecycle |
|---|---|---|
| `builder` | Compile ROS 2 packages, run tests and generate build artifacts | On demand |
| `autonomy` | Execute the compiled ROS 2 autonomy stack | Long-running |
| `gazebo` | Run Gazebo Harmonic simulation server and GUI | Long-running |

The builder and autonomy containers use compatible ROS environments. The builder contains development dependencies, while autonomy contains only runtime dependencies.

A single Gazebo server will eventually host multiple simulated robots. Individual robot containers are not required.

## 4. Workspace and Storage

The Git repository remains on the host. The ROS workspace exists inside the builder container only.

Host repository:

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

Builder workspace:

```text
/workspace/ros2_ws/
├── src/       # Bind-mounted from host
├── build/     # Docker named volume
├── install/   # Docker named volume
└── log/       # Docker named volume
```

Build artifacts persist through Docker named volumes and are not stored in the Git repository.

The autonomy container mounts the install volume read-only. It does not require access to the source repository or build tools.

## 5. Build and Runtime Workflow

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

- The builder runs on demand.
- Package builds are explicitly triggered.
- Colcon handles incremental builds.
- The autonomy container executes the latest successfully built packages.
- Source changes require rebuilding before the updated stack is executed.

The existence of build artifacts alone is not considered proof that they are up to date.

## 6. Networking

Docker host networking will be used for all three containers.

- Containers share the host network namespace and IP address.
- No macvlan or ipvlan configuration is required.
- ROS 2 DDS discovery uses the host network directly.
- No Docker port mapping is required.
- Port conflicts must be avoided.
- `ROS_DOMAIN_ID` will be configurable.

## 7. ROS-Gazebo Integration

`ros_gz_bridge` runs inside the autonomy container and connects ROS 2 communication with Gazebo Transport.

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

## 8. Design Principles

- Host-independent development environment.
- Reproducible container builds.
- Source code managed through Git.
- Persistent build artifacts.
- Separation of build-time and runtime dependencies.
- Runtime container does not require compilation tools.
- No ROS installation required on the host.
- No individual containers per simulated robot.
- Simple networking without physical NIC dependencies.