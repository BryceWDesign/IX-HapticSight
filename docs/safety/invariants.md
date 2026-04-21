# Safety Invariants

This document defines the core safety invariants that the upgraded IX-HapticSight repository is expected to preserve.

An invariant in this context is a rule that should remain true across normal operation, degraded operation, replay, benchmarking, and future runtime integrations unless explicitly superseded by a documented design change.

These invariants are stricter than implementation convenience.
If code and an invariant disagree, the code should be treated as suspect until the discrepancy is resolved.

---

## 1. Purpose

The project exists to make human-facing robot interaction more bounded, more inspectable, and more vetoable.

That means the repository needs hard rules that survive:

- refactors
- new runtime layers
- sensor additions
- benchmark harnesses
- ROS 2 integration
- execution backend changes

The invariants below provide that anchor.

---

## 2. Scope

These invariants apply to the project as a whole, including:

- protocol-level logic in `src/ohip/`
- future runtime orchestration layers
- future sensing interfaces
- future execution adapter code
- replay and benchmark tooling when they simulate or inspect behavior

These invariants do not claim to replace hardware safety requirements, regulatory review, or deployment-specific risk controls.

---

## 3. Consent Invariants

### INV-CONSENT-001
No human-facing contact behavior may proceed without a valid consent state or a documented interaction mode that explicitly allows non-contact behavior only.

Implication:
- contact planning must not treat missing consent as acceptable
- stale consent must not silently pass
- ambiguous consent must not be upgraded to approval by default

---

### INV-CONSENT-002
Consent freshness must be evaluated before contact authorization when freshness is part of the active policy.

Implication:
- a once-valid consent record is not permanently valid unless a policy explicitly says so
- runtime convenience must not bypass freshness checks

---

### INV-CONSENT-003
Consent revocation must have higher priority than convenience execution.

Implication:
- if consent is revoked during a session, execution should stop or transition according to documented retreat/safe-hold rules
- the system must not continue contact because “the current plan was already underway”

---

## 4. Safety-Veto Invariants

### INV-SAFETY-001
A hard safety veto must be able to block, abort, or force retreat regardless of planner preference.

Implication:
- planning and execution may not overrule a hard veto
- veto logic must remain authoritative

---

### INV-SAFETY-002
A RED-zone or equivalent hard hazard state must not be reinterpreted as acceptable by downstream code.

Implication:
- execution adapter code must not soften hazard semantics
- planner code must not treat a hard block as a warning

---

### INV-SAFETY-003
Stale critical signals must not be treated as fresh if freshness is required for the active safety path.

Examples:
- stale force-torque reading
- stale proximity reading
- stale thermal reading
- stale fused contact-state update

Implication:
- timeout or freshness failure should trigger rejection, abort, retreat, or degraded mode according to documented rules

---

## 5. Contact-Force Invariants

### INV-FORCE-001
Contact force must remain bounded by the active force-limit profile or a stricter runtime-imposed bound.

Implication:
- the system must not self-escalate force ceilings for convenience
- planner and execution layers must preserve selected limits

---

### INV-FORCE-002
An overforce condition must be surfaced as an explicit state or event, not hidden inside informal logs.

Implication:
- replay, testing, and audit tooling must be able to identify overforce events deterministically

---

### INV-FORCE-003
The absence of high-resolution tactile sensing must not be described as evidence of safe contact quality.

Implication:
- missing sensing capability should narrow claims, not expand them

---

## 6. State-Machine Invariants

### INV-STATE-001
State transitions must follow documented transition rules or a documented revision of those rules.

Implication:
- code must not invent hidden transitions without documentation and tests
- replay output must be explainable against the state machine

---

### INV-STATE-002
Abort, retreat, and safe-hold transitions must remain explicit and distinguishable.

Implication:
- the system should not collapse all failure behavior into one vague “stopped” state
- analysis needs to know whether the robot aborted, retreated, or simply failed

---

### INV-STATE-003
A latched fault state must not silently clear itself unless the design explicitly defines an automatic clear condition.

Implication:
- severe faults should remain visible until cleared according to documented logic

---

## 7. Planning Invariants

### INV-PLAN-001
The planner may only generate plans within constraints already established by policy and safety evaluation.

