# IX-HapticSight v0.2.0 Validation Report

**Validation date:** 2026-08-29
**Environment:** Windows 11 / Python 3.13.2 local release verification; Linux / Python 3.13.5 artifact-preparation verification.
**Evidence scope:** software tests, deterministic synthetic calibration, and simulation only unless explicitly stated otherwise.

## Release verification

Command:

`python scripts/verify_release.py`

Observed result:

- Python compile check: PASS
- automated test suite: **183 passed**
- protocol quickstart: PASS, `SAFETY_OK: True`
- perception-to-contact integration demo: PASS
- tamper-evident evidence chain in integration demo: PASS
- adversarial safety-authority benchmark: **8 / 8 scenarios passed**
- overall software release verification: PASS

## Reproducible perception-model evidence

The test suite retrains both committed reference segmenters into a fresh temporary directory and requires the generated model and metrics files to match the committed artifacts byte-for-byte.

Result: PASS.

Evidence class: `SYNTHETIC_CALIBRATION`.

This does not support a claim of production segmentation accuracy. The training data are deterministic synthetic calibration samples.

## Randomized safety property evidence

The suite evaluates 2,000 deterministic randomized authority proposals and verifies that the independent safety authority never grants force or speed above:

- the requested force/speed;
- the configured base force/speed caps;
- zero when the disposition is `DENY`.

Result: PASS.

Evidence class: `SOFTWARE_TEST`.

## ROS 2 evidence

Implemented:

- `WrenchStamped` force/torque ingestion;
- normalized tactile patch ingestion;
- E-stop input;
- bounded `TwistStamped` output;
- structured safety events;
- `FollowJointTrajectory` action-client implementation.

Validation environment does not contain `rclpy`. The repository explicitly raises `Ros2Unavailable` rather than substituting simulated hardware, and that behavior is tested.

Physical ROS 2 robot validation: **NOT RUN**.

## HIL evidence

The HIL harness is implemented and tested. It refuses to report a PASS when required hardware is absent.

Measured HIL PASS for this release: **NOT_RUN_NO_HARDWARE**.

No synthetic measurement has been promoted to HIL evidence.

## WebXR evidence

Implemented:

- local live safety-state feed;
- 2D browser fallback;
- WebXR `immersive-ar` session path;
- `XRWebGLLayer`;
- XR animation frame loop;
- XR-space hazard marker rendering.

Headset/device validation for this release: **NOT RUN**.

## Physical robot evidence

Physical robot execution PASS: **NOT CLAIMED**.

The ROS 2 execution paths are code-complete reference integrations, but a physical manipulator, calibrated sensors, controller, and HIL rig are required before physical performance can be stated.

## Claim boundary

The v0.2.0 repository supports a strong claim of an executable, auditable perception-to-contact safety architecture. It does not support a claim that IX-HapticSight outperforms a deployed industrial robot in manipulation speed, object coverage, success rate, durability, or scale.
