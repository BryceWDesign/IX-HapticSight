# Standards Crosswalk

This document defines the initial standards-and-guidance crosswalk for IX-HapticSight.

The repository is not claiming certification, formal compliance, or deployment approval.
It is also not claiming that documents alone make a system safe.

What this document does is narrower and more useful:
it maps major project concerns to external standards domains and guidance themes so reviewers can see where the repository is aligned, where it is incomplete, and where evidence would still be required.

---

## 1. Purpose

The standards crosswalk exists to answer these questions:

- which standards domains are relevant to the project
- which repository artifacts relate to those domains
- what is already represented in the repo
- what is still missing for stronger engineering credibility
- what evidence would be needed before making stronger claims

This document is intentionally conservative.

---

## 2. Crosswalk Philosophy

IX-HapticSight should not wave standards names around loosely.

A useful crosswalk should distinguish between:

- **relevance**
- **conceptual alignment**
- **implemented trace**
- **evidence-backed support**
- **actual compliance or certification**

Those are not the same thing.

For this repository, the correct current posture is:
- relevant to multiple robotics, safety, AI governance, privacy, and security domains
- partially aligned in architecture intent
- incomplete in runtime evidence
- not certified
- not deployment-approved

---

## 3. Primary Standards and Guidance Domains

The following domains are especially relevant.

### 3.1 Industrial robot safety and integration
Relevant because the project concerns human-facing robot behavior, bounded motion, fault handling, and interaction safety.

Examples of relevant standards domains:
- industrial robot safety requirements
- robot system integration safety requirements
- collaborative operation guidance

Repository relevance:
- state machine
- contact-force semantics
- hazard zones
- retreat and safe-hold logic
- bounded execution architecture

---

### 3.2 Human-robot interaction evaluation and trust
Relevant because the project involves perceived safety, appropriateness, transparency, and repeatability of interaction behavior.

Repository relevance:
- explicit interaction states
- structured event logging direction
- replay and benchmark planning
- bounded interaction semantics
- consent-aware behavior control

---

### 3.3 Functional safety and fault management
Relevant because the project distinguishes blocking faults, abort faults, latched critical faults, and recovery paths.

Repository relevance:
- fault model
- invariants
- retreat semantics
- watchdog direction
- structured fault/event artifacts

---

### 3.4 AI risk and governance
Relevant because the project touches perception, contact decisions, runtime policy, and possibly future model-assisted interpretation.

Repository relevance:
- explicit non-claims
- deterministic governance preference
- privacy posture
- threat model
- replay and evidence discipline

---

### 3.5 Privacy and data handling
Relevant because the repository may eventually involve logs, consent records, sensor data, replay artifacts, and subject-linked session data.

Repository relevance:
- consent management
- privacy and data-handling posture
- replay and logging direction
- data minimization expectations

---

### 3.6 Cybersecurity for connected robotic systems
Relevant because runtime integrity, sensor trust, config integrity, and command authority can directly affect physical behavior.

Repository relevance:
- threat model
- policy bundle integrity direction
- execution adapter boundary
- live-versus-replay separation
- structured provenance expectations

---

## 4. Crosswalk Table

| Domain | Why It Matters Here | Current Repo Alignment | Key Repo Artifacts | Current Maturity |
|---|---|---|---|---|
| Robot safety / integration | Human-facing bounded motion and contact | partial conceptual alignment | `docs/spec.md`, `docs/state_machine.md`, `src/ohip/safety_gate.py`, `configs/force_limits.yaml` | partial |
| Collaborative interaction safety | Contact, spacing, consent, retreat, hazard gating | partial conceptual alignment | `docs/safety/invariants.md`, `docs/safety/retreat_semantics.md`, `src/ohip/contact_planner.py` | partial |
| Functional safety / fault handling | Blocking, abort, latched faults, recovery | growing architectural alignment | `docs/safety/fault_handling.md`, `docs/safety/invariants.md` | partial |
| HRI evaluation / repeatability | Need for replay, benchmark, transparency | planned alignment | `ROADMAP.md`, `docs/architecture/node_graph.md` | planned |
| AI governance / risk management | Perception and policy decisions need bounded claims | growing alignment | `docs/governance/privacy_data_handling.md`, `docs/governance/threat_model.md`, `ROADMAP.md` | partial |
| Privacy / data handling | Consent, logs, replay, sensor artifacts | growing alignment | `src/ohip/consent_manager.py`, `docs/governance/privacy_data_handling.md` | partial |
| Robotics cybersecurity | Config, sensor, command, log integrity | growing alignment | `docs/governance/threat_model.md`, `docs/architecture/execution_adapter.md` | partial |
| Evidence / verification discipline | Need measurable support, not prose-only claims | planned alignment | `docs/safety/requirements_traceability.md`, `CHANGELOG.md`, `ROADMAP.md` | planned |

