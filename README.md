# IX-HapticSight

**IX-HapticSight** is an open, safety-first perception-to-contact authority for robots and XR.

It is built around one architectural rule:

> Intelligent perception, planning, or an LLM may propose a physical action. A separate deterministic safety authority decides whether that action is allowed, must be reduced, or must be denied.

The repository connects perception-derived state to bounded robot behavior through explicit consent, hazard, force, speed, freshness, uncertainty, watchdog, recovery, and evidence rules.

**License:** MIT. See `RESPONSIBLE_USE.md` for the project's non-license safety and humanitarian-use statement.

## v0.2.0 status

Software reference implementation with executable perception, safety authority, controller, ROS 2 integration code, WebXR observability, simulation, HIL evidence collection, replay, benchmarks, and tests.

Current automated suite at the v0.2.0 release-candidate build: **183 tests passing**.

This repository does **not** claim a physical robot, HIL pass, certified safety system, or production deployment unless measured hardware evidence is explicitly included.

## What is implemented

### Perception and vision

- RGB image ingestion with depth input
- executable semantic segmentation model
- two independently trained reference model parameter sets
- deterministic training script
- held-out synthetic calibration metrics
- model-confidence and uncertainty output
- independent perception quorum
- critical-class disagreement detection
- vision-derived 3D GREEN / YELLOW / RED hazard voxels

The shipped reference segmentation models are intentionally small and auditable. They are trained on deterministic **synthetic calibration data**. This proves an executable vision path and reproducible model artifact, not production perception accuracy.

### Agent / VLA safety broker

`src/ohip_agent/` treats LLM, VLA, or planner output as an **untrusted physical proposal**. The broker hashes the exact proposal, fuses current multimodal safety state, and issues a receipt containing the granted force/speed authority and reasons. Agent output can never increase deterministic limits.

### Independent safety authority

`src/ohip_control/authority.py` provides an explicit authority boundary:

- `ALLOW`
- `MODIFY`
- `DENY`

The authority evaluates:

- consent state
- perception quorum
- perception uncertainty
- GREEN / YELLOW / RED safety level
- human presence and proximity
- requested force
- requested speed
- configured base limits

A learned model cannot enlarge the granted envelope.

### Deterministic multimodal fusion

Vision, force/torque, tactile, proximity, and thermal assessments are fused into one inspectable GREEN / YELLOW / RED decision. Required missing modalities fail closed. Excessive measured force, tactile pressure/shear, thermal limits, proximity stops, or perception disagreement can override a visually GREEN scene.

### Dynamic force and speed envelopes

Authority automatically derates or removes motion based on:

- YELLOW safety state
- increasing perception uncertainty
- human proximity
- RED hazards

A request for 8 N does not become an 8 N command merely because an AI planner asked for it.

### Cycle-level invariant monitoring

Every reference control cycle can independently verify:

- E-stop state
- consent continuity
- perception-quorum health
- commanded force versus granted force
- measured force versus granted force
- commanded speed versus granted speed
- safety-sensor freshness
- controller watchdog timing

Violations drive deterministic stop, latch, retreat, zero-effort, or safe-hold behavior.

### Contact control and recovery

The reference controller is executable and timing-instrumented. It supports:

- approach
- contact
- bounded command clamping
- measured over-force detection
- consent-loss stop
- perception-disagreement stop
- zero-effort recovery
- retract recovery
- safe hold
- operator-clear latch semantics

The Python implementation is **soft real time**. It is not represented as a certified hard-real-time controller.

### ROS 2

`src/ohip_ros2/` contains real ROS 2 integration code, loaded only when ROS 2 is available:

- `geometry_msgs/WrenchStamped` force/torque ingestion
- normalized tactile-patch ingestion via `std_msgs/Float32MultiArray`
- bounded `TwistStamped` output
- E-stop input
- structured safety-event output
- standard `control_msgs/FollowJointTrajectory` action client
- robot-controller trajectory validation

This means the repository contains an executable path into normal ROS 2 robot infrastructure. It does **not** mean a physical robot was run for this release.

### WebXR

`examples/webxr/` contains a browser WebXR safety observer that exposes:

- live safety-authority decision
- GREEN / YELLOW / RED hazard markers
- force cap
- speed cap
- consent state
- controller state
- veto / derating reason

A WebXR-capable browser can request an `immersive-ar` session. Device-specific registration and headset validation remain future measured work.

### HIL evidence harness

`src/ohip_hil/` implements a hardware-in-the-loop evidence harness with a strict rule:

**no hardware, no HIL PASS.**

Possible results include:

- `PASSED`
- `FAILED`
- `NOT_RUN_NO_HARDWARE`
- `NOT_RUN_INCOMPLETE`

A PASS requires declared hardware capability plus measured samples satisfying the configured force, latency, fault, and sample-count criteria.

### Tamper-evident evidence

`src/ohip_evidence/` provides:

- SHA-256 chained runtime records
- sequence continuity
- previous-hash continuity
- portable JSONL evidence records
- manifest hashing
- evidence-bundle verification
- tamper detection

This makes post-run evidence independently checkable instead of relying only on console output.

### Existing OHIP protocol/runtime layers

The repository retains and extends its earlier architecture for:

- consent management
- contact planning
- nudge scheduling
- rest pose generation
- dual-channel safety gating
- runtime sessions and fault states
- normalized force/torque interfaces
- tactile interfaces
- proximity interfaces
- thermal interfaces
- structured event logging
- replay
- deterministic benchmark scenarios
- simulated execution

