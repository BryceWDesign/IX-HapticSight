# Requirements Traceability Matrix

This document defines the initial traceability matrix for IX-HapticSight as the repository evolves from a protocol-oriented reference implementation into a stronger runtime and evidence-oriented architecture.

The purpose of this matrix is simple:

- identify what the project claims
- identify what each claim depends on
- identify where that claim is implemented, documented, or tested
- identify what evidence is still missing

This document is intentionally conservative.
A requirement is not considered satisfied merely because a concept appears in prose.
A requirement should map to at least one of the following:

- normative documentation
- source code
- test coverage
- benchmark scenario
- replay artifact
- future hardware-in-the-loop evidence path

---

## 1. Traceability Philosophy

IX-HapticSight should prefer explicit traceability over vague assurance.

A reviewer should be able to ask:

- what is the requirement
- where is it defined
- where is it implemented
- where is it tested
- where is it logged
- what evidence remains missing

If that chain does not exist, the requirement is still immature.

---

## 2. Status Labels

This matrix uses the following status labels.

### `IMPLEMENTED`
There is code or documentation in the current repository that materially satisfies the requirement at the reference-implementation level.

### `PARTIAL`
Some evidence exists, but the requirement is not yet fully represented in code, tests, logging, or runtime behavior.

### `PLANNED`
The requirement is part of the intended architecture, but the current repository does not yet implement it in a meaningful way.

### `EVIDENCE-GAP`
The requirement is conceptually present, but meaningful evidence for it is not yet available.

---

## 3. Current Baseline Artifacts

Current repository artifacts relevant to traceability include:

- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/schemas.py`
- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`
- `src/ohip/nudge_scheduler.py`
- `src/ohip/rest_pose.py`
- `src/ohip/safety_gate.py`
- `tests/test_schemas.py`
- `tests/test_nudge_scheduler.py`
- `configs/force_limits.yaml`
- `configs/culture_profiles.yaml`
- `examples/quickstart.py`

This matrix also references upgrade-era documents such as:

- `docs/safety/invariants.md`
- future benchmark, replay, runtime, and HIL artifacts that will be added later in the 72-commit campaign

---

## 4. Requirement Matrix

## RQ-001 — Canonical protocol data structures shall be defined in a stable, implementation-agnostic form.

**Intent:**  
The project must have clear message/data structures for consent, safety semantics, contact planning, and execution logging so that implementations do not drift silently.

**Primary references:**  
- `docs/spec.md`
- `src/ohip/schemas.py`

**Current implementation anchors:**  
- `src/ohip/schemas.py`

**Current test anchors:**  
- `tests/test_schemas.py`

**Logging/replay relevance:**  
- execution/event structures exist conceptually in schemas, but dedicated replay/logging tooling is not yet present

**Status:**  
`IMPLEMENTED` at reference-implementation level

**Evidence gap:**  
- no dedicated event-log package yet
- no schema compatibility tests across runtime backends yet

---

## RQ-002 — Human-facing contact shall require valid consent semantics or an explicitly documented non-contact-only mode.

**Intent:**  
The system must not treat human contact as default-permitted behavior.

**Primary references:**  
- `docs/spec.md`
- `docs/state_machine.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`

**Current test anchors:**  
- indirect coverage may exist in behavior paths, but there is not yet a dedicated consent test suite in the current baseline

**Logging/replay relevance:**  
- consent decisions are not yet captured through structured event logging

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no dedicated unit tests for consent freshness and revocation
- no replay artifact showing denial, revocation, or stale-consent behavior
- no benchmark suite for consent edge cases yet

---

## RQ-003 — Safety-map semantics shall distinguish GREEN, YELLOW, and RED conditions.

**Intent:**  
The repository must preserve clear tri-level safety semantics for permitted, verify-first, and prohibited conditions.

**Primary references:**  
- `docs/spec.md`
- `src/ohip/schemas.py`

**Current implementation anchors:**  
- `src/ohip/schemas.py`
- `src/ohip/safety_gate.py`

**Current test anchors:**  
- partial schema coverage in `tests/test_schemas.py`

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no dedicated tests for hazard-to-veto behavior
- no scenario suite validating RED intersection behavior
- no runtime replay evidence yet

---

## RQ-004 — A hard hazard or veto condition shall prevent or interrupt unsafe action.

**Intent:**  
The system must preserve veto authority above convenience execution.

