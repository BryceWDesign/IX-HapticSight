# IX-HapticSight Roadmap

This roadmap defines the planned upgrade path from the current reference implementation toward a stronger, more auditable, and more runtime-oriented safety stack for bounded optical-haptic interaction.

It is intentionally conservative.

The project is not represented as certified, clinically validated, production deployed, or regulator-approved. The roadmap describes engineering intent and repository milestones, not real-world deployment approval.

---

## Repository Mission

IX-HapticSight is being developed as a safety-first optical-haptic interaction architecture for bounded human-facing robot behavior.

The core project mission is to make these behaviors explicit, testable, and reviewable:

- approach
- pre-contact verification
- bounded contact
- retreat
- safe hold
- consent-aware interaction gating
- hazard-aware veto behavior
- auditable runtime policy evaluation

The long-term direction is not broad social robotics.

The long-term direction is a measurable interaction-governance stack with deterministic safety constraints.

---

## Current Baseline

The current repository already contains:

- protocol schemas
- consent logic
- nudge scheduling logic
- rest-pose generation
- contact planning logic
- safety gating logic
- configuration files
- example usage
- baseline unit tests

That is enough for a reference implementation, but not enough for a runtime-grade or evidence-backed package.

---

## Upgrade Goals

The upgrade campaign is designed to produce a stronger repository in the following areas:

1. **Repository credibility**
   - cleaner project structure
   - clearer scope and non-claims
   - stronger contribution and review rules
   - more disciplined release notes and artifacts

2. **Runtime architecture**
   - package separation by responsibility
   - runtime coordinator structure
   - ROS 2-compatible package layout
   - explicit interfaces and message models

3. **Safety behavior**
   - stronger veto architecture
   - explicit fault handling
   - retreat semantics
   - stale-consent rejection
   - independent policy enforcement paths

4. **Physical sensing interfaces**
   - force-torque input abstraction
   - tactile sensor input abstraction
   - proximity input abstraction
   - thermal input abstraction
   - contact-state fusion hooks

5. **Evidence and replay**
   - structured logs
   - replay tooling
   - deterministic benchmark scenarios
   - simulation scene packs
   - hardware-in-the-loop scaffolding

6. **Governance**
   - threat model artifacts
   - privacy and data handling docs
   - safety invariant traceability
   - standards crosswalk
   - safety-case starter materials

---

## Planned Maturity Levels

### M0 — Reference Prototype
Status: approximately current state

Characteristics:
- pure Python reference modules
- documentation-first posture
- baseline configs and tests
- no real runtime messaging layer
- no tactile or hardware abstraction layer
- no benchmark suite
- no HIL scaffolding

### M1 — Structured Repository
Planned outcome:
- stronger packaging
- contribution and release hygiene
- clarified roadmap, non-claims, and project boundaries
- expanded project documentation

Exit criteria:
- repository structure is stable
- upgrade plan is documented
- contribution rules and release notes exist
- package metadata is present

### M2 — Modular Runtime Foundation
Planned outcome:
- logical package separation
- runtime coordination interfaces
- ROS 2 workspace and node scaffolding
- message and service definitions
- launch and configuration layering

Exit criteria:
- runtime module boundaries are explicit
- state ownership is clearer
- node lifecycle assumptions are documented
- configuration loading is centralized

### M3 — Safety-Grade Execution Layer
Planned outcome:
- motion execution adapter interfaces
- collision and zone gating
- retreat/abort logic
- watchdog behavior
- dual-path veto design
- stronger fault handling tests

Exit criteria:
- execution boundaries are explicit
- abort and retreat semantics are testable
- safety behavior is separated from convenience behavior

### M4 — Physical Signal Integration
Planned outcome:
- force-torque interfaces
- tactile interfaces
- proximity interfaces
- thermal interfaces
- contact-state fusion logic
- simulated sensor fixtures

Exit criteria:
- the codebase can represent measured contact-related inputs
- the planner and safety logic can consume those inputs without hidden assumptions

### M5 — Evidence, Replay, and Benchmarking
Planned outcome:
- structured event logs
- replay tooling
- benchmark schemas
- canonical scenarios
- metrics reports
- deterministic result packages

Exit criteria:
- behavior changes can be replayed
- benchmark outputs are comparable
- metrics are documented and reproducible

### M6 — HIL and Safety Case Readiness
Planned outcome:
- hardware-in-the-loop scaffolding
- calibration templates
- fault injection templates
- standards crosswalk
- privacy and governance docs
- safety invariant traceability matrix
- safety-case starter pack

Exit criteria:
- the repository supports disciplined evidence collection
- traceability exists between requirements, tests, and claims
- governance artifacts exist for future review

---

## What This Project Is Not

The repository should not drift into claims it cannot support.

It is not:

- a certified collaborative robot package
- a medical device
- a therapy robot
- a proven emotion-recognition engine
- a production deployment stack
- a substitute for hardware safety engineering
- a substitute for legal, regulatory, or IRB review
- a claim of socially correct behavior in all settings

---

## Evidence Philosophy

The strongest form of this project will rely on:

- explicit requirements
- deterministic safety behavior
- replayable logs
- bounded contact semantics
- benchmark scenarios
- hardware-in-the-loop evidence
- traceable documentation

Preference is always given to measured evidence over narrative claims.

---

## Release Philosophy

The planned release direction is:

- v0.1.x: reference implementation baseline
- v0.2.x: repository restructuring and modularization
- v0.3.x: runtime and ROS 2 scaffolding
- v0.4.x: sensing interfaces and execution safety expansion
- v0.5.x: replay and benchmark package
- v0.6.x: HIL scaffolding and safety-case preparation
- v1.0.0: strong repository milestone, still bounded by explicit non-claims unless real evidence justifies more

---

## Final Roadmap Rule

Every major upgrade should improve at least one of these:

- safety
- clarity
- testability
- traceability
- replayability
- boundedness

If it does not improve one of those, it should be treated as optional, not core.
