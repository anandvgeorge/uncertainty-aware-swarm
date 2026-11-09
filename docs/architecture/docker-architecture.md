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

- The builder runs on demand.
- Package builds are explicitly triggered.
- Colcon handles incremental builds.
- The autonomy container executes the packages available in the install volume.
- Source changes require rebuilding before the updated stack is executed.

The existence of build artifacts alone is not considered proof that they are up to date.

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
- Depends on the Gazebo service.
- Uses `sleep infinity` as its default command to keep the container running.

### Gazebo

- Builds from `docker/Dockerfile.gazebo`.
- Uses host networking.
- Receives the host `DISPLAY` and X11 authorization configuration.
- Mounts the X11 socket and Xauthority file.
- Uses `sleep infinity` as its default command to keep the container running.

The current Compose configuration prepares and starts the containers. It does not automatically launch Gazebo or the autonomy application.

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
docker compose ps
```

View service logs:

```bash
docker compose logs
```

Open a shell in a service:

```bash
docker compose exec builder bash
docker compose exec autonomy bash
docker compose exec gazebo bash
```

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

The planned integration will use `ros_gz_bridge` to connect ROS 2 communication with Gazebo Transport. This work is assigned to M0.4: Gazebo Integration.

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

This diagram represents the planned integration architecture, not a claim that the bridge is already configured in M0.2.

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