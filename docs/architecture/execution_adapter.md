# Execution Adapter Semantics

This document defines the planned execution adapter boundary for IX-HapticSight.

The project currently contains protocol and planning logic in `src/ohip/`, but it does not yet contain a dedicated runtime execution layer. This document describes the execution contract that should exist as the repository evolves into a stronger runtime-oriented architecture.

The purpose of the execution adapter is to keep bounded interaction logic separate from backend-specific command transport.

---

## 1. Why an Execution Adapter Exists

IX-HapticSight should not tie its core safety, consent, and contact-planning logic directly to one robot backend or simulator.

A dedicated execution adapter layer exists to:

- translate bounded plans into backend commands
- enforce local execution constraints
- report execution acknowledgements and failures
- support abort and retreat behavior
- isolate backend-specific details from protocol logic
- allow simulation and hardware backends to share the same high-level behavior model

Without this boundary, backend assumptions leak into planning and safety code and make the repository harder to audit.

---

## 2. Scope of the Execution Adapter

The execution adapter is responsible for converting already-approved, already-bounded plans into executable steps.

It is **not** responsible for:

- deciding whether consent is valid
- deciding whether contact is ethically allowed
- deciding whether safety vetoes should be ignored
- inventing new goals outside the approved plan
- weakening hard limits for convenience

The execution adapter is allowed to reject an execution request if it cannot honor safety or backend constraints.

---

## 3. Upstream Dependencies

The execution adapter should receive input from runtime coordination and planning layers, not directly from raw operator intent.

Expected upstream sources:

- interaction coordinator
- contact planner
- retreat planner
- safety evaluator
- watchdog or fault manager

The execution adapter should assume that upstream layers have already performed:

- consent checks
- policy checks
- hazard evaluation
- force-limit selection
- basic bounded-plan generation

The adapter may still perform local validation before executing.

---

## 4. Planned Responsibilities

The execution adapter boundary should handle the following responsibilities.

### 4.1 Command translation
Translate bounded motion or posture plans into backend-specific commands.

Examples:
- joint targets
- Cartesian pose targets
- velocity-limited trajectories
- retreat motions
- safe-hold postures

### 4.2 Local validation
Validate that a command is executable under current backend assumptions.

Examples:
- missing target frame
- target outside backend workspace model
- invalid pose vector
- backend unavailable
- motion mode incompatible with requested action

### 4.3 Limit application
Apply or verify execution-side constraints such as:

- velocity scaling
- acceleration limits
- jerk limits where supported
- workspace constraints
- backend collision-check mode selection
- execution timeout bounds

### 4.4 Abort handling
Accept and prioritize abort commands over normal execution flow.

Examples:
- emergency stop request
- hazard-induced abort
- overforce abort
- stale-signal abort
- consent revocation

### 4.5 Retreat handling
Accept retreat requests and execute a safe retreat or safe hold behavior.

Examples:
- reverse out of contact zone
- move to a predefined neutral posture
- hold position if motion is unsafe
- report inability to retreat if backend constraints prevent motion

### 4.6 Execution reporting
Return structured execution status to the rest of the system.

Examples:
- accepted
- running
- completed
- partially completed
- rejected
- aborted
- faulted
- retreat complete
- retreat failed

---

## 5. Planned Interface Contract

A future implementation may represent the adapter through a stable interface class.

A conceptual shape is:

- `can_execute(plan) -> ExecutionCheckResult`
- `execute(plan) -> ExecutionStartResult`
- `abort(reason) -> ExecutionAbortResult`
- `retreat(plan, reason) -> ExecutionRetreatResult`
- `get_status() -> ExecutionStatus`
- `get_backend_capabilities() -> BackendCapabilities`

The exact code shape may change, but the semantic contract should remain stable.

---

## 6. Required Input Semantics

The adapter should only accept plans that are already explicit.

A valid execution request should include, or be able to derive:

- interaction/session identifier
- plan identifier
- target posture or motion segment
- active force-limit profile identifier
- speed or timing constraints
- relevant frame metadata
- plan class
- execution mode
- timeout or completion expectation
- reason code for retreat or abort if applicable

A plan that lacks essential metadata should be rejected rather than guessed.

---

## 7. Required Output Semantics

