# Package Map

IX-HapticSight v0.2 separates perception, policy, safety authority, execution, sensing, evidence, and validation so no learned model silently inherits actuator authority.

## `src/ohip/`

Protocol core:
- canonical schemas;
- consent management;
- contact planning;
- nudge scheduling;
- rest pose generation;
- legacy dual-channel safety gate.

## `src/ohip_agent/`

Untrusted agent/VLA boundary:
- physical proposal schema;
- strict numeric validation;
- proposal SHA-256;
- multimodal safety brokerage;
- bounded decision receipts.

## `src/ohip_perception/`

Perception:
- RGB-D frame normalization;
- executable reference segmenters;
- reproducible synthetic calibration training;
- two-model quorum;
- uncertainty and critical-disagreement handling;
- vision-to-hazard projection.

## `src/ohip_control/`

Independent physical safety authority:
- multimodal safety fusion;
- `ALLOW` / `MODIFY` / `DENY` authority;
- dynamic force/speed envelopes;
- runtime invariant monitor;
- bounded soft-real-time control kernel;
- deterministic recovery planner.

## `src/ohip_runtime/`

Session/runtime coordination:
- interaction requests;
- session state;
- faults;
- coordination decisions;
- runtime service and session store.

## `src/ohip_interfaces/`

Backend-neutral sensing and execution contracts:
- signal health/freshness;
- force/torque;
- tactile;
- proximity;
- thermal;
- execution adapter;
- simulated execution adapter.

## `src/ohip_ros2/`

Concrete ROS 2 integration:
- `WrenchStamped` force/torque conversion;
- normalized tactile patch transport;
- E-stop input;
- bounded `TwistStamped` output;
- structured safety events;
- `FollowJointTrajectory` action client.

ROS 2 is optional at import time. Starting the bridge without ROS 2 installed fails explicitly rather than substituting simulation.

## `src/ohip_sim/`

Deterministic software-only contact plant for controller regression. It is simulation evidence only.

## `src/ohip_hil/`

Hardware-in-the-loop evidence harness. It cannot report PASS without declared required hardware and measured samples.

## `src/ohip_logging/`

Structured runtime event logging and replay helpers.

## `src/ohip_evidence/`

Tamper-evident evidence chain and portable evidence-bundle verifier.

## `src/ohip_bench/`

Deterministic benchmark models, scenarios, reports, and adversarial safety-authority benchmark.

## `src/ohip_xr/`

XR safety-state payloads and local state server.

## `examples/webxr/`

Actual browser WebXR observer with XR-space hazard rendering plus desktop fallback.

## `models/`

Committed reference segmentation parameters and metrics. The current models are synthetic-calibration baselines, not production perception claims.

## `tests/`

Automated regression suite covering protocol, runtime, interfaces, perception, control, multimodal safety, agent brokerage, evidence integrity, ROS 2 contracts, HIL semantics, XR artifacts, and simulation.
