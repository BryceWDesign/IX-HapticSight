# Runtime Architecture Overview

This document defines the planned runtime-oriented architecture for IX-HapticSight as the repository evolves from a reference Python implementation into a more modular and auditable interaction stack.

It is a design target, not a claim that all runtime capabilities already exist in the repository today.

---

## 1. Purpose

The runtime architecture exists to make these behaviors explicit and inspectable:

- perception-informed interaction gating
- consent-aware behavior authorization
- bounded approach and pre-contact verification
- bounded contact execution
- retreat and safe-hold behavior
- deterministic veto behavior under hazard or policy failure
- replayable event history for review

The design goal is to keep safety and policy logic understandable even as execution layers become more complex.

---

## 2. Current Baseline

The current repository already provides these core logic components under `src/ohip/`:

- `schemas.py`
- `consent_manager.py`
- `contact_planner.py`
- `nudge_scheduler.py`
- `rest_pose.py`
- `safety_gate.py`

These modules form the protocol and behavior core, but they do not yet represent a full robotics runtime.

What is still missing from a stronger runtime form includes:

- runtime orchestration and node boundaries
- message and service contracts
- motion execution adapter boundaries
- sensor interface abstraction layers
- structured event logging and replay
- benchmark execution harnesses
- fault-injection and HIL integration points

---

## 3. Target Runtime Layers

The planned architecture is organized into seven layers.

### Layer A — Policy and Data Model

This layer defines the canonical meaning of system data.

Responsibilities:
- schema definitions
- policy structures
- force limit structures
- consent records
- contact request definitions
- event record definitions
- benchmark result records

Baseline mapping:
- currently centered in `src/ohip/schemas.py`

Key rule:
- runtime services should consume and emit stable typed structures rather than ad hoc dictionaries wherever practical

---

### Layer B — Interaction Governance

This layer determines whether interaction is permitted and under what constraints.

Responsibilities:
- consent validation
- consent freshness checks
- caregiver and cultural policy handling
- schedule logic
- state-aware permission checks
- interaction profile resolution

Baseline mapping:
- `src/ohip/consent_manager.py`
- `src/ohip/nudge_scheduler.py`

Planned expansion:
- explicit consent service
- policy bundle versioning
- audit log records for consent and override decisions

Key rule:
- no execution path should bypass this layer when human-facing contact is being considered

---

### Layer C — Safety and Veto

This layer determines whether action should be slowed, blocked, aborted, or routed to retreat.

Responsibilities:
- hazard-zone evaluation
- environment clearance checks
- force threshold gating
- stale-input detection
- retreat triggers
- safe-hold triggers
- watchdog and fault response
- independent veto path evaluation

Baseline mapping:
- `src/ohip/safety_gate.py`

Planned expansion:
- independent veto logic
- thermal and proximity-aware blocking
- latched fault semantics
- execution halt path integration

Key rule:
- safety decisions must remain inspectable and must not be delegated to probabilistic convenience behavior

---

### Layer D — Contact Planning and Behavior Shaping

This layer produces bounded interaction plans within policy and safety constraints.

Responsibilities:
- contact target interpretation
- pose feasibility checks
- approach corridor planning
- pre-contact confirmation logic
- retreat path generation
- rest posture generation
- support posture generation

Baseline mapping:
- `src/ohip/contact_planner.py`
- `src/ohip/rest_pose.py`

Planned expansion:
- richer pre-contact stages
- contact-state fusion hooks
- execution adapter commands
- retreat semantics for additional fault classes

Key rule:
- planning should be bounded by upstream policy and safety outputs rather than discovering those constraints late

---

### Layer E — Sensor and Signal Interfaces

This layer ingests the measured signals used by runtime policy and safety evaluation.

Responsibilities:
- force-torque input normalization
- tactile input normalization
- proximity input normalization
- thermal input normalization
- freshness timestamps
- confidence and health metadata
- fused contact-state representation

Current status:
- not yet fully implemented as separate modules

Planned additions:
- interface abstractions for:
  - wrist force-torque
  - surface tactile sensing
  - short-range proximity
  - local thermal sensing

Key rule:
- runtime logic should consume normalized signal objects rather than device-specific raw payloads

---

### Layer F — Execution Adapter

This layer translates bounded interaction plans into runtime execution commands for a robot or simulation backend.

Responsibilities:
- command transport
- execution acknowledgements
- abort and retreat commands
- limit scaling
- collision-aware motion handoff
- execution fault reporting

Current status:
- not yet represented as a dedicated runtime layer

Planned examples:
- simulated executor
- ROS 2 execution bridge
- future MoveIt-compatible bridge layer

Key rule:
- execution should remain replaceable without rewriting governance, safety, or planning logic

---

### Layer G — Observability, Replay, and Evidence

This layer captures what happened and why.

Responsibilities:
- structured event logging
- replay records
- benchmark scenario execution
- metrics aggregation
- audit artifacts
- calibration and HIL evidence storage

Current status:
- not yet implemented as a dedicated package

Planned outputs:
- event logs
- replay sessions
- benchmark reports
- safety traceability artifacts
- scenario result bundles

Key rule:
- important behavior should be explainable after the fact without reconstructing intent from scattered logs

---

## 4. Planned Runtime Package Direction

As the repository grows, responsibilities should separate cleanly.

A target structure is:

- `src/ohip/`
  - stable Python reference implementation and shared models
- `src/ohip_runtime/`
  - runtime coordination and orchestration
- `src/ohip_interfaces/`
  - sensor and execution interfaces
- `src/ohip_logging/`
  - event logging and replay
- `src/ohip_bench/`
  - benchmark runners and metrics
- `src/ohip_ros2/`
  - ROS 2-facing integration layer

This separation is intended to preserve a clean core while allowing runtime-specific tooling to evolve.

---

## 5. Planned Data Flow

A simplified target data flow is:

1. sensor and scene input arrive
2. signal interfaces normalize and timestamp inputs
3. policy and consent checks evaluate allowed interaction scope
4. safety layer evaluates veto, slowdown, abort, or continue
5. planner generates bounded approach, contact, or retreat instructions
6. execution adapter translates those instructions to the runtime backend
7. logging layer records decisions, transitions, and outcomes

This flow should remain one-directional in logic ownership:

- policy constrains planning
- safety can veto planning and execution
- execution never silently rewrites policy or safety assumptions

---

## 6. State Ownership Principles

The runtime should have clear ownership of state.

### Canonical state categories
- interaction state
- consent state
- hazard state
- execution state
- contact state
- fault state

### Ownership goals
- avoid hidden globals
- avoid duplicated state with conflicting authority
- make fault state latched where appropriate
- ensure transition reasons are loggable

The existing state machine in `docs/state_machine.md` should remain the reference for interaction state semantics.

---

## 7. Non-Goals

This runtime architecture is not intended to become:

- a generic social robotics framework
- a broad emotional inference engine
- a production certification claim
- a substitute for hardware safety engineering
- a guarantee of safe real-world deployment without measured evidence

The purpose is bounded interaction governance, not broad personality simulation.

---

## 8. Review Standard for Runtime Work

New runtime work should improve at least one of the following:

- state clarity
- safety separation
- sensor abstraction quality
- replayability
- bounded execution
- testability
- traceability

If a change makes runtime behavior harder to reason about, it should be treated as suspect even if it adds capability.

---

## 9. Next Planned Runtime Documents

This overview will be supported by future documents covering:

- package map
- node graph
- execution adapter semantics
- event log schema
- fault handling
- requirements traceability
- benchmark metrics