The adapter should emit structured responses rather than free-form strings.

A useful execution response should include:

- status code
- backend timestamp
- execution identifier
- acknowledgement state
- failure reason if any
- backend fault indicator
- current motion mode
- retreat state when relevant
- whether the action is reversible
- any downgraded execution condition

This supports replay, audit, and benchmark comparison later.

---

## 8. State Expectations

The execution adapter should maintain a minimal internal state model.

Recommended execution states:

- `IDLE`
- `READY`
- `EXECUTING`
- `ABORTING`
- `RETREATING`
- `SAFE_HOLD`
- `FAULTED`
- `UNAVAILABLE`

These are backend-facing states, not the full interaction protocol state machine.

The runtime coordinator should not have to infer execution state from scattered backend logs.

---

## 9. Abort Semantics

Abort behavior must be clear and prioritized.

### Hard rule
If a valid abort command is received, the adapter must stop normal execution flow as soon as backend behavior allows.

Abort reasons may include:
- emergency stop
- operator stop
- overforce
- hazard violation
- thermal threshold exceedance
- stale critical signal
- execution watchdog timeout
- consent revoked

The adapter should report:

- whether abort was acknowledged
- whether motion ceased
- whether the system entered safe hold
- whether follow-on retreat is possible or blocked

Abort is not a soft suggestion.
It is a mode change.

---

## 10. Retreat Semantics

Retreat is distinct from abort.

Abort means:
- stop the current action

Retreat means:
- execute a bounded movement away from the interaction zone or toward a safer configuration

A retreat request should include:
- retreat reason
- target retreat posture or path
- speed bound
- whether contact is currently active
- whether a hold-before-retreat is required

If retreat cannot be completed, the adapter must report the failure clearly rather than silently falling back to undefined behavior.

---

## 11. Safety Boundary Rules

The adapter should never:

- expand force limits on its own
- reinterpret a blocked command as allowed
- initiate new contact not described in the plan
- continue execution after a latched hard veto unless explicitly cleared by system logic
- suppress execution faults from the event log

The adapter may be conservative and reject execution.
It may not become permissive on its own.

---

## 12. Backend Replaceability Goal

The execution adapter boundary is intended to support multiple backends over time.

Examples:
- pure simulation backend
- local test backend
- ROS 2 bridge
- motion-planning backend
- future physical robot controller bridge

The goal is that the planner and safety logic remain stable while the backend changes.

This keeps the repository architecture stronger and easier to test.

---

## 13. Logging Requirements

The execution adapter should emit structured events for:

- plan acceptance
- plan rejection
- execution start
- execution completion
- execution abort
- retreat start
- retreat completion
- retreat failure
- backend fault
- degraded mode entry
- backend unavailability

These events are important for:
- replay tooling
- benchmark scoring
- debugging
- safety-case traceability

---

## 14. Benchmark-Relevant Metrics

The execution adapter is a major source of runtime metrics.

Examples of useful metrics:
- command acceptance latency
- abort acknowledgement latency
- retreat start latency
- retreat completion time
- execution rejection rate by reason
- backend fault frequency
- safe-hold entry count
- partial execution incidence
- timeout incidence

These metrics should eventually feed benchmark and evidence tooling.

---

## 15. Current Repository Implication

At the current repository stage, the execution adapter is still mostly conceptual.

The existing files that feed this future boundary are:

- `src/ohip/contact_planner.py`
- `src/ohip/rest_pose.py`
- `src/ohip/safety_gate.py`

Those files express what the system wants to do and what should be blocked.
They do not yet provide a runtime-grade execution contract.

This document exists to keep that future contract disciplined before code growth makes the boundary muddy.

---

## 16. Review Questions for Adapter Code

When execution adapter code is added, reviewers should ask:

1. Does this code only execute already-approved plans?
2. Does it preserve hard abort priority?
3. Can it report failures in structured form?
4. Does it avoid inventing policy decisions?
5. Can it be replaced without rewriting the protocol core?
6. Does it preserve replay and benchmark usefulness?

If the answer to any of those is no, the adapter design is drifting.

---

## 17. Final Rule

The execution adapter should be a narrow bridge, not a second brain.

Its job is to execute bounded intent safely, report what happened, and refuse what it cannot do without violating constraints.
