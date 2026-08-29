# Requirements Traceability Matrix

This matrix describes the v0.2.0 reference implementation. `IMPLEMENTED` means implemented and tested at the stated software level. It does not imply physical validation or certification.

| ID | Requirement | Implementation anchors | Test / evidence anchors | Status | Remaining evidence |
|---|---|---|---|---|---|
| RQ-001 | Canonical protocol schemas | `src/ohip/schemas.py` | `tests/test_schemas.py` | IMPLEMENTED | interoperability/version migration across external implementations |
| RQ-002 | Consent must gate contact where required | `src/ohip/consent_manager.py`, `src/ohip_control/authority.py` | consent + authority tests | IMPLEMENTED | human-subject/user-interface validation |
| RQ-003 | RED hazards must deny physical authority | `src/ohip/safety_gate.py`, `src/ohip_control/authority.py` | adversarial benchmark, randomized authority property test | IMPLEMENTED | physical hazard-sensor validation |
| RQ-004 | Learned/agent output may not enlarge deterministic limits | `src/ohip_agent/broker.py`, `src/ohip_control/envelope.py` | broker tests, 2,000-case randomized authority property test | IMPLEMENTED | external VLA/LLM integration trials |
| RQ-005 | Vision shall produce explicit confidence/uncertainty | `src/ohip_perception/segmentation.py` | perception tests, reproducible model build | IMPLEMENTED | field dataset calibration |
| RQ-006 | Independent perception disagreement shall be detectable | `src/ohip_perception/fusion.py` | quorum tests | IMPLEMENTED | independent production model families and field tests |
| RQ-007 | Perception-derived hazards shall map to tri-level safety state | `src/ohip_perception/hazard_map.py` | hazard-map and pipeline tests | IMPLEMENTED | calibrated camera/depth geometry |
| RQ-008 | Multimodal state shall be able to override vision | `src/ohip_control/multimodal.py` | multimodal fusion tests | IMPLEMENTED | live synchronized sensor streams |
| RQ-009 | Force and speed requests shall be clamped or denied | `src/ohip_control/envelope.py`, `authority.py` | envelope, authority, benchmark, property tests | IMPLEMENTED | robot/controller measurements |
| RQ-010 | Runtime shall re-check safety after initial authorization | `src/ohip_control/invariants.py`, `realtime.py` | controller/invariant tests | IMPLEMENTED | hard-real-time deployment and timing evidence |
| RQ-011 | Recovery shall be explicit | `src/ohip_control/recovery.py` | controller/recovery tests | IMPLEMENTED | measured recovery trajectories |
| RQ-012 | Backend transport shall remain downstream of safety authority | `src/ohip_interfaces/execution_adapter.py`, `src/ohip_ros2/` | adapter and ROS contract tests | IMPLEMENTED | robot-specific integration |
| RQ-013 | Live F/T transport path shall exist | `src/ohip_ros2/messages.py`, `bridge.py` | ROS wrench converter tests | IMPLEMENTED | live force/torque hardware evidence |
| RQ-014 | Live tactile transport path shall exist | `src/ohip_ros2/messages.py`, `bridge.py` | tactile converter tests | IMPLEMENTED | live tactile hardware evidence |
| RQ-015 | Missing ROS runtime shall not silently become simulated hardware | `src/ohip_ros2/bridge.py` | `test_ros2_unavailable_is_explicit.py` | IMPLEMENTED | ROS 2 deployment test |
| RQ-016 | HIL PASS shall require real declared hardware + measured samples | `src/ohip_hil/harness.py` | HIL harness tests | IMPLEMENTED | actual HIL run |
| RQ-017 | Runtime evidence shall be tamper-evident | `src/ohip_evidence/` | hash-chain/bundle tamper tests | IMPLEMENTED | signed external timestamp/identity if required |
| RQ-018 | Safety state shall be externally observable in XR | `src/ohip_xr/`, `examples/webxr/` | XR payload/static integration tests | IMPLEMENTED | headset registration/latency measurements |
| RQ-019 | Simulation shall remain distinguishable from hardware evidence | `src/ohip_sim/`, HIL status model, docs claim matrix | HIL and simulation tests | IMPLEMENTED | process discipline in future reports |

## Evidence classes

Future evidence should be explicitly labeled:

- `SOFTWARE_TEST`
- `SYNTHETIC_CALIBRATION`
- `SIMULATION`
- `REPLAY`
- `HIL_MEASURED`
- `PHYSICAL_ROBOT_MEASURED`

Only the final two may support physical performance claims.

## Current release evidence gap

The v0.2.0 software architecture is substantially implemented, but the repository does not contain a physical robot test or HIL PASS. That gap is intentional and visible.
