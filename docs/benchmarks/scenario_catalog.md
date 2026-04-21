# Benchmark Scenario Catalog

This document describes the current built-in benchmark scenarios for IX-HapticSight and the intended direction for future scenario expansion.

The purpose of the scenario catalog is simple:

- define what cases currently exist
- define what each case is testing
- show what evidence each case does and does not provide
- make future coverage gaps obvious

This document is not a substitute for the actual scenario definitions in code.
It is the reviewer-facing map of those scenarios.

---

## 1. Purpose

The benchmark catalog exists so a reviewer can answer:

- what scenarios are currently implemented
- what repository behavior each scenario checks
- what outcome is expected
- which benchmark domains are currently covered
- which important cases are still missing

A serious benchmark system should make scenario coverage visible, not hide it inside code.

---

## 2. Current Catalog Location

The current built-in scenario catalog lives in:

- `src/ohip_bench/scenarios.py`

The benchmark runner consumes those scenario objects through:

- `src/ohip_bench/runner.py`

The supporting result structures live in:

- `src/ohip_bench/models.py`

The current benchmark overview and reporting helpers live in:

- `docs/benchmarks/overview.md`
- `src/ohip_bench/reporting.py`

---

## 3. Current Implemented Scenarios

At the current repository stage, the built-in catalog is intentionally small and focused.

The current core catalog includes:

1. `consent-approved-001`
2. `consent-denied-001`
3. `safety-red-001`

These are deterministic repository scenarios, not physical deployment scenarios.

---

## 4. Scenario Details

## 4.1 `consent-approved-001`

### Title
**Explicit consent allows support contact**

### Domain
`CONSENT`

### What it checks
This scenario checks that a support-contact request is:

- allowed when explicit consent exists
- considered executable when runtime safety remains acceptable
- accepted by the simulated execution adapter

### Expected result
- decision status: `APPROVED`
- executable: `True`
- execution status: `ACCEPTED`

### Why it matters
This is the benchmark happy path for the current repo.
It proves the repo can move from:
- explicit consent
- valid request
- acceptable safety conditions
to:
- approved coordinated behavior
- accepted execution request
- structured event output

### What it does not prove
It does not prove:
- physical contact safety
- real robot execution quality
- actual force quality
- human comfort

---

## 4.2 `consent-denied-001`

### Title
**Missing consent blocks support contact**

### Domain
`CONSENT`

### What it checks
This scenario checks that a support-contact request is:

- denied when explicit consent is absent
- not treated as executable
- associated with the expected fault reason

### Expected result
- decision status: `DENIED`
- executable: `False`
- fault reason: `consent_missing_or_invalid`

### Why it matters
This is one of the most important current logic-path benchmarks because it verifies that contact is not treated as default-permitted behavior.

It gives evidence that the runtime path respects:
- missing consent
- blocked request behavior
- structured fault/event emission

### What it does not prove
It does not prove:
- every possible consent edge case
- consent freshness expiry behavior
- revocation-during-execution behavior
- multi-actor authorization behavior

Those remain future benchmark targets.

---

## 4.3 `safety-red-001`

### Title
**RED safety level blocks support contact**

### Domain
`SAFETY`

### What it checks
This scenario checks that a support-contact request is denied when:

- explicit consent exists
- but the session starts in `RED` safety state

### Expected result
- decision status: `DENIED`
- executable: `False`
- fault reason: `session_safety_red`

### Why it matters
This scenario shows that authorization alone is not enough.
Even with valid consent, the runtime should still deny behavior when the safety context is already unacceptable.

That is an important architectural claim in this repo:
**consent does not override safety.**

### What it does not prove
It does not prove:
- dynamic RED transitions during live motion
- hardware-originated RED conditions
- retreat timing under hazard change
- backend abort latency

---

## 5. Current Coverage Map

The current built-in scenarios provide strongest coverage in:

### Consent domain
Covered:
- approved explicit-consent path
- denied missing-consent path

Partially covered:
- contact authorization logic
- executable vs non-executable distinction
- structured fault reason recording

Not yet covered:
- consent freshness expiry
- consent revocation during approach
- consent revocation during contact
- caregiver override logic
- institutional-policy overrides

---

### Safety domain
Covered:
- pre-existing RED session denial path

Partially covered:
- safety gate interaction with runtime service
- structured denial outcome for RED state

Not yet covered:
- dynamic hazard intrusion
- software veto vs hardware veto distinctions
- stale-signal safety failure
- overforce-triggered retreat
- safe-hold fallback after retreat failure

---

### Execution domain
Indirectly covered:
- execution adapter acceptance on approved path
- absence of execution on denied path

Not yet covered as built-in catalog cases:
- explicit execution rejection case
- backend fault case
- abort path
- safe-hold path
- retreat path

---

### Logging and replay domain
Indirectly covered:
- event emission count as part of benchmark observation

Not yet covered as catalog cases:
- event completeness expectations
- event ordering expectations
- replay integrity checks
- benchmark artifact round-trip checks

---

## 6. Scenario Structure Conventions

Current scenarios are built around a few explicit sections in `inputs`:

- `session`
- `request`
- `consent`
- `nudge`
- `start_pose`

Each scenario also defines an explicit `expectation`.

This is important because it avoids hidden runner magic.
A reviewer can inspect the scenario definition and understand:

- starting state
- requested action
- consent condition
- target contact geometry
- expected outcome

That keeps the catalog auditable.

---

## 7. Current Catalog Strengths

The current scenario catalog is small, but it has real strengths:

- deterministic
- explicit expectations
- uses fresh runtime service instances
- structured observations
- tightly bound to repository behavior
- easy to extend

This is a much stronger starting point than having only ad hoc demos or prose claims.

---

## 8. Current Catalog Limits

The catalog is still early-stage.

Important current limits:

- very few scenarios
- no HIL-backed scenarios
- no real hardware adapter scenarios
- no replay-only catalog cases yet
- no event-log integrity scenarios yet
- no sensor-freshness denial scenarios yet
- no retreat/safe-hold scenario coverage in the built-in catalog yet

That is acceptable for now, but it should remain visible.

---

## 9. Recommended Next Scenarios

The next highest-value catalog additions should be:

### Consent
- consent freshness expired before contact
- consent revoked during active approach
- consent revoked during active contact

### Safety
- dynamic RED intrusion after planning
- stale critical signal blocks execution
- overforce causes retreat

### Execution
- simulated backend rejects plan
- simulated backend faults mid-run
- safe-hold command path
- abort command path

### Logging and replay
- event count regression scenario
- replay round-trip equivalence scenario
- event ordering integrity scenario

### Integration
- full request-to-execution-to-abort scenario
- denial-to-fault-log consistency scenario

---

## 10. Catalog Review Questions

When adding a new scenario, reviewers should ask:

1. What exact repo behavior is being checked?
2. Is the expectation explicit?
3. Is the scenario deterministic?
4. Does it measure something useful or just duplicate another case?
5. Does it help close a current coverage gap?
6. Is the scenario claiming more than the runtime actually supports?

If those questions are weak, the scenario is probably weak.

---

## 11. Final Rule

A benchmark catalog should make repository coverage easier to understand, not harder.

If the catalog cannot quickly tell a reviewer what is tested, what is not tested, and what still needs evidence, it is not doing its job.
