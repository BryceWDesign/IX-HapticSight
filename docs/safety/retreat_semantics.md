# Retreat Semantics

This document defines the planned retreat semantics for IX-HapticSight as the repository evolves into a stronger runtime-oriented interaction stack.

Retreat is one of the most important bounded behaviors in this project.
It is the difference between a system that merely notices a problem and a system that can move away from a problem in a disciplined, inspectable way.

This document is written to keep retreat behavior explicit before additional runtime and execution code are added.

---

## 1. Purpose

The retreat model exists to answer these questions clearly:

- what retreat means
- when retreat should happen
- how retreat differs from abort and safe hold
- what information a retreat request should carry
- what completion or failure should look like
- what must be logged for later review

Retreat is not just “move backward.”
It is a safety-relevant state transition with specific intent.

---

## 2. Core Definition

In IX-HapticSight, **retreat** means:

> a bounded movement away from the current interaction condition, contact zone, or approach corridor toward a safer configuration, initiated because continuing the current interaction is no longer acceptable or no longer justified.

A retreat may be triggered:

- before contact
- during contact
- immediately after contact
- after an abort when motion away remains safe and feasible

A retreat is therefore both:
- a movement class
- a recovery intent

---

## 3. Retreat Compared to Other Outcomes

### 3.1 Abort

Abort means:
- stop the current action as quickly as allowed by the execution context

Abort does **not** necessarily mean:
- move away
- return to rest
- recover to a known neutral posture

Abort is about interruption.

---

### 3.2 Retreat

Retreat means:
- move away from the unsafe or no-longer-authorized interaction condition in a bounded, reviewable way

Retreat is about withdrawal.

---

### 3.3 Safe Hold

Safe hold means:
- maintain or stabilize in place because movement itself is unsafe, unavailable, or not yet justified

Safe hold may occur:
- after abort
- instead of retreat
- after failed retreat
- during backend failure

Safe hold is about controlled non-movement.

---

## 4. Why Retreat Must Be Explicit

A system involved in human-facing interaction cannot collapse every adverse outcome into one vague “stop” behavior.

Examples:
- a contact interaction may need separation from the person
- a near-contact approach may need to back out of a corridor
- a hazard intrusion may require moving to a safer posture
- consent revocation may require ending contact and withdrawing

If the system only “stops,” it may remain too close, too ambiguous, or physically awkward.

Retreat exists to make withdrawal behavior:
- bounded
- explainable
- testable
- benchmarkable

---

## 5. Retreat Triggers

Retreat may be appropriate under any of the following classes of condition.

### 5.1 Safety-triggered retreat
Examples:
- RED-zone intrusion
- unsafe corridor state
- overforce
- thermal threshold exceedance
- stale critical signal during active interaction

---

### 5.2 Consent-triggered retreat
Examples:
- consent revoked during approach
- consent revoked during contact
- operator-issued stop with configured withdrawal behavior
- policy downgrade that invalidates current interaction mode

---

### 5.3 Planning-triggered retreat
Examples:
- pre-contact verification failed after partial approach
- target moved into an invalid geometry
- contact plan invalidated during execution
- continuation no longer satisfies bounded constraints

---

### 5.4 Execution-triggered retreat
Examples:
- backend indicates current action cannot continue safely
- command succeeded only partially and requires withdrawal
- degraded execution mode requires exit from interaction zone

---

## 6. Retreat Preconditions

A retreat request should only be issued when one of the following is true:

1. withdrawal motion is safer than remaining where the system is
2. the system is in or near a human-facing interaction zone that should be exited
3. policy or consent semantics no longer justify continued proximity or contact
4. an abort alone would leave the system in an undesirable or ambiguous posture

If none of those are true, safe hold may be the better outcome.

---

## 7. Required Retreat Inputs

A serious retreat request should include, or be able to derive, the following:

- `session_id`
- `interaction_state`
- `retreat_reason`
- `retreat_class`
- `current_contact_state`
- `target_retreat_mode`
- `speed_bound`
- `active_force_profile`
- `expected_end_state`
- `path_constraints` where relevant
- `requires_contact_break_first` flag when relevant
- `fallback_if_retreat_fails`

A retreat request that lacks reason and target state is weak and harder to audit.

---

## 8. Retreat Classes

The runtime should distinguish retreat classes rather than treating every withdrawal identically.

### 8.1 Micro-retreat
A short withdrawal used to re-establish safer spacing without fully leaving the interaction context.

Possible use:
- pre-contact uncertainty
- near-contact misalignment
- soft hazard caution state

Expected end state:
- verify or pre-contact state

---

### 8.2 Full retreat
A deliberate movement out of the current interaction zone toward a safer posture or neutral spacing.

Possible use:
- consent revoked
- hard hazard
- overforce
- failed contact verification

Expected end state:
- safe hold, rest, or idle-adjacent recovery state