Implication:
- the planner is not allowed to create new permission
- the planner is not allowed to soften active safety restrictions

---

### INV-PLAN-002
A plan must contain enough metadata to be reviewed, logged, and replayed.

Minimum expectations:
- plan identifier
- session or interaction context
- target classification
- active constraint profile
- plan type
- reason code where relevant

Implication:
- opaque “do thing” commands are not acceptable for a serious runtime path

---

### INV-PLAN-003
Retreat planning must remain bounded and explicitly classified.

Implication:
- retreat is not “just another motion”
- retreat intent, reason, and expected safety posture must stay visible

---

## 8. Execution Invariants

### INV-EXEC-001
The execution layer may refuse a plan it cannot safely honor, but it may not expand the plan’s authority.

Implication:
- execution may be more conservative than the planner
- execution may not be more permissive than the planner

---

### INV-EXEC-002
Abort requests must preempt routine execution flow.

Implication:
- execution code must not finish an unsafe step “for smoothness”
- abort acknowledgement should be prioritized

---

### INV-EXEC-003
Execution faults must be surfaced in structured form.

Implication:
- backend failures should not disappear into console noise
- logging and replay must preserve fault identity

---

## 9. Logging and Replay Invariants

### INV-LOG-001
Safety-relevant decisions and state transitions must be represented in structured event records.

Examples:
- consent denial
- stale consent rejection
- hazard veto
- overforce event
- retreat entry
- safe-hold entry
- execution rejection

---

### INV-LOG-002
Replay tooling must not invent events that were not part of the source record unless they are clearly marked as derived annotations.

Implication:
- replay is for inspection, not fiction

---

### INV-LOG-003
Event records should preserve enough causal context to explain why a transition occurred.

Examples:
- reason code
- threshold source
- policy bundle version
- signal freshness failure
- hazard classification

---

## 10. Interface Invariants

### INV-IFACE-001
Device-specific raw payloads should be normalized before core policy and safety logic consumes them.

Implication:
- protocol logic should not depend on one vendor-specific payload shape

---

### INV-IFACE-002
Signal health and freshness should be explicit fields, not hidden assumptions.

Implication:
- a clean payload without timestamp semantics is not enough for serious safety logic

---

## 11. Benchmark Invariants

### INV-BENCH-001
Benchmarks must be replayable or reproducible from defined inputs.

Implication:
- a benchmark result with no clear scenario definition is weak evidence

---

### INV-BENCH-002
A passing benchmark must not be presented as proof of real-world deployment safety.

Implication:
- benchmark success supports engineering confidence, not blanket certification claims

---

### INV-BENCH-003
Benchmark metrics must remain tied to documented definitions.

Implication:
- “improved safety” is not enough
- metrics must specify what improved and how it was measured

---

## 12. Governance Invariants

### INV-GOV-001
The repository must preserve clear non-claims about what has not been validated.

Implication:
- documentation should not drift into unsupported production claims

---

### INV-GOV-002
Privacy-sensitive or behavior-sensitive data handling rules must be explicit when such data is logged or replayed.

Implication:
- data retention and observability cannot remain undefined once runtime logging grows

---

### INV-GOV-003
Security-related assumptions that materially affect physical behavior must be documented.

Implication:
- trust boundaries cannot stay implicit once runtime execution and interfaces are added

---

## 13. Review Checklist

When reviewing a change, ask:

1. Does this weaken or bypass an invariant?
2. Does this introduce a new implicit authority path?
3. Does this hide a safety-relevant event?
4. Does this reduce replay or audit quality?
5. Does this make force, consent, or hazard behavior less explicit?
6. Does documentation still match behavior?

If the answer to any of these is yes, the change requires closer scrutiny.

---

## 14. Relationship to Tests

Future tests should map to these invariants where practical.

Examples:
- stale-consent tests should point to consent invariants
- hard-veto tests should point to safety-veto invariants
- retreat tests should point to state and execution invariants
- logging tests should point to logging invariants

This document is intended to support that traceability.

---

## 15. Final Rule

The project should prefer a conservative failure over an ambiguous permissive action.

If the system cannot justify an action within consent, safety, force, and state rules, it should not proceed.
