# Project Roadmap

## Phase 0: Infrastructure

Establish a reproducible development environment and software engineering workflow.

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

Establish the ROS 2 workspace and initial package structure.

### M0.4: Gazebo Integration

Integrate ROS 2 with Gazebo Harmonic using the ROS-Gazebo integration stack.

### M0.5: Robot Description and Spawning

Create the robot description and establish repeatable robot spawning in simulation.

### M0.6: Continuous Integration

Establish automated build and test workflows.

## Phase 1: Multi-Robot Navigation

Establish a working multi-robot navigation baseline using Nav2.

## Phase 2: Collision Avoidance

Implement and evaluate baseline collision-avoidance algorithms such as RVO and ORCA.

## Phase 3: State Estimation

Integrate EKF-based state estimation and validate covariance estimates against simulation ground truth.

## Phase 4: Uncertainty-Aware Collision Avoidance

Develop collision-avoidance methods that explicitly account for state-estimation uncertainty.

## Phase 5: Decentralized Coordination

Implement decentralized robot-state exchange and coordination without a central decision-making node.

## Phase 6: Experimental Evaluation

Benchmark the proposed methods under different localization uncertainties, robot densities, and communication conditions.