# Safety Case Starter Pack

This document defines the initial safety-case structure for IX-HapticSight.

The repository is not claiming certification, production approval, or formal acceptance by any regulatory or institutional body.
This document is not a certification artifact.

Its purpose is narrower and more practical:
to give the repository a disciplined structure for arguing what the system is intended to do, what it is not intended to do, what assumptions it depends on, what evidence exists, and where the evidence gaps still are.

That is the beginning of a real safety case.

---

## 1. Purpose

A safety-case structure exists to answer these questions:

- what is the system and what is its intended scope
- what hazards and unsafe outcomes are being taken seriously
- what claims are being made
- what evidence supports each claim
- what assumptions or constraints limit those claims
- what is still missing before stronger claims would be appropriate

The goal is not to produce paperwork theater.
The goal is to make safety reasoning traceable and falsifiable.

---

## 2. Safety-Case Philosophy

IX-HapticSight should follow these principles:

- narrow claims beat broad claims
- explicit non-claims matter
- assumptions must be visible
- evidence quality matters more than document volume
- code, tests, replay, and measured artifacts should support the argument
- unresolved evidence gaps should remain visible, not buried

This repository should prefer:
- “bounded architecture with defined evidence gaps”
over
- “sounds safe because the prose is confident”

---

## 3. Current Safety-Case Posture

At the current repository stage, the correct posture is:

- concept and reference-implementation maturity
- strong architectural intent
- partial code support for protocol logic
- growing documentation support for invariants, fault handling, retreat semantics, privacy, and threat modeling
- limited evidence beyond baseline unit tests
- no HIL evidence yet
- no runtime execution evidence yet
- no certification claim

That means the safety case is currently:
**starter-pack level**, not final-case level.

---

## 4. Top-Level Safety Argument Structure

A useful top-level structure for this repository is:

### Claim A
The repository defines a bounded interaction architecture rather than an unconstrained human-contact behavior system.

### Claim B
The repository gives safety and authorization logic priority over convenience execution.

### Claim C
The repository preserves explicit failure, retreat, and safe-hold semantics rather than vague stop behavior.

### Claim D
The repository is designed to support traceability, replay, benchmarking, and later evidence collection.

### Claim E
The repository explicitly limits its claims and does not present itself as certified or deployment-ready without further evidence.

These claims are appropriate for the current maturity level.
Stronger claims would require stronger evidence.

---

## 5. Safety Scope Definition

The safety case must start by being clear about scope.

### In scope
- bounded human-facing interaction logic
- consent-aware gating
- hazard-aware veto behavior
- force-limited contact planning semantics
- retreat and safe-hold semantics
- state-machine clarity
- replay and evidence discipline direction
- future runtime architecture boundaries

### Not in scope
- proving a real deployed robot is safe in all contexts
- proving medical or therapeutic safety
- proving human comfort across populations
- replacing hardware safety engineering
- replacing deployment-specific risk assessment
- formal certification without substantial future evidence

A safety case becomes weak the moment scope silently expands.

---

## 6. Hazard Categories the Safety Case Should Address

The argument structure should eventually cover hazards such as:

### HZ-001 — Unauthorized contact
Examples:
- contact without valid consent
- contact after consent revocation
- contact initiated outside allowed policy scope

### HZ-002 — Unsafe proximity or approach
Examples:
- approach through unsafe corridor
- approach under poor safety-map conditions
- inappropriate pre-contact continuation

### HZ-003 — Excessive or misapplied force
Examples:
- overforce
- sustained contact beyond bounds
- contact outside intended zone

### HZ-004 — Failure to disengage safely
Examples:
- abort without adequate withdrawal when needed
- retreat not available
- unsafe hold in ambiguous posture

### HZ-005 — Fault concealment or weak observability
Examples:
- fault occurs but is not logged
- state transition reason lost
- replay cannot explain a harmful event

### HZ-006 — Integrity or security compromise affecting physical behavior
Examples:
- tampered force-limit config
- spoofed signal path
- unauthorized execution command
- falsified logs

### HZ-007 — Privacy or evidence misuse with human-facing data
Examples:
- unnecessary retention of raw media
- replay artifacts overexpose person-linked data
- sensitive logs shared without minimization

These categories are still architectural, but they are the right ones to anchor now.

---

## 7. Top-Level Claims and Evidence Mapping

## Claim A
**The repository defines bounded interaction behavior.**

### Supporting rationale
The repo uses:
- explicit schemas
- state-machine semantics
- force-limit profiles
- safety gating
- contact planning boundaries
- retreat and safe-hold direction