## Architecture

```text
Camera / depth / scene state
            |
            v
   perception model A
   perception model B
            |
            v
     perception quorum
            |
            v
 vision-derived hazard map
            |
            +----------------------+
                                   |
AI / LLM / planner proposal        |
            |                      |
            v                      v
     +-----------------------------------+
     |   INDEPENDENT SAFETY AUTHORITY    |
     |                                   |
     | consent                           |
     | uncertainty                       |
     | model agreement                   |
     | hazard state                      |
     | force / speed envelopes           |
     | human proximity                   |
     +-----------------------------------+
            |
       ALLOW / MODIFY / DENY
            |
            v
   bounded reference controller
            |
     runtime invariant monitor
            |
      +-----+--------------------+
      |                          |
      v                          v
ROS 2 / robot adapter       recovery authority
      |                     zero effort / retract
      v                     safe hold / operator
robot or simulator                |
      ^                            |
      |                            |
force / tactile / proximity ------+
      |
      v
 tamper-evident evidence + replay + XR observer
```

## Quick verification

Run the complete software release verification:

```bash
python scripts/verify_release.py
```

Or install and run the suite directly:

```bash
python -m pip install -e .
pytest -q
```

Run the existing protocol quickstart:

```bash
python examples/quickstart.py
```

Run the perception-to-contact integration demo:

```bash
python examples/perception_to_contact_demo.py
```

Run the adversarial independent-authority benchmark:

```bash
python scripts/run_safety_authority_benchmark.py
```

Retrain both committed reference segmenters reproducibly:

```bash
python scripts/train_reference_segmenter.py
```

Run the WebXR observer:

```bash
python examples/webxr/run_observer.py
```

Then open `http://127.0.0.1:8765` in a browser. WebXR immersive AR requires compatible browser/device support.

## Repository map

### Core protocol

`src/ohip/`

Consent, schemas, planning, safety gating, nudge scheduling, and rest pose behavior.

### Perception

`src/ohip_perception/`

RGB-D frames, reference segmentation, two-model quorum, vision pipeline, and hazard projection.

### Agent safety broker

`src/ohip_agent/`

Model-agnostic LLM/VLA proposal ingestion, multimodal safety brokerage, proposal hashing, and decision receipts.

### Physical safety authority and control

`src/ohip_control/`

Independent action authority, dynamic envelopes, runtime invariants, bounded controller, and recovery planner.

### ROS 2 integration

`src/ohip_ros2/`

ROS 2 force/torque ingestion, bounded motion publication, E-stop state, safety events, and joint-trajectory action client.

### Hardware evidence

`src/ohip_hil/`

Measured HIL acceptance harness with explicit no-hardware semantics.

### Evidence

`src/ohip_evidence/`

Tamper-evident evidence chaining and portable bundle verification.

### XR

`src/ohip_xr/` and `examples/webxr/`

Safety-state payloads, local state server, and WebXR observer.

### Simulation

`src/ohip_sim/`

Deterministic contact plant for controller regression tests. Simulation is clearly separated from physical evidence.

### Existing runtime and interfaces

- `src/ohip_runtime/`
- `src/ohip_interfaces/`
- `src/ohip_logging/`
- `src/ohip_bench/`

## Claim matrix

| Capability | Implementation | Evidence in this repo |
|---|---|---|
| Safety-first protocol | YES | automated tests |
| Consent-aware contact | YES | automated tests |
| Force envelopes | YES | automated tests |
| Tri-level hazards | YES | automated tests |
| Vision pipeline | YES | executable RGB-D path |
| Segmentation model | YES | model files + reproducible training + synthetic held-out metrics |
| Vision-derived hazard maps | YES | executable projector + tests |
| Independent model quorum | YES | disagreement tests |
| Dynamic safety authority | YES | adversarial benchmark + tests |
| Soft-real-time controller | YES | executable timing-instrumented controller + tests |
| Recovery architecture | YES | deterministic recovery + tests |
| ROS 2 bridge | YES | real ROS 2 code; runtime requires ROS 2 environment |
| ROS 2 robot action client | YES | `FollowJointTrajectory` implementation; physical run not claimed |
| WebXR observer | YES | actual browser WebXR client; headset validation not claimed |
| Hardware F/T integration path | YES | ROS 2 `WrenchStamped` adapter; live device measurement not included |
| Hardware tactile integration path | YES | normalized ROS 2 tactile-patch transport; live device measurement not included |
| LLM/VLA safety broker | YES | untrusted proposal validation, multimodal fusion, deterministic receipt |
| HIL harness | YES | executable harness |
| HIL measured PASS | **NO** | requires physical hardware |
| Physical robot execution evidence | **NO** | requires physical robot |
| Certified robot safety | **NO** | requires applicable engineering, standards, and independent validation |

## Why the final three NOs remain NO

IX-HapticSight deliberately refuses to turn software simulation into physical evidence.

A ROS 2 adapter can be complete without a robot being connected. A HIL harness can be complete without fabricated measurements. A controller can be executable without being certified hard real time.

Those distinctions are part of the project, not missing marketing polish.

## Responsible use and safety

The MIT license is in `LICENSE`. `RESPONSIBLE_USE.md` is a separate statement of project intent and does not add contradictory license restrictions.

Physical deployment should use hardware-specific safety engineering, independent emergency-stop mechanisms, calibrated sensing, watchdogs, robot limits, formal risk assessment, and the standards applicable to the actual system and environment.

## Author

Bryce Lovell
