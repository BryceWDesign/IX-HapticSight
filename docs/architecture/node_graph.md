# Planned Node Graph

This document defines the planned runtime node graph for the upgraded IX-HapticSight architecture.

It is a target operating model for a stronger runtime-oriented repository.
It does not imply that all nodes described here already exist in the current codebase.

The current repository is still primarily a Python reference implementation under `src/ohip/`.
This document defines how that logic should be separated once runtime orchestration and ROS 2-facing layers are introduced.

---

## 1. Design Goal

The node graph is intended to make these responsibilities explicit:

- who owns interaction state
- who evaluates consent state
- who evaluates hazard state
- who fuses contact-related signals
- who authorizes or vetoes execution
- who records structured event history
- who provides replay and benchmark observability

The graph is intentionally conservative.
It prioritizes inspection and control over convenience.

---

## 2. Top-Level Planned Nodes

The primary planned nodes are:

1. `interaction_coordinator_node`
2. `consent_service_node`
3. `safety_evaluator_node`
4. `contact_planner_node`
5. `signal_fusion_node`
6. `execution_adapter_node`
7. `event_logger_node`
8. `benchmark_runner_node`
9. `replay_publisher_node`

Not all of these need to exist on day one.
The point of the graph is to reserve clean responsibility boundaries.

---

## 3. Node Responsibilities

### 3.1 `interaction_coordinator_node`

Purpose:
- owns high-level interaction session flow
- coordinates state transitions
- requests checks from consent and safety services
- routes approved requests to planning and execution
- initiates retreat or safe hold when required

Inputs:
- operator or application interaction requests
- state machine timing events
- safety veto notifications
- consent decisions
- signal health summaries

Outputs:
- interaction state updates
- planning requests
- execution requests
- retreat requests
- structured transition events

This is the central orchestrator, but it must not silently absorb all logic.
It coordinates. It does not replace safety or policy ownership.

---

### 3.2 `consent_service_node`

Purpose:
- evaluates whether requested interaction is permitted
- validates consent freshness
- evaluates caregiver or profile-specific allowances
- returns explicit authorization, denial, or requires-refresh results

Inputs:
- interaction request
- subject profile
- consent record
- policy bundle version

Outputs:
- consent decision
- denial reason
- audit metadata
- consent freshness status

This node should remain deterministic and heavily auditable.

---

### 3.3 `safety_evaluator_node`

Purpose:
- evaluates whether the requested or current interaction remains allowed from a safety standpoint
- can issue slowdown, block, abort, retreat, or safe-hold recommendations
- acts as the main safety-veto node

Inputs:
- fused signal state
- force/torque data
- tactile data
- proximity data
- thermal data
- scene hazard summary
- requested interaction target
- current interaction state

Outputs:
- safety status
- veto decision
- retreat trigger
- safe-hold trigger
- overforce indication
- hazard reasoning metadata

This node is safety-critical in concept.
Its decisions must be explainable and loggable.

---

### 3.4 `contact_planner_node`

Purpose:
- turns an approved interaction request into a bounded approach, pre-contact, contact, or retreat plan

Inputs:
- authorized interaction request
- subject geometry metadata
- rest/support posture rules
- current state
- safety constraints
- contact-state summary

Outputs:
- bounded interaction plan
- pre-contact checkpoints
- retreat plan
- posture targets
- planner status and failure reasons

This node should not decide whether contact is ethically or safely allowed.
It should plan within already-approved constraints.

---

### 3.5 `signal_fusion_node`

Purpose:
- normalizes and fuses measured signals into a stable runtime summary for safety and planning consumption

Inputs:
- force-torque interface data
- tactile interface data
- proximity interface data
- thermal interface data
- signal freshness and health metadata

Outputs:
- fused contact-state estimate
- signal health state
- freshness state
- confidence metadata
- normalized contact zone information

This node helps keep device-specific assumptions out of coordinator, planner, and safety logic.

---

### 3.6 `execution_adapter_node`

Purpose:
- converts approved plans into runtime backend commands
- enforces local execution constraints
- handles abort and retreat command routing
- reports execution acknowledgements and faults

Inputs:
- bounded plan segments
- velocity or pose targets
- abort commands
- retreat commands
- backend capability metadata

Outputs:
- execution acknowledgements
- command delivery status
- execution faults
- current execution progress

This node is an adapter boundary.
It should be replaceable without rewriting consent or safety logic.

---

### 3.7 `event_logger_node`

Purpose:
- writes structured event history for transitions, approvals, denials, vetoes, and execution outcomes

Inputs:
- transition events
- decision events
- planner events
- sensor summary events
- replay markers
- benchmark result events

Outputs:
- event log files
- evidence bundle entries
- structured audit streams

