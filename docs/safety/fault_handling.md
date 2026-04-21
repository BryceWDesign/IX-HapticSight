# Fault Handling Model

This document defines the planned fault-handling model for IX-HapticSight as the repository evolves from a reference implementation into a stronger runtime-oriented interaction stack.

The project is concerned with bounded human-facing behavior.
That means faults cannot be treated as generic technical nuisances.
A fault in this system may change whether contact is allowed, whether motion must stop, whether retreat is possible, and whether future action must remain latched off until explicitly cleared.

This document is written to keep those rules explicit before additional runtime code is added.

---

## 1. Purpose

The fault-handling model exists to answer five questions clearly:

1. what counts as a fault
2. how faults are classified
3. what state changes faults should trigger
4. what logging and evidence they must produce
5. what conditions are required for recovery

The goal is not to maximize uptime at all costs.
The goal is to fail conservatively and observably.

---

## 2. Fault-Handling Philosophy

The project follows these principles:

- faults must be explicit
- serious faults must be difficult to ignore
- safety-relevant faults must be structured and replayable
- ambiguous conditions should not silently pass as normal
- recovery behavior must be documented, not improvised

This is especially important because the system may be involved in:

- pre-contact motion
- bounded physical contact
- support posture generation
- retreat behavior
- hazard-aware veto behavior

---

## 3. Fault Classes

Faults should be classified by consequence, not just by source.

### 3.1 Informational Fault
A noncritical issue that should be logged but does not directly require motion stop.

Examples:
- optional telemetry stream unavailable
- noncritical benchmark metadata missing
- delayed but noncritical analytics export

Expected behavior:
- log event
- continue if no safety path depends on it

---

### 3.2 Degraded-Mode Fault
A condition that reduces confidence or capability and may narrow behavior, but does not automatically require hard stop.

Examples:
- one noncritical sensor unavailable while a safer fallback exists
- reduced scene confidence outside active contact zone
- replay-only tool failure during live runtime

Expected behavior:
- enter degraded mode if defined
- narrow permitted behavior
- surface explicit degraded status
- log entry and exit from degraded mode

---

### 3.3 Blocking Fault
A condition that should prevent a requested action from starting.

Examples:
- missing valid consent for contact
- required signal freshness unavailable before approach
- invalid force profile selection
- backend unavailable for commanded action
- invalid retreat plan before execution starts

Expected behavior:
- deny or reject action
- do not begin motion
- log reason in structured form

---

### 3.4 Abort Fault
A condition discovered during execution that should interrupt the current action.

Examples:
- hard hazard intrusion
- overforce
- thermal threshold exceedance
- consent revoked during execution
- stale critical signal during contact
- execution watchdog timeout

Expected behavior:
- abort active motion
- transition to abort, retreat, or safe-hold path
- preserve structured reason code
- log event with timing information

---

### 3.5 Latched Critical Fault
A severe fault that should remain visible and should not silently clear itself.

Examples:
- repeated overforce beyond threshold
- execution backend fault in active contact context
- contradictory state authority
- corrupted policy bundle integrity
- emergency stop event
- unrecoverable retreat failure in a safety-relevant context

Expected behavior:
- enter latched critical fault state
- block new interaction execution
- require explicit clear condition or operator action according to documented rules
- preserve evidence trail

---

## 4. Fault Sources

The same fault class can be triggered by different sources.

### 4.1 Policy and consent faults
Examples:
- missing consent
- stale consent
- revoked consent
- mismatched caregiver authority
- unsupported interaction mode

---

### 4.2 Safety and hazard faults
Examples:
- RED-zone intersection
- dynamic obstacle intrusion
- unsafe corridor geometry
- invalid clearance state
- impossible safe approach state

---

### 4.3 Contact and force faults
Examples:
- overforce
- unexpected sustained contact
- contact outside intended target zone
- contact dwell time exceedance
- contact without confirmed pre-contact state

---

### 4.4 Sensor and signal faults
Examples:
- stale signal
- out-of-range sensor value
- sensor health invalid
- timestamp regression
- missing required modality
- conflicting fused state

---

### 4.5 Execution faults
Examples:
- backend unavailable
- command rejected
- motion timeout
- execution stopped unexpectedly
- retreat command failure
- safe-hold command failure

---

### 4.6 Configuration and integrity faults
Examples:
- invalid policy file
- failed bundle hash check
- unknown profile identifier
- mismatched schema version
- malformed force-limit definition

---

## 5. Required Fault Fields

Every structured fault record should eventually include, at minimum:

- `fault_id`
- `fault_class`
- `fault_source`
- `reason_code`
- `severity`
- `timestamp`
- `session_id` when applicable
- `interaction_state`
- `execution_state` when applicable
- `latched` flag
- `requires_abort` flag
- `requires_retreat` flag
- `requires_safe_hold` flag
- `clearance_condition` or `recovery_note`
- relevant threshold or freshness metadata if applicable