**Primary references:**  
- `docs/spec.md`
- `docs/state_machine.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- `src/ohip/safety_gate.py`
- conceptual interaction flow in `examples/quickstart.py`

**Current test anchors:**  
- no dedicated veto-path test file currently present in the baseline archive

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no dedicated unit tests for hard-veto priority
- no fault-injection or replay evidence
- no independent runtime watchdog path yet

---

## RQ-005 — The state machine shall define bounded interaction states and explicit recovery paths.

**Intent:**  
The project must not rely on vague or hidden control flow for approach, contact, retreat, and safe-hold behavior.

**Primary references:**  
- `docs/state_machine.md`
- `docs/spec.md`

**Current implementation anchors:**  
- distributed logically across:
  - `src/ohip/contact_planner.py`
  - `src/ohip/rest_pose.py`
  - `src/ohip/safety_gate.py`
  - `src/ohip/nudge_scheduler.py`

**Current test anchors:**  
- no dedicated state-machine conformance tests in the present baseline

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no transition-table tests
- no invariant tests against the FSM
- no replay of actual transition sequences

---

## RQ-006 — Force-limited contact behavior shall remain bounded by configured limits.

**Intent:**  
If contact is planned or executed, it must remain inside explicitly selected constraints.

**Primary references:**  
- `docs/spec.md`
- `configs/force_limits.yaml`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- `configs/force_limits.yaml`
- `src/ohip/contact_planner.py`
- `src/ohip/safety_gate.py`

**Current test anchors:**  
- no dedicated force-limit validation tests in the current baseline

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no force-profile selection tests
- no overforce event tests
- no measured evidence
- no structured overforce logging yet

---

## RQ-007 — Rest posture behavior shall be explicit and non-threatening when idle or after recovery.

**Intent:**  
The system should maintain a clear and bounded idle/rest behavior rather than ambiguous hand motion.

**Primary references:**  
- `docs/spec.md`
- `src/ohip/rest_pose.py`

**Current implementation anchors:**  
- `src/ohip/rest_pose.py`

**Current test anchors:**  
- none currently visible in baseline tests

**Status:**  
`PARTIAL`

**Evidence gap:**  
- no posture validation tests
- no scenario coverage for recovery-to-rest behavior
- no runtime evidence or replay

---

## RQ-008 — Engagement scheduling shall prioritize safer interaction opportunities and avoid unsafe targets.

**Intent:**  
Scheduling logic should respect safety semantics and support deterministic prioritization.

**Primary references:**  
- `docs/spec.md`
- `src/ohip/nudge_scheduler.py`

**Current implementation anchors:**  
- `src/ohip/nudge_scheduler.py`

**Current test anchors:**  
- `tests/test_nudge_scheduler.py`

**Status:**  
`IMPLEMENTED` at reference-implementation level

**Evidence gap:**  
- no replayable benchmark pack for scheduler edge cases
- no runtime coordination tests involving multiple simultaneous requests

---

## RQ-009 — The repository shall support transparent auditing of important decisions and outcomes.

**Intent:**  
A serious safety-first interaction stack must support review after the fact.

**Primary references:**  
- `docs/spec.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- conceptual only through schemas and documentation

**Current test anchors:**  
- none

**Status:**  
`PLANNED`

**Evidence gap:**  
- no structured event logger package
- no replay tool
- no evidence bundle format
- no benchmark result schema package yet

---

## RQ-010 — The repository shall preserve explicit non-claims and avoid overstating deployment readiness.

**Intent:**  
Documentation must not imply certification, medical validation, or production safety that the repo does not actually support.

**Primary references:**  
- `ROADMAP.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- currently mixed; some legacy docs still contain language that needs tightening

**Current test anchors:**  
- not applicable as a code test in the current baseline

**Status:**  
`PARTIAL`

**Evidence gap:**  
- README and some legacy documentation still need harmonization
- no release checklist enforcing non-claim language yet

---

## RQ-011 — The project shall maintain backend-agnostic core logic.

**Intent:**  
Core policy, consent, and safety behavior should remain portable rather than tightly bound to one transport or middleware.

**Primary references:**  
- `docs/spec.md`
- `docs/architecture/package_map.md`
- `docs/architecture/runtime_overview.md`

**Current implementation anchors:**  
- current `src/ohip/` package is Python-only and middleware-agnostic

**Current test anchors:**  
- indirect through existing unit tests

**Status:**  
`IMPLEMENTED` at current scale

**Evidence gap:**  
- future ROS 2 integration must preserve this boundary
- no compatibility checks across multiple runtimes yet

---

## RQ-012 — Runtime execution shall eventually distinguish approval logic from backend command transport.

**Intent:**  
Consent, safety, planning, and backend execution must not collapse into one hidden path.

**Primary references:**  
- `docs/architecture/runtime_overview.md`
- `docs/architecture/execution_adapter.md`
- `docs/architecture/node_graph.md`

**Current implementation anchors:**  
- not yet implemented as a dedicated code boundary

**Current test anchors:**  
- none

**Status:**  
`PLANNED`

**Evidence gap:**  
- no execution adapter package yet
- no runtime coordinator yet
- no execution fault tests yet

---

## RQ-013 — Sensor freshness and signal health shall be explicit once runtime sensing interfaces are added.

**Intent:**  
The system must not pretend stale sensor data is trustworthy in a safety path.

**Primary references:**  
- `docs/safety/invariants.md`
- `docs/architecture/runtime_overview.md`

**Current implementation anchors:**  
- not yet represented as dedicated interface modules in the baseline archive

**Current test anchors:**  
- none

**Status:**  
`PLANNED`

**Evidence gap:**  
- no force-torque, tactile, proximity, or thermal interface packages yet
- no stale-signal tests yet

---

## RQ-014 — Structured logging and replay shall support after-action review and benchmark comparison.

**Intent:**  
Important behavior should be inspectable without guesswork.

**Primary references:**  
- `docs/architecture/runtime_overview.md`
- `docs/architecture/node_graph.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- not yet implemented as code