### Current supporting artifacts
- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/schemas.py`
- `src/ohip/contact_planner.py`
- `src/ohip/safety_gate.py`
- `configs/force_limits.yaml`
- `docs/safety/invariants.md`
- `docs/safety/retreat_semantics.md`

### Evidence status
**Partial support**

### Major evidence gaps
- no dedicated transition conformance tests
- no runtime execution evidence
- no HIL support yet

---

## Claim B
**Safety and authorization logic are intended to override convenience behavior.**

### Supporting rationale
The repo architecture explicitly prioritizes:
- consent semantics
- hazard veto semantics
- blocking, abort, and latched fault handling

### Current supporting artifacts
- `src/ohip/consent_manager.py`
- `src/ohip/safety_gate.py`
- `docs/safety/invariants.md`
- `docs/safety/fault_handling.md`
- `docs/architecture/runtime_overview.md`

### Evidence status
**Partial support**

### Major evidence gaps
- no dedicated veto-priority tests yet
- no structured fault log implementation yet
- no independent watchdog or runtime veto path yet

---

## Claim C
**The repository distinguishes abort, retreat, and safe-hold outcomes.**

### Supporting rationale
The upgrade docs explicitly separate:
- interruption
- withdrawal
- controlled non-movement

### Current supporting artifacts
- `docs/state_machine.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/architecture/execution_adapter.md`

### Evidence status
**Architecturally supported, implementation still limited**

### Major evidence gaps
- no retreat schema
- no retreat execution adapter code
- no retreat benchmark scenarios yet

---

## Claim D
**The repository is being shaped to support traceability and evidence collection.**

### Supporting rationale
The repo now includes explicit traceability, threat model, privacy posture, standards crosswalk, and safety-case starter structure.

### Current supporting artifacts
- `docs/safety/requirements_traceability.md`
- `docs/governance/threat_model.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/standards_crosswalk.md`
- `ROADMAP.md`
- `CHANGELOG.md`

### Evidence status
**Strong architectural intent, limited runtime evidence**

### Major evidence gaps
- no structured event logger
- no replay tooling
- no benchmark suite
- no HIL evidence packages

---

## Claim E
**The repository is explicit about non-claims and maturity limits.**

### Supporting rationale
The upgrade path is intentionally conservative and repeatedly distinguishes concept maturity from validated deployment.

### Current supporting artifacts
- `ROADMAP.md`
- `docs/governance/standards_crosswalk.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/threat_model.md`

### Evidence status
**Good documentation support**

### Major evidence gaps
- README still needs final harmonization at the end of the campaign
- release checklist still needs stronger non-claim enforcement later

---

## 8. Assumptions

A safety case is weak if assumptions stay hidden.
The current repository depends on assumptions such as:

### A-001
Core policy and safety logic will remain inspectable rather than being replaced by opaque convenience behavior.

### A-002
Future runtime integrations will preserve the authority of consent and safety logic.

### A-003
Force-limit configuration will be treated as safety-relevant and not casually modified.

### A-004
Replay and logging layers, once added, will preserve event provenance.

### A-005
Future sensor integrations will expose freshness and health metadata explicitly.

### A-006
Human-facing deployment contexts will require additional hardware, operational, and institutional controls beyond the repo alone.

These assumptions should eventually map to tests, config controls, and documented deployment limits.

---

## 9. Constraints

The safety case should also preserve explicit constraints.

### C-001
The repo is not a substitute for hardware safety engineering.

### C-002
The repo is not proof of certification readiness.

### C-003
The repo is not proof of population-wide social appropriateness or comfort.

### C-004
The repo is not sufficient by itself for clinical or therapeutic use.

### C-005
The repo is not sufficient by itself for unrestricted real-world human-contact deployment.

Constraints are not weakness.
They are honesty.

---

## 10. Evidence Types the Safety Case Should Eventually Use

The repository should eventually support multiple evidence classes.

### 10.1 Documentation evidence
Examples:
- protocol spec
- state machine
- invariants
- threat model
- privacy posture
- standards crosswalk

### 10.2 Code evidence
Examples:
- schema definitions
- consent logic
- safety gate
- contact planner
- runtime coordinator
- execution adapter

### 10.3 Test evidence
Examples:
- schema tests
- state-transition tests
- veto-priority tests
- force-limit tests
- fault-handling tests
- retreat tests

### 10.4 Replay and benchmark evidence
Examples:
- structured event logs
- scenario result bundles
- reproducible benchmark outputs
- regression comparisons

### 10.5 HIL evidence
Examples:
- load-cell calibration records
- overforce trials
- retreat timing measurements
- backend fault injection results

### 10.6 Controlled study evidence
Examples:
- carefully scoped human-interaction studies
- comfort and predictability measures
- operator comprehension checks

At present, the repo mostly has documentation and a small amount of code/test evidence.
That is fine, as long as it is stated clearly.

---

## 11. Safety-Case Maturity Levels

A practical maturity ladder for this repo is:

### SC-0 — Concept only
Claims exist, evidence sparse.

### SC-1 — Structured architecture
Claims, non-claims, invariants, and traceability docs exist.

### SC-2 — Code-backed reference case
Core logic exists with tests and clearer requirement mapping.

### SC-3 — Replay/benchmark-backed case
Structured events, replay, and scenario metrics exist.

### SC-4 — HIL-supported case
Physical test artifacts and measured runtime evidence exist.

### SC-5 — Deployment-support case
Substantial integration evidence, operational controls, and domain review exist.

Right now the repo is transitioning from **SC-1** toward **SC-2**.

---

## 12. Current Repository Mapping

Current baseline and upgrade-era artifacts relevant to this safety-case starter include:

- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/schemas.py`
- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`
- `src/ohip/rest_pose.py`
- `src/ohip/safety_gate.py`
- `tests/test_schemas.py`
- `tests/test_nudge_scheduler.py`
- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/threat_model.md`
- `docs/governance/standards_crosswalk.md`

This is a stronger safety-case foundation than the baseline repo had, but it is not yet enough for strong external safety claims.

---

## 13. Near-Term Priorities

The highest-value next steps for the safety case are:

1. add dedicated consent tests
2. add dedicated veto and force-limit tests
3. add state-transition conformance tests
4. add explicit fault and retreat event structures
5. add structured event logger and replay tooling
6. add benchmark scenario and metrics definitions
7. add HIL evidence scaffolding

Those steps convert argument structure into stronger evidence.

---

## 14. Review Questions

When someone proposes a new safety-related feature or claim, reviewers should ask:

1. What exact claim is being made?
2. What hazard does it relate to?
3. What assumptions limit the claim?
4. What evidence supports it?
5. What evidence is still missing?
6. Is the wording stronger than the support behind it?

If those questions cannot be answered cleanly, the safety case is not strong enough yet.

---

## 15. Final Rule

The repository should never rely on confidence language as a substitute for evidence.

A good safety case is not a performance.
It is a visible chain from claim to artifact to evidence to limitation.
