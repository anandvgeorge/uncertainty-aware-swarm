# Project Roadmap

## Phase 0: Infrastructure

Establish a reproducible development environment and software engineering workflow.

- M0.1: GitHub repository foundation.
- M0.2: Docker environment.
- M0.3: ROS 2 workspace.
- M0.4: Gazebo integration.
- M0.5: Robot description and spawning.
- M0.6: Continuous integration.

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