# v0.2.0 Claim Matrix

This file is normative for release claims.

## Software claims supported in repository

- executable RGB-D perception path;
- executable reference semantic segmentation;
- reproducible synthetic calibration training;
- two-model perception quorum;
- vision-derived hazard voxels;
- deterministic safety authority;
- dynamic force/speed derating;
- cycle-level runtime invariant monitoring;
- bounded soft-real-time reference controller;
- deterministic recovery;
- ROS 2 bridge implementation;
- standard joint-trajectory action-client implementation;
- WebXR observer implementation;
- executable HIL evidence harness;
- tamper-evident evidence chain;
- deterministic simulation and adversarial software benchmarks.

## Claims not supported without external evidence

- production perception accuracy;
- HIL PASS;
- physical robot execution PASS;
- certified hard-real-time performance;
- collaborative-robot certification;
- safety certification;
- human-subject validation;
- production deployment reliability.

## Evidence labeling rule

Every future report should label its source as one of:

- SOFTWARE_TEST
- SYNTHETIC_CALIBRATION
- SIMULATION
- REPLAY
- HIL_MEASURED
- PHYSICAL_ROBOT_MEASURED

Only the last two may support hardware-performance claims.
