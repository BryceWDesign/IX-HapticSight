# Changelog

All notable changes to IX-HapticSight are documented here.

## [0.2.0] - 2026-08-29

### Added
- Executable RGB-D perception pipeline with image ingestion.
- Two independently trained reference semantic segmenters with committed model parameters, deterministic training script, and held-out synthetic calibration metrics.
- Perception quorum that fails closed on model disagreement, critical-class disagreement, or low confidence.
- Vision-derived 3D GREEN/YELLOW/RED hazard projection.
- Deterministic multimodal safety fusion across vision, force/torque, tactile, proximity, and thermal state.
- Model-agnostic LLM/VLA safety broker that hashes untrusted physical proposals and returns bounded decision receipts.
- Independent safety authority that returns explicit `ALLOW`, `MODIFY`, or `DENY` decisions and bounded counterfactual explanations.
- Dynamic force and speed envelopes that derate authority for uncertainty, YELLOW state, and human proximity.
- Cycle-level runtime invariant monitor for consent, force, speed, sensor freshness, perception quorum, watchdog timing, and E-stop state.
- Bounded soft-real-time reference controller with deterministic recovery, zero-effort, retract, safe-hold, and operator-clear semantics.
- Deterministic contact-world simulation for closed-loop regression testing.
- ROS 2 bridge for bounded twist commands, `WrenchStamped` force/torque input, normalized tactile-patch input, E-stop input, and safety events.
- Standard ROS 2 `FollowJointTrajectory` client implementation for physical robot-controller integration when ROS 2 hardware is available.
- WebXR safety observer with live hazard, force-cap, speed-cap, consent, controller-state, and authority visualization.
- Executable HIL harness that can only report `PASSED` from declared hardware capability plus measured samples. Missing hardware produces `NOT_RUN_NO_HARDWARE`, never a synthetic pass.
- SHA-256 chained runtime evidence records and portable evidence-bundle verification.
- Adversarial safety-authority benchmark covering nominal behavior, over-request derating, RED hazards, consent loss, perception disagreement, high uncertainty, and human-proximity cases.
- End-to-end perception-to-contact software demonstration.
- Expanded automated test suite: 183 tests passing at release-candidate build time.

### Corrected
- Package license metadata now matches the MIT `LICENSE` file.
- Responsible-use language moved to a separate non-license statement to avoid contradictory license claims.
- Repository author metadata normalized to Bryce Lovell.

### Evidence limits
- Reference vision models are trained on deterministic synthetic calibration data, not field robot datasets.
- The Python controller is timing-instrumented soft real time, not a certified hard-real-time controller.
- ROS 2 and robot-controller adapters are implemented but not physically validated in this repository build.
- No HIL pass or real-robot pass is claimed without external measured hardware evidence.

## [0.1.0] - 2026-04-10

### Added
- Initial OHIP schemas and protocol reference implementation.
- Consent management, contact planning, nudge scheduling, rest pose generation, safety gating, simulation scene, configuration, and baseline tests.
