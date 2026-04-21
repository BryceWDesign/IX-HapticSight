# HIL Fault Injection Strategy

This document defines the recommended fault-injection strategy for future hardware-in-the-loop (HIL) work in IX-HapticSight.

At the current repository stage, this is a **planning and evidence-discipline document**, not proof that these injections have already been run on real hardware.
Its purpose is to define:

- what kinds of faults should be injected
- why those faults matter for this repo
- what a credible fault-injection trial should record
- how injected-fault evidence should map back to repository claims

A human-facing interaction system is not credible if it only demonstrates nominal behavior.
It must also show how it fails.

---

## 1. Purpose

Fault injection exists to answer questions like:

- what happens when a critical signal goes stale
- what happens when force exceeds the intended limit
- what happens when execution stops responding
- what happens when retreat is requested but cannot complete
- what happens when the system must fall back to safe hold
- whether the event trail still explains what occurred

This matters because many of the repo’s strongest safety claims are actually **bad-case claims**, not good-case claims.

Examples:
- consent does not override safety
- safety veto can block or interrupt action
- retreat and safe hold remain explicit
- fault behavior should be structured and auditable

Fault injection is how those claims become testable.

---

## 2. Fault-Injection Philosophy

IX-HapticSight fault injection should follow these rules:

1. **Inject explicit faults, not vague chaos**
   - each injected fault should have a name, trigger method, and expected consequence

2. **One causal story per trial**
   - a fault-injection trial should make it clear what was injected and what outcome was expected

3. **Bounded escalation**
   - start with software-side or simulated injections
   - move toward HIL and physical injections only when the evidence path is ready

4. **Preserve auditability**
   - event logs, measured traces, and trial notes must make the fault visible

5. **Prefer conservative interpretation**
   - if the fault outcome is ambiguous, the claim should stay narrow

This repo should not treat “it looked fine in the demo” as a substitute for injected-fault evidence.

---

## 3. Why Fault Injection Matters Here

The repo is explicitly about:

- bounded interaction
- consent-aware behavior
- safety-gated planning and execution
- explicit fault handling
- explicit retreat and safe hold
- replayable event trails

That means fault injection is not optional theater.
It is one of the main ways to check whether the architecture behaves as claimed.

Without fault injection, the repo may show:
- good nominal flow
- clean approval path
- neat logs

But still fail under:
- stale signals
- threshold violations
- execution faults
- denied retreat conditions
- desynchronized evidence paths

Those are exactly the cases serious reviewers care about.

---

## 4. Current Repo Support for Fault-Injection Thinking

The current repo already contains structures that support a future fault-injection program:

- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `src/ohip_runtime/state.py`
- `src/ohip_runtime/runtime_service.py`
- `src/ohip_interfaces/`
- `src/ohip_logging/`
- `src/ohip_bench/`

What is still missing:
- real HIL fault-injection harnesses
- measured timing traces under fault
- actual physical backend fault injections
- evidence bundle manifests linked to those runs

So this document is laying out the strategy before those artifacts exist.

---

## 5. Fault Categories to Inject

A strong future fault-injection program should cover at least five categories.

### 5.1 Consent and authorization faults
Examples:
- missing consent where contact is requested
- stale consent
- consent revoked during approach
- consent revoked during contact
- mismatched caregiver override

Why:
- the repo claims contact is not default-permitted

---

### 5.2 Safety and hazard faults
Examples:
- session starts RED
- RED hazard appears after planning
- target region becomes invalid
- corridor suddenly becomes unsafe
- manual safety latch is triggered

Why:
- the repo claims safety remains authoritative over convenience

---

### 5.3 Sensor freshness and validity faults
Examples:
- force-torque input becomes stale
- proximity input becomes stale
- tactile stream disappears
- thermal input becomes invalid
- contradictory normalized signal state appears

Why:
- freshness and signal trust are part of the safety argument

---

### 5.4 Contact and force faults
Examples:
- measured overforce
- unexpected sustained contact
- pressure concentration exceeds threshold
- contact occurs outside intended zone
- release does not happen when expected

Why:
- bounded contact claims require bad-case testing

---

### 5.5 Execution and backend faults
Examples:
- execution backend rejects a request
- backend stops updating progress
- abort request is delayed
- retreat request is refused
- safe-hold path must be used because retreat is unavailable

Why:
- execution adapter behavior is part of the real system boundary

---

## 6. Recommended Injection Progression

Fault injection should progress in stages.

### Stage 1 — Software-path injection
Examples:
- manually set RED state
- manually remove consent
- simulate denied execution adapter response
- simulate runtime-side fault object application

Purpose:
- test architecture and event-path behavior early

### Stage 2 — Replay and benchmark-path injection
Examples:
- benchmark scenarios for denied approval
- replay sequences with expected fault markers
- event-order validation under fault

Purpose:
- make failure behavior repeatable and reviewable

### Stage 3 — Simulated backend injection
Examples:
- simulated execution adapter faults
- forced safe hold
- forced abort
- forced progress stall
- forced retreat state

Purpose:
- test execution-path fault semantics before hardware

### Stage 4 — HIL instrumentation-level injection
Examples:
- stale sensor feed
- artificial threshold exceedance
- timestamp skew
- load spike
- thermal threshold input

Purpose:
- connect fault semantics to measured signals