**Current test anchors:**  
- none

**Status:**  
`PLANNED`

**Evidence gap:**  
- no event schema package beyond conceptual schema structures
- no replay loader/publisher
- no result comparison tooling

---

## RQ-015 — Benchmark scenarios shall become reproducible and tied to documented metrics.

**Intent:**  
The project should be able to compare behavior across changes using consistent scenarios.

**Primary references:**  
- `ROADMAP.md`
- `docs/safety/invariants.md`
- future benchmark docs

**Current implementation anchors:**  
- not yet implemented as a benchmark package

**Current test anchors:**  
- none

**Status:**  
`PLANNED`

**Evidence gap:**  
- no scenario catalog yet
- no metrics collector
- no benchmark runner
- no benchmark report schema

---

## RQ-016 — Future hardware-in-the-loop evidence should be traceable to repository requirements.

**Intent:**  
If the project eventually gathers physical evidence, that evidence should map cleanly back to documented requirements.

**Primary references:**  
- `ROADMAP.md`
- `docs/safety/invariants.md`

**Current implementation anchors:**  
- none yet; only planned architecture direction

**Current test anchors:**  
- none

**Status:**  
`EVIDENCE-GAP`

**Evidence gap:**  
- no HIL fixture architecture yet
- no calibration templates
- no fault-injection templates
- no evidence bundle structure yet

---

## 5. Requirement-to-Artifact Summary Table

| Requirement | Primary Focus | Current Code Anchor | Current Test Anchor | Status |
|---|---|---|---|---|
| RQ-001 | canonical schemas | `src/ohip/schemas.py` | `tests/test_schemas.py` | IMPLEMENTED |
| RQ-002 | consent for contact | `src/ohip/consent_manager.py` | none dedicated yet | PARTIAL |
| RQ-003 | GREEN/YELLOW/RED semantics | `src/ohip/schemas.py`, `src/ohip/safety_gate.py` | partial schema tests | PARTIAL |
| RQ-004 | veto priority | `src/ohip/safety_gate.py` | none dedicated yet | PARTIAL |
| RQ-005 | bounded state machine | distributed in `src/ohip/` | none dedicated yet | PARTIAL |
| RQ-006 | force-limited contact | planner + safety + configs | none dedicated yet | PARTIAL |
| RQ-007 | rest posture behavior | `src/ohip/rest_pose.py` | none dedicated yet | PARTIAL |
| RQ-008 | deterministic scheduling | `src/ohip/nudge_scheduler.py` | `tests/test_nudge_scheduler.py` | IMPLEMENTED |
| RQ-009 | transparent auditing | not yet dedicated | none | PLANNED |
| RQ-010 | explicit non-claims | docs/roadmap layer | none | PARTIAL |
| RQ-011 | backend-agnostic core | `src/ohip/` | indirect existing tests | IMPLEMENTED |
| RQ-012 | execution boundary | planned docs only | none | PLANNED |
| RQ-013 | signal freshness | planned docs only | none | PLANNED |
| RQ-014 | replayability | planned docs only | none | PLANNED |
| RQ-015 | benchmark reproducibility | planned docs only | none | PLANNED |
| RQ-016 | HIL traceability | not yet present | none | EVIDENCE-GAP |

---

## 6. Near-Term Traceability Priorities

The next highest-value traceability improvements are:

1. add dedicated consent tests
2. add dedicated safety-veto tests
3. add force-limit and overforce tests
4. add state-transition conformance tests
5. add structured event definitions for logging and replay
6. add benchmark scenario and result schemas
7. add HIL evidence folder structure and templates

These will convert several `PARTIAL` and `PLANNED` requirements into something much stronger.

---

## 7. Review Rule

A new feature should not be considered mature unless it can answer four questions:

1. what requirement does it satisfy
2. where is that requirement documented
3. where is it implemented
4. where is it tested or otherwise evidenced

If one of those links is missing, the feature is still incomplete.

---

## 8. Final Note

This matrix will need regular updates as the 72-commit campaign progresses.

It is intended to become stricter over time, not looser.
As runtime, sensing, replay, benchmark, and HIL artifacts are added, they should be inserted into this matrix rather than left as disconnected files.
