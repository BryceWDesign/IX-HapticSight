# IX-HapticSight Roadmap

IX-HapticSight is a safety-first perception-to-contact authority for robots and XR. The project keeps learned perception, planners, and LLMs outside the final physical safety authority.

## M0: Protocol reference
**Status: complete**

Consent, state machine, contact planning, force envelopes, safety gating, retreat semantics, and core schemas.

## M1: Auditable runtime
**Status: complete**

Runtime coordination, explicit sessions/faults, normalized force/tactile/proximity/thermal interfaces, structured logging, replay, benchmark support, and simulated execution.

## M2: Perception-to-hazard pipeline
**Status: complete at reference-model level**

RGB-D ingestion, executable segmentation, reproducible synthetic calibration training, independent model quorum, uncertainty handling, and vision-derived tri-level hazard voxels.

**Remaining evidence:** field datasets, calibrated depth hardware, production segmentation models, adverse-lighting evaluation, occlusion benchmarks, and robot-specific camera calibration.

## M3: Independent physical safety authority
**Status: complete at software reference level**

Explicit `ALLOW`, `MODIFY`, and `DENY`; dynamic authority derating; consent enforcement; uncertainty stops; proximity stops; runtime invariant monitoring; force and speed clamping; deterministic recovery.

**Remaining evidence:** hardware safety controller implementation, safety PLC/MCU partitioning, formal timing analysis, certified E-stop chain, and standards-specific validation.

## M4: ROS 2 and controller integration
**Status: implementation complete, hardware validation pending**

Bounded ROS 2 twist bridge, `WrenchStamped` force/torque ingestion, E-stop state, structured safety side-channel, and `FollowJointTrajectory` action client.

**Remaining evidence:** named robot/controller configuration, MoveIt Servo or equivalent integration, real robot joint limits, collision scene, calibration, and measured command/feedback latency.

## M5: XR observability
**Status: implementation complete, device validation pending**

WebXR observer with live safety-authority state, hazard markers, consent state, force/speed authority, and controller state.

**Remaining evidence:** headset-specific testing, spatial registration accuracy, user studies, and latency measurements.

## M6: HIL evidence
**Status: harness complete, measured evidence pending**

The harness rejects synthetic HIL claims. A PASS requires positive hardware capability detection and measured samples meeting declared limits.

**Exit criteria for a real HIL PASS:**
- robot motion hardware present;
- live force/torque source present;
- time-synchronized measurements;
- declared sample count reached;
- force and latency limits not exceeded;
- fault injection and recovery captured;
- evidence bundle retained.

## M7: Physical robot validation
**Status: not yet claimed**

Required work includes physical contact trials, diverse-object manipulation, human-proximity validation, measured recovery, controller stress testing, failure injection, sim-to-real comparison, and independent review.

## M8: Production / certification track
**Status: future**

Hardware-specific safety case, applicable standards work, deployment controls, privacy review, cybersecurity, manufacturing constraints, and external validation.

## Non-negotiable claim rule

Simulation, software tests, ROS 2 adapter availability, and synthetic calibration do not become physical evidence by wording. IX-HapticSight should only claim what an artifact or measurement actually demonstrates.