### Stage 5 — Physical backend / rig-level injection
Examples:
- measured overforce
- physical retreat obstruction
- actuator-side refusal or stop
- real timing under hardware fault

Purpose:
- gather the strongest bad-case evidence later

This staged approach keeps the evidence honest.

---

## 7. Recommended Initial Fault-Injection Set

If the repo had to start with the highest-value injected faults first, I would pick:

1. **Missing consent**
2. **Session RED at request start**
3. **Execution adapter rejects request**
4. **Forced abort**
5. **Forced safe hold**
6. **Overforce-like trigger path**
7. **Stale critical signal path**
8. **Retreat unavailable -> safe hold fallback**

Those eight cover much of the repo’s most important current safety story.

---

## 8. What an Injected-Fault Trial Should Record

Every serious fault-injection trial should eventually record at least:

- trial ID
- injected fault category
- injected fault method
- trigger time or trigger condition
- expected system reaction
- observed system reaction
- event log path
- measured trace path if relevant
- benchmark/scenario ID if applicable
- pass/fail/error result
- reason code
- operator note if needed

That is the minimum structure for later review.

---

## 9. Example Fault-Injection Trials

## 9.1 Missing consent trial
### Injected condition
No valid consent for contact request

### Expected behavior
- deny request
- no execution submission
- structured fault/event trail
- reason tied to consent failure

### Evidence targets
- decision status
- fault reason
- event count
- no execution status acceptance

---

## 9.2 Session RED trial
### Injected condition
Session starts in RED safety state

### Expected behavior
- deny request
- no execution
- fault/event trail tied to RED state

### Evidence targets
- decision status
- fault reason
- event trail correctness

---

## 9.3 Simulated backend reject trial
### Injected condition
Execution adapter refuses the approved request

### Expected behavior
- execution response shows rejection
- runtime event trail captures rejection
- no false success state appears

### Evidence targets
- execution status
- event trail
- session state after rejection

---

## 9.4 Forced abort trial
### Injected condition
Abort command triggered during active execution

### Expected behavior
- explicit abort transition
- execution status update reflects abort
- session state updates conservatively

### Evidence targets
- state transition events
- execution status event
- timing if available

---

## 9.5 Safe-hold fallback trial
### Injected condition
Retreat unavailable or execution degraded such that hold is safer

### Expected behavior
- explicit safe-hold transition
- structured reason code
- no silent collapse into vague stop behavior

### Evidence targets
- state transition
- execution status
- safe-hold event trail

---

## 9.6 Overforce trial
### Injected condition
Measured force exceeds threshold

### Expected behavior
- overforce recognized
- abort or retreat path begins
- event trail records reason
- physical trace aligns with trigger if measured

### Evidence targets
- threshold crossing
- event log
- retreat or abort timing
- measurement linkage

---

## 10. Fault Injection and Timing Evidence

Some of the most valuable future fault-injection evidence will be timing-sensitive.

Examples:
- fault-detection latency
- abort-command latency
- retreat start latency
- safe-hold entry latency
- event-log alignment latency

To make these claims credible later, the repo will need:
- calibration-aware timing alignment
- explicit time-source handling
- evidence bundle linkage

Right now, the architecture is being prepared for that.
It is not yet proven by the repo alone.

---

## 11. Fault Injection and Event Logs

A fault-injection trial is much stronger when the event log shows the fault story clearly.

A future reviewer should be able to ask:

- where did the fault appear in the log
- what state changed
- what reason code was emitted
- whether retreat or safe hold occurred
- whether execution status reflected the same story

This is why the current event-log schema and replay support matter so much.

Fault injection without a structured event trail is weaker.
A structured event trail without injected faults is also weaker.
They are strongest together.

---

## 12. Fault Injection and Benchmarking

The current benchmark runner is already a useful base for software-path fault injection.

Examples of benchmarkable fault scenarios:
- missing consent
- session RED
- execution rejection
- forced safe hold
- stale signal denial later
- replay/order integrity under fault

The benchmark layer should eventually become the controlled front door for many fault-injection cases, while HIL and physical rigs provide the stronger measurement path later.

---

## 13. Fault Injection and Traceability

Injected-fault evidence should map back to:

- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/governance/safety_case.md`

Examples:
- missing consent trial maps to consent invariants
- RED denial trial maps to safety-veto invariants
- overforce trial maps to force and fault invariants
- retreat unavailable trial maps to retreat and safe-hold semantics

If a fault trial cannot be traced back to a repo requirement or claim, it is less valuable than it should be.

---

## 14. What Fault Injection Does Not Automatically Prove

Even a good injected-fault trial does not automatically prove:

- full deployment safety
- certification readiness
- population-wide appropriateness
- hardware robustness under all environments
- legal or regulatory sufficiency

It does, however, make the repo’s bad-case claims much stronger than prose alone.

---

## 15. Review Questions

When evaluating a proposed injected-fault trial, ask:

1. What exact fault is being injected?
2. What exact repo claim is being tested?
3. What exact system reaction is expected?
4. What artifacts will prove that reaction happened?
5. Can the trial be repeated?
6. How will the result be traced back to repo requirements?

If those answers are weak, the fault-injection design is weak.

---

## 16. Final Rule

A safety-first interaction repo must be judged by how it handles the bad cases, not only the clean demos.

If injected faults do not produce an explicit, measurable, and reviewable story, the evidence is not strong enough.