A fault that cannot be tied to a reason code is weak evidence and poor audit material.

---

## 6. Fault-to-State Expectations

The following mappings should hold unless a documented exception exists.

### Informational Fault
Likely outcome:
- remain in current state
- record event only

### Degraded-Mode Fault
Likely outcome:
- remain operational with narrowed behavior
- annotate degraded capability
- potentially restrict contact initiation

### Blocking Fault
Likely outcome:
- remain in idle, verify, or request-denied path
- no execution begins

### Abort Fault
Likely outcome:
- interrupt execution
- transition to abort, retreat, or safe-hold path

### Latched Critical Fault
Likely outcome:
- enter critical fault or safe-hold path
- block further interaction until explicit recovery criteria are met

These are behavioral expectations, not yet final code guarantees.

---

## 7. Recovery Model

Recovery should be based on fault class and evidence, not wishful optimism.

### 7.1 Auto-recoverable conditions
These should be rare and carefully bounded.

Possible examples:
- noncritical telemetry reconnect
- temporary degraded signal restored before action begins
- replay visualization failure in offline mode

Auto-recovery requires:
- a documented clear condition
- no active contradiction with safety invariants
- a log event showing recovery

---

### 7.2 Operator-cleared conditions
These require explicit acknowledgement or restart action.

Possible examples:
- backend restart after rejection
- degraded mode exit after manual verification
- policy reload after config correction

Clear requirements:
- documented operator action
- evidence that the underlying issue is resolved
- logged clear event

---

### 7.3 Hard-latched conditions
These should not clear themselves.

Possible examples:
- emergency stop
- integrity failure in policy bundle
- repeated unexplained overforce
- retreat failure while safety depends on retreat success

Clear requirements:
- explicit, documented reset path
- evidence that the cause was addressed
- preserved event history

---

## 8. Abort, Retreat, and Safe-Hold Relationship

Fault handling must keep these three outcomes distinct.

### Abort
Meaning:
- stop current execution as quickly as allowed

Typical trigger:
- immediate violation or hard veto during action

---

### Retreat
Meaning:
- move away from current interaction zone or toward safer posture

Typical trigger:
- active contact or approach needs bounded withdrawal

---

### Safe Hold
Meaning:
- stop or stabilize in place because motion is unsafe or unavailable

Typical trigger:
- retreat impossible
- backend degraded
- motion itself creates more uncertainty

A fault record should indicate which of these was requested and which was actually achieved.

---

## 9. Fault Priority

When multiple conditions occur, the runtime should prefer the highest-priority safety-relevant interpretation.

A sensible priority order is:

1. emergency stop / hard latched critical fault
2. hard safety veto / immediate abort fault
3. consent revocation during active interaction
4. overforce / thermal / stale critical signal
5. blocking pre-execution validation fault
6. degraded-mode fault
7. informational fault

This order may be refined later, but the core idea must remain:
severe safety-relevant faults should not be buried under convenience logic.

---

## 10. Logging Requirements

Faults are only useful if they can be inspected later.

Each serious fault should generate:
- a structured event
- a state transition record if a state changed
- a reason code
- any relevant threshold or freshness context
- a recovery or latch status

Critical or latched faults should also be included in:
- replay artifacts
- benchmark metrics where relevant
- safety-case traceability later in the project

---

## 11. Benchmark-Relevant Fault Scenarios

The future benchmark suite should include scenarios such as:

- stale consent before contact request
- consent revoked during active approach
- RED-zone intrusion during motion
- overforce during contact
- thermal threshold exceedance
- missing required signal freshness
- retreat backend rejection
- safe-hold fallback after retreat failure
- conflicting sensor fusion result
- policy bundle integrity failure

These scenarios will help turn the fault model into something measurable.

---

## 12. Current Repository Mapping

At the present repository baseline, fault-relevant behavior is primarily distributed across:

- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`
- `src/ohip/nudge_scheduler.py`
- `src/ohip/safety_gate.py`
- `docs/state_machine.md`
- `docs/spec.md`

What is still missing:
- dedicated fault schema package
- latched fault manager
- structured event logger
- replay-aware fault artifacts
- dedicated fault test suite

This document exists to define those expectations before implementation spreads.

---

## 13. Review Questions

When new fault-related code is added, ask:

1. Is the fault class explicit?
2. Is the consequence documented?
3. Does the system block, abort, retreat, or safe-hold appropriately?
4. Is the fault loggable in structured form?
5. Can the fault be replayed or benchmarked later?
6. Is recovery defined, or is the system silently forgiving itself?

If the answer to any of these is no, the handling is probably too weak.

---

## 14. Final Rule

The system should prefer a visible conservative fault response over an invisible permissive continuation.

If something important is uncertain, the repository should make that uncertainty obvious and bounded.