This node should reduce dependence on ad hoc console output.

---

### 3.8 `benchmark_runner_node`

Purpose:
- drives deterministic scenario execution for consent, hazard, contact, and retreat benchmark suites

Inputs:
- scenario definitions
- seed values
- replay or simulation fixtures
- benchmark configuration

Outputs:
- scenario result artifacts
- metrics summaries
- pass/fail assertions
- benchmark event streams

This node is not part of normal runtime operation.
It exists for disciplined evaluation.

---

### 3.9 `replay_publisher_node`

Purpose:
- replays logged sessions for audit, debugging, and benchmark comparison

Inputs:
- event log bundles
- replay configuration
- optional timing scale controls

Outputs:
- replayed state and event streams
- reproducibility traces
- benchmark comparison runs

This node enables after-action inspection without rewriting scenarios by hand.

---

## 4. Suggested Communication Pattern

The preferred flow is:

1. external request arrives at `interaction_coordinator_node`
2. coordinator asks `consent_service_node` for authorization
3. coordinator asks `safety_evaluator_node` for current go/no-go status
4. coordinator requests fused signal state from `signal_fusion_node`
5. if authorized and safe, coordinator asks `contact_planner_node` for a bounded plan
6. planner returns a plan
7. coordinator sends the plan to `execution_adapter_node`
8. all major decisions and transitions are sent to `event_logger_node`
9. benchmark and replay tooling may observe or drive the same interfaces offline

This preserves clear authority:
- consent authorizes
- safety vetoes
- planner constrains plan generation
- execution carries out commands
- logger records the trail

---

## 5. Node Graph Summary

A conceptual graph:

- external request source
  - to `interaction_coordinator_node`

- `interaction_coordinator_node`
  - queries `consent_service_node`
  - queries `safety_evaluator_node`
  - queries `signal_fusion_node`
  - commands `contact_planner_node`
  - commands `execution_adapter_node`
  - emits events to `event_logger_node`

- `signal_fusion_node`
  - ingests sensor interfaces
  - publishes fused signal state to:
    - `safety_evaluator_node`
    - `contact_planner_node`
    - `interaction_coordinator_node`

- `benchmark_runner_node`
  - drives or simulates:
    - `interaction_coordinator_node`
    - `signal_fusion_node`
    - `event_logger_node`

- `replay_publisher_node`
  - feeds historical event streams to:
    - analysis tools
    - benchmark comparison tools
    - optional visualization tools

---

## 6. State Ownership Intent

The node graph should clarify ownership of state categories.

### `interaction_coordinator_node`
owns:
- current interaction session state
- transition intent
- coordination timers

### `consent_service_node`
owns:
- consent evaluation result
- freshness status
- denial reason metadata

### `safety_evaluator_node`
owns:
- veto status
- retreat recommendation
- safe-hold recommendation
- fault gating outcome

### `signal_fusion_node`
owns:
- normalized signal summary
- contact-state summary
- signal health and freshness

### `execution_adapter_node`
owns:
- execution progress
- local execution fault reporting
- command acknowledgement state

### `event_logger_node`
owns:
- immutable or append-only event record generation
- event serialization

This separation prevents conflicting hidden authority.

---

## 7. Fault Handling Intent

The graph must support clean fault routing.

Examples:
- stale proximity input
- thermal threshold exceedance
- overforce event
- consent refresh failure
- execution backend refusal
- operator stop request
- watchdog timeout

The desired route is:

1. fault is detected by the node closest to its source
2. fault is emitted as structured status
3. `interaction_coordinator_node` transitions appropriately
4. `event_logger_node` records the sequence
5. `execution_adapter_node` receives abort or retreat if needed

Safety-critical veto paths should not depend on a noncritical visualization layer or human console reading.

---

## 8. What This Graph Is Not

This node graph is not intended to imply:

- fully autonomous social behavior
- production-ready deployment
- hardware certification
- complete sensor coverage
- final ROS topic naming
- final message type design

It is a responsibility graph first.

---

## 9. Near-Term Build Order

The most sensible implementation order is:

1. `interaction_coordinator_node`
2. `consent_service_node`
3. `safety_evaluator_node`
4. `contact_planner_node`
5. `signal_fusion_node`
6. `execution_adapter_node`
7. `event_logger_node`
8. `benchmark_runner_node`
9. `replay_publisher_node`

This order creates control first, then sensing and execution, then evidence tooling.

---

## 10. Review Rule

A new node is justified only if it improves at least one of these:

- safety boundary clarity
- state ownership clarity
- replayability
- backend replaceability
- benchmarkability
- auditability

If a new node adds indirection without clarifying authority, it should not be added.
