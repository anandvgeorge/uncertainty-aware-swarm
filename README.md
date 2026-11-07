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

## 4. Repository Structure

```text
.
├── .github/       # CI and PR templates
├── docker/        # Container configurations
├── src/           # ROS 2 packages and other libraries
├── docs/          # Architecture and documentation
├── scripts/       # Utility scripts
├── tests/         # Integration tests
├── README.md
└── CONTRIBUTING.md
```

## 5. Development Roadmap

- Phase 0: Development infrastructure and environment.
- Phase 1: Multi-robot navigation baseline.
- Phase 2: Collision-avoidance baseline.
- Phase 3: State estimation and uncertainty modelling.
- Phase 4: Uncertainty-aware collision avoidance.
- Phase 5: Decentralized coordination.
- Phase 6: Experiments and evaluation.

## 6. Development

The `dev` branch is the integration branch. All feature development should happen in dedicated branches and be merged through Pull Requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 7. Project Status

Currently in Phase 0: Development infrastructure and environment setup.