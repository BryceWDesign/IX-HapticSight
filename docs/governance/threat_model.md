# Threat Model

This document defines the baseline threat model for IX-HapticSight as the repository evolves from a protocol-oriented reference implementation into a stronger runtime and execution-aware interaction stack.

The project is concerned with human-facing robot behavior.
That means cybersecurity and integrity risks cannot be treated as a side topic.
A compromised policy bundle, spoofed sensor feed, or unauthorized command path can become a physical-safety problem.

This document exists to define the main trust boundaries, threat surfaces, and conservative assumptions before deeper runtime integration is added.

---

## 1. Purpose

The threat model exists to answer these questions clearly:

- what assets matter
- who or what may threaten them
- where the trust boundaries are
- what kinds of compromise could become safety-relevant
- which risks the repository should explicitly constrain
- which assumptions are still open or unproven

The goal is not to claim complete security.
The goal is to make the security posture inspectable and non-naive.

---

## 2. Threat-Model Philosophy

IX-HapticSight should assume the following:

- software can be misconfigured
- telemetry can be stale or spoofed
- command paths can be abused
- logs can be incomplete or tampered with
- identity and consent records can be mishandled
- convenience features can accidentally weaken safety boundaries

The repository should therefore prefer:

- explicit trust boundaries
- versioned policy artifacts
- structured fault and event logging
- integrity checks for critical configuration
- minimal authority per component
- narrow execution privileges
- conservative fallback behavior when trust is uncertain

---

## 3. Scope

This threat model applies to:

- protocol logic in `src/ohip/`
- future runtime orchestration layers
- future sensing interface layers
- future execution adapter layers
- structured event logging and replay artifacts
- benchmark and evidence packages where integrity matters

This document does not claim to replace:
- a full deployment-specific penetration test
- hardware controller security review
- enterprise network hardening
- legal or regulatory approval

---

## 4. High-Value Assets

The following assets are especially important.

### 4.1 Safety-critical policy artifacts
Examples:
- force-limit profiles
- consent policy semantics
- hazard threshold rules
- retreat and safe-hold policy
- interaction mode restrictions

Why they matter:
- unauthorized modification could turn bounded behavior into unsafe permissive behavior

---

### 4.2 Consent and authorization state
Examples:
- consent records
- consent freshness state
- revocation status
- caregiver override scope
- subject-linked profile selection

Why they matter:
- compromise could allow contact that should be denied or prevent contact logging from reflecting reality

---

### 4.3 Sensor and signal inputs
Examples:
- force-torque readings
- proximity readings
- thermal readings
- tactile readings
- scene hazard summaries
- signal freshness metadata

Why they matter:
- spoofed or stale inputs can corrupt safety decisions

---

### 4.4 Runtime state and transition authority
Examples:
- interaction state
- fault-latch state
- retreat requests
- abort requests
- execution status
- watchdog state

Why they matter:
- hidden or unauthorized transitions can bypass safety expectations

---

### 4.5 Execution command path
Examples:
- backend motion commands
- abort commands
- retreat commands
- safe-hold commands

Why they matter:
- unauthorized or modified commands can create direct physical risk

---

### 4.6 Event logs and evidence bundles
Examples:
- structured event logs
- replay bundles
- benchmark result records
- HIL evidence packages

Why they matter:
- tampering can hide faults, falsify evidence, or weaken trust in the system

---

## 5. Trust Boundaries

The upgraded repository should assume multiple trust boundaries.

### 5.1 Operator or upstream application boundary
Requests may arrive from:
- UI
- supervisory application
- scripted benchmark runner
- replay tooling
- remote control layer

Risk:
- upstream intent may be malformed, unauthorized, stale, or ambiguous

Mitigation direction:
- explicit validation
- session-aware request handling
- narrow request schemas
- structured denial reasons

---

### 5.2 Policy/configuration boundary
Configuration files and policy bundles may be:
- edited incorrectly
- replaced with malicious versions
- loaded out of version order
- mismatched against code expectations

Risk:
- silent drift in force, consent, or safety semantics

Mitigation direction:
- version tagging
- schema validation
- bundle hashing
- signed or integrity-checked artifacts for critical configs

---

### 5.3 Sensor ingestion boundary
Sensor data may arrive from:
- physical devices
- simulators
- test harnesses
- replay feeds
- middleware topics or adapters

Risk:
- spoofed data
- stale data
- inconsistent timestamps
- modality mismatch
- missing health metadata

Mitigation direction:
- freshness checks
- normalization
- explicit signal-health fields
- rejection of underspecified critical inputs

---

### 5.4 Runtime coordination boundary
The coordinator receives and routes:
- requests
- approvals
- vetoes
- plans
- execution commands
- fault notifications

Risk:
- over-centralized authority
- silent state mutation
- bypass of consent or safety checks

Mitigation direction:
- explicit state ownership
- testable transition rules
- structured event emission
- independent veto authority

---

### 5.5 Execution/backend boundary
Execution may involve:
- simulation backend
- test executor
- future ROS 2 bridge
- future motion-planning backend
- future robot controller bridge

Risk:
- backend ignores limits
- command tampering
- backend reports false success
- abort path not honored promptly

Mitigation direction:
- execution adapter boundary
- structured acknowledgements
- separate abort semantics
- backend capability reporting
- benchmarked fault scenarios

---

### 5.6 Logging and evidence boundary
Event and replay artifacts may be:
- incomplete
- overwritten
- modified after the fact
- misattributed across sessions

Risk:
- false confidence
- hidden faults
- invalid benchmark comparison
- weak audit value

Mitigation direction:
- append-oriented logs where practical
- content hashing
- bundle manifests
- timestamps and reason codes
- artifact provenance metadata

---

## 6. Threat Actors and Failure Sources

Threats do not only come from an external attacker.
The following sources matter.

### 6.1 Accidental developer or maintainer error
Examples:
- wrong config edit
- weakened threshold
- silent change in default behavior
- removing safety logic while refactoring

This is one of the most realistic threats.

---

### 6.2 Curious but unauthorized operator
Examples:
- changing profile behavior to “make it work”
- bypassing logging
- replaying or exporting sensitive data carelessly
- overriding force or retreat parameters without review

---

### 6.3 Malicious local actor
Examples:
- editing configuration artifacts
- injecting spoofed sensor data
- suppressing fault logs
- issuing unauthorized execution commands

---

### 6.4 Remote attacker through connected runtime infrastructure
Examples:
- command injection through a networked interface
- replaying stale commands
- tampering with middleware messages
- unauthorized access to stored evidence bundles

---

### 6.5 Faulty or compromised device or middleware component
Examples:
- drifting timestamps
- corrupted sensor bridge
- delayed signal transport
- backend falsely reporting completion

This matters even without a human attacker.

---

## 7. Primary Threat Categories

### 7.1 Unauthorized permission escalation
Threat:
- a component grants broader contact or execution permission than policy allows

Examples:
- stale consent treated as fresh
- blocked interaction reclassified as allowed
- execution layer softens planner limits

Safety consequence:
- contact or motion proceeds without proper authorization

Mitigation direction:
- explicit policy evaluation
- hard invariants
- testable denial paths
- no hidden authority expansion

---

### 7.2 Sensor spoofing or stale-signal misuse
Threat:
- safety-relevant inputs are fabricated, delayed, or treated as valid when stale

Examples:
- fake clear proximity signal
- stale force reading used during contact
- replayed thermal reading treated as live

Safety consequence:
- unsafe continuation or unsafe initiation of motion

Mitigation direction:
- timestamp checks
- freshness invariants
- signal health fields
- benchmark scenarios for stale data

---

### 7.3 Policy/configuration tampering
Threat:
- a config or policy bundle is modified outside approved review

Examples:
- increased force ceiling
- disabled retreat behavior
- relaxed consent freshness
- altered hazard semantics

Safety consequence:
- runtime behaves outside intended safety envelope

Mitigation direction:
- schema validation
- version pinning
- content hashing
- signed bundle direction for critical settings

---

### 7.4 Unauthorized or malformed execution commands
Threat:
- a command path triggers movement outside approved plans

Examples:
- raw backend motion injected directly
- replay artifact mistaken for live command
- malformed retreat request
- command issued without consent and safety checks

Safety consequence:
- direct physical risk

Mitigation direction:
- execution adapter boundary
- narrow command schemas
- command-source separation
- structured command provenance

---

### 7.5 Log suppression or evidence tampering
Threat:
- important events are not recorded, are altered, or lose provenance

Examples:
- overforce event deleted
- retreat failure omitted from result bundle
- benchmark output rewritten to appear cleaner

Safety consequence:
- unsafe system appears trustworthy
- faults cannot be reviewed honestly

Mitigation direction:
- append-friendly event model
- bundle manifests
- artifact hashing
- provenance metadata
- reviewable report generation

---

### 7.6 Replay-to-live confusion
Threat:
- replay data or benchmark tooling is confused with live runtime inputs

Examples:
- replayed consent record injected into live session
- simulated sensor data enters runtime path without being labeled
- benchmark runner exercises live command path accidentally

Safety consequence:
- false authorization or unsafe motion based on non-live data

Mitigation direction:
- environment labeling
- mode separation
- explicit source metadata
- hard guardrails between live and replay modes

---

### 7.7 Privacy and identity misuse
Threat:
- unnecessary personal or person-linked data are exposed, retained, or cross-linked

Examples:
- replay artifact contains identifiable video by default
- subject-linked logs retained without purpose
- raw data exported casually for debugging

Safety consequence:
- user harm, trust erosion, governance failure

Mitigation direction:
- data minimization
- explicit retention controls
- pseudonymous identifiers
- sanitized benchmark outputs

---

## 8. Security-Relevant Assumptions

The current repository may reasonably assume, for now:

- developers act in good faith but can still make mistakes
- the current Python reference implementation is not exposed as a hardened network service
- hardware actuation is not yet directly controlled from this repo
- the repo is still at concept/prototype maturity, not deployment maturity

The repository should **not** assume:
- all inputs are trustworthy
- configs are always correct
- logs are automatically reliable
- a single coordinator should have unchecked total authority
- future runtime integrations will inherit safety automatically

---

## 9. Security Controls Direction

The following controls are appropriate design targets for the upgrade campaign.

### 9.1 Configuration integrity
- schema validation
- policy bundle versioning
- content hashes
- signed critical bundles where feasible

### 9.2 Request validation
- typed request schemas
- reason codes
- source metadata
- rejection of under-specified requests

### 9.3 Signal trust controls
- freshness checks
- signal health flags
- modality-required checks
- source labeling for live vs replay

### 9.4 Execution path hardening
- explicit execution adapter boundary
- command acknowledgement semantics
- abort priority
- backend capability declaration

### 9.5 Evidence integrity
- append-oriented logs where practical
- artifact manifest files
- hashable evidence bundles
- provenance-aware benchmark outputs

### 9.6 Privacy controls
- data minimization
- replay sanitization
- pseudonymous identifiers
- explicit retention and export behavior

---

## 10. Current Repository Mapping

Current baseline artifacts relevant to this threat model include:

- `src/ohip/schemas.py`
- `src/ohip/consent_manager.py`
- `src/ohip/safety_gate.py`
- `docs/spec.md`
- `docs/state_machine.md`
- `configs/force_limits.yaml`
- `configs/culture_profiles.yaml`

What is still missing:
- explicit runtime trust-boundary code
- bundle integrity checks
- structured event logger
- replay mode separation
- execution adapter package
- dedicated threat-oriented tests

This document exists so those additions have a disciplined frame.

---

## 11. Review Questions

When adding new runtime, sensing, execution, replay, or configuration code, reviewers should ask:

1. What trust boundary does this cross?
2. Could this input be stale, spoofed, or malformed?
3. Can this component expand authority silently?
4. Could this change hide or weaken evidence of faults?
5. Does this blur live and replay paths?
6. Does it increase privacy exposure?
7. Is the failure mode conservative if trust is uncertain?

If those questions cannot be answered clearly, the security posture is too weak.

---

## 12. Non-Claims

This repository should not claim, unless later evidence exists, that it is:

- penetration tested
- production hardened
- secure by certification
- safe against all adversaries
- sufficient on its own for operational deployment approval

The appropriate claim right now is narrower:
the repository defines a conservative threat-aware engineering posture for a human-facing interaction stack.

---

## 13. Final Rule

Any component that can change physical behavior, safety interpretation, or evidence integrity should be treated as security-relevant.

If trust in a critical path is uncertain, the system should narrow behavior rather than widen it.