---

## 5. Domain-by-Domain Mapping

## 5.1 Robot Safety and Integration

### Why this domain is relevant
IX-HapticSight is concerned with:
- bounded human-facing motion
- contact-related constraints
- hazard-zone reasoning
- retreat and safe hold
- execution boundaries
- force-limit profiles

These are all safety-relevant topics in robot-system design and integration.

### Current alignment in the repo
Current relevant artifacts include:
- `docs/spec.md`
- `docs/state_machine.md`
- `configs/force_limits.yaml`
- `src/ohip/safety_gate.py`
- `src/ohip/contact_planner.py`

### What is still missing
To make this alignment materially stronger, the repo still needs:
- explicit runtime execution boundary
- stronger transition tests
- dedicated force-limit tests
- abort and retreat execution tests
- measured HIL evidence
- stronger standards traceability by requirement

### Current maturity
**Partial conceptual alignment**  
The repo clearly takes safety seriously, but it does not yet contain the runtime evidence or system-integration depth needed for stronger claims.

---

## 5.2 Collaborative Interaction Safety

### Why this domain is relevant
The project is not just about motion.
It is about motion near or involving a person, with contact constraints, consent conditions, and withdrawal behavior.

### Current alignment in the repo
Relevant artifacts include:
- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`
- `src/ohip/rest_pose.py`
- `docs/safety/invariants.md`
- `docs/safety/retreat_semantics.md`

### What is still missing
The repo still needs:
- explicit contact-state fusion
- better sensing abstractions
- runtime pre-contact verification logic
- benchmark scenarios for revocation, overforce, and retreat
- measurable evidence on timing and bounded contact behavior

### Current maturity
**Partial conceptual alignment**

---

## 5.3 Functional Safety and Fault Handling

### Why this domain is relevant
The project already distinguishes:
- blocking faults
- abort faults
- critical latched faults
- retreat and safe-hold outcomes

That is the start of a serious fault model.

### Current alignment in the repo
Relevant artifacts include:
- `docs/safety/fault_handling.md`
- `docs/safety/invariants.md`
- `docs/state_machine.md`
- `src/ohip/safety_gate.py`

### What is still missing
The repo still needs:
- explicit fault schemas
- latched fault state handling in code
- structured fault events
- fault-driven transition tests
- fault-injection harnesses
- execution/backend fault handling evidence

### Current maturity
**Partial but improving alignment**

---

## 5.4 HRI Evaluation, Repeatability, and Transparency

### Why this domain is relevant
A human-facing interaction system needs more than code.
It needs:
- repeatable scenarios
- benchmark metrics
- transparent state changes
- replayable outcomes
- inspectable reason codes

### Current alignment in the repo
Current relevant artifacts include:
- `ROADMAP.md`
- `docs/architecture/runtime_overview.md`
- `docs/architecture/node_graph.md`
- `docs/safety/requirements_traceability.md`

### What is still missing
The repo still needs:
- structured event logging
- replay tooling
- metrics schema
- benchmark runner
- scenario catalog
- benchmark result packages

### Current maturity
**Planned alignment**

---

## 5.5 AI Governance and Risk Management

### Why this domain is relevant
The project may eventually involve perception, signal interpretation, behavior selection, or policy mediation.
Even if the core remains deterministic, governance still matters because the system is human-facing.

### Current alignment in the repo
Relevant artifacts include:
- `ROADMAP.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/threat_model.md`
- `docs/safety/invariants.md`

### Project strengths here
The repo already leans in the right direction by:
- preferring bounded claims
- avoiding broad autonomy claims
- separating consent from convenience
- favoring deterministic safety rules
- explicitly defining non-claims

### What is still missing
The repo still needs:
- explicit AI-risk register
- model use boundary if ML components appear later
- dataset governance policy if training/evaluation datasets are added
- stronger benchmark and audit evidence

### Current maturity
**Partial alignment in governance posture**

---

## 5.6 Privacy and Data Handling

### Why this domain is relevant
The system may touch:
- consent records
- person-linked profiles
- sensor traces
- event logs
- replay bundles

That creates privacy obligations even before deployment.

### Current alignment in the repo
Relevant artifacts include:
- `src/ohip/consent_manager.py`
- `docs/governance/privacy_data_handling.md`
- `docs/spec.md`

### What is still missing
The repo still needs:
- retention configuration
- sanitization tooling
- replay export controls
- data-classification metadata in logs
- explicit raw-media handling controls if such data are ever added

### Current maturity
**Partial alignment**

---

## 5.7 Cybersecurity for Robotic Systems

### Why this domain is relevant
Compromise of:
- configs
- signals
- commands
- logs
can become a physical-safety problem.

### Current alignment in the repo
Relevant artifacts include:
- `docs/governance/threat_model.md`
- `docs/architecture/execution_adapter.md`
- `docs/architecture/runtime_overview.md`

### What is still missing
The repo still needs:
- config integrity checks in code
- source labeling for live vs replay
- structured provenance in logs
- runtime trust-boundary tests
- signed or hashed policy bundles for critical settings

### Current maturity
**Partial alignment**

---

## 6. Evidence Levels

To keep the crosswalk honest, the repo should distinguish four evidence levels.

### Level 0 — Mention only
A standard or domain is referenced, but the repo has no meaningful implementation or trace.

### Level 1 — Conceptual alignment
The repository architecture or docs align in spirit, but evidence is limited.

### Level 2 — Implemented trace
There is code, documentation, and at least some tests mapping to the domain.

### Level 3 — Strong evidence package
There are traceable artifacts such as:
- benchmarks
- replay records
- HIL evidence
- integrity checks
- measurable result bundles

At the current stage, most relevant domains are between **Level 1** and **Level 2**, with some still at **Level 0–1** depending on topic.

---

## 7. What This Crosswalk Does Not Mean

This document does **not** mean the repository is:
- certified
- compliant by declaration
- ready for production deployment
- sufficient for institutional approval
- legally cleared for all contexts

It only means the repository is attempting to align its architecture and documentation with the correct problem domains.

---

## 8. Near-Term Priorities to Strengthen the Crosswalk

The highest-value next steps are:

1. add stronger tests for consent, veto, force limits, and state transitions
2. create structured event and replay artifacts
3. add benchmark scenario and metric definitions
4. add integrity handling for critical configs
5. add runtime boundary code that preserves policy/safety separation
6. add HIL scaffolding and evidence templates

Those steps would materially raise the maturity of the crosswalk.

---

## 9. Current Repository Mapping Summary

Current baseline files that carry most of the alignment burden are:

- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/schemas.py`
- `src/ohip/consent_manager.py`
- `src/ohip/contact_planner.py`
- `src/ohip/safety_gate.py`
- `configs/force_limits.yaml`

New upgrade-era files that strengthen governance and traceability include:

- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/threat_model.md`

This is a stronger documentation spine than the baseline repo had, but it is still only part of the journey.

---

## 10. Review Questions

When a maintainer cites a standard or guidance domain in future docs, the reviewer should ask:

1. Is the domain actually relevant to this feature?
2. Is the alignment conceptual, implemented, or evidenced?
3. Which repo files support the claim?
4. Are there tests or metrics behind it?
5. Is the language overstating maturity?

If the answers are unclear, the standards language should be tightened.

---

## 11. Final Rule

A standards crosswalk is only useful if it reduces confusion.

If a standards reference makes the repo sound more mature than it really is, that reference is being used badly.
If it clarifies what the repo is trying to align with and what evidence is still missing, it is doing its job.