---

### 8.3 Emergency retreat
A maximally bounded withdrawal behavior under urgent but still movable conditions.

Possible use:
- immediate hazard but motion still available
- dangerous proximity while not yet latched into safe hold

Expected end state:
- safe hold or latched recovery state

This class should be used sparingly and only when documented.

---

### 8.4 Planned disengagement retreat
A non-emergency withdrawal after successful or intentionally ended interaction.

Possible use:
- end of bounded support interaction
- end of demonstration cycle
- return to neutral after safe completion

Expected end state:
- rest or idle posture

This class exists so not every retreat is treated as a failure event.

---

## 9. Retreat End States

A retreat should specify or imply its intended end state.

Common end states include:

- `VERIFY`
- `IDLE`
- `REST`
- `SAFE_HOLD`
- `FAULT_LATCHED`

Examples:
- revocation during approach may retreat to `VERIFY` or `IDLE`
- overforce during contact may retreat to `SAFE_HOLD`
- execution backend instability may retreat if possible, then enter `SAFE_HOLD`
- planned disengagement may retreat to `REST`

A retreat without a clear end state is underspecified.

---

## 10. Retreat and Contact Relationship

Retreat semantics depend strongly on whether contact is active.

### 10.1 No active contact
Retreat can often begin immediately if spacing and corridor conditions allow.

Examples:
- invalidated approach
- dynamic obstacle entered corridor
- consent check failed late

---

### 10.2 Active intended contact
Retreat may require:
- controlled contact break
- speed reduction
- stricter force monitoring
- explicit separation stage before larger movement

Examples:
- support contact ended
- consent revoked while touching
- overforce requiring immediate but bounded disengagement

---

### 10.3 Unintended or uncertain contact
Retreat may need to begin only after:
- aborting ongoing motion
- evaluating whether movement worsens contact
- falling back to safe hold if movement is riskier than staying still

This is one reason retreat and safe hold must remain separate concepts.

---

## 11. Retreat Priority

Retreat is not always the first step.

A practical order is:

1. detect fault or trigger
2. determine whether abort is required immediately
3. determine whether retreat is safer than holding
4. if yes, execute retreat
5. if no, enter safe hold and report retreat as unavailable or deferred

This preserves the distinction between:
- interruption
- withdrawal
- immobilization

---

## 12. Retreat Failure

A retreat can fail.
The system must be prepared to say so explicitly.

Examples of retreat failure:
- backend rejected retreat plan
- no valid retreat path available
- motion unsafe due to uncertain state
- retreat interrupted by higher-priority fault
- hardware unavailable
- force/contact conditions made motion unsafe

A retreat failure should produce:
- explicit structured event
- failure reason
- resulting fallback state
- indication whether safe hold was entered
- indication whether a fault latched

Retreat failure must not disappear into generic “execution failed” noise.

---

## 13. Logging Requirements

Each retreat event should eventually include:

- `retreat_id`
- `session_id`
- `retreat_reason`
- `retreat_class`
- `trigger_source`
- `start_timestamp`
- `end_timestamp` when completed
- `initial_state`
- `target_end_state`
- `actual_end_state`
- `contact_active` flag
- `success` flag
- `failure_reason` if any
- `fallback_used` if any

These records are important for:
- replay
- benchmarking
- incident analysis
- safety-case evidence later

---

## 14. Benchmark Scenarios for Retreat

The future benchmark suite should include retreat-specific scenarios such as:

- late consent revocation during approach
- hard hazard intrusion during pre-contact
- overforce during contact
- thermal exceedance requiring withdrawal
- retreat unavailable, safe hold entered
- planned disengagement after successful interaction
- backend rejects retreat command
- stale critical signal causes abort followed by retreat

These scenarios will help measure whether retreat behavior is:
- timely
- bounded
- distinguishable
- auditable

---

## 15. Current Repository Mapping

At the present repository stage, retreat-related semantics are distributed conceptually across:

- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/contact_planner.py`
- `src/ohip/rest_pose.py`
- `src/ohip/safety_gate.py`

What is still missing:
- explicit retreat schema
- explicit retreat state tests
- execution adapter retreat interface
- structured retreat logging
- dedicated retreat benchmarks

This document exists to define those expectations before implementation expands.

---

## 16. Review Questions

When evaluating retreat-related code, ask:

1. Is this actually retreat, or just abort?
2. Is the retreat reason explicit?
3. Is the target end state explicit?
4. Is retreat safer than safe hold in this case?
5. Is contact status accounted for?
6. Can failure be reported clearly?
7. Can this behavior be replayed and benchmarked later?

If the answer to any of these is no, the retreat semantics are too weak.

---

## 17. Final Rule

Retreat should be treated as a bounded safety behavior, not as an afterthought.

A system that can only stop is incomplete.
A system that can withdraw clearly, conservatively, and explainably is far stronger.
