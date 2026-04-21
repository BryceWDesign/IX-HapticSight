# Privacy and Data Handling

This document defines the privacy and data-handling posture for IX-HapticSight as the repository evolves from a protocol-oriented reference implementation into a stronger runtime and evidence-oriented interaction stack.

The current repository is not yet a full deployment system.
It does, however, already describe perception, consent, logging, and safety behavior in ways that can create privacy obligations if expanded into runtime tooling.

This document exists to keep those obligations explicit.

---

## 1. Purpose

The privacy model exists to answer these questions clearly:

- what kinds of data the project may touch
- which data are necessary for core safety behavior
- which data are optional and should be minimized
- what logging should and should not retain
- how replay and benchmark tooling should handle sensitive inputs
- what claims the repository must avoid making about privacy until evidence exists

The goal is not to make broad compliance claims.
The goal is to define a conservative engineering baseline.

---

## 2. Privacy Philosophy

IX-HapticSight should follow these principles:

- collect only what is necessary
- store less rather than more
- prefer structured summaries over raw media when possible
- preserve consent and safety evidence without over-retaining sensitive data
- separate operational need from curiosity
- make privacy-sensitive behavior explicit in configuration and documentation

This is especially important because the system may eventually involve:

- visual perception
- proximity sensing
- consent records
- contact-related events
- replay artifacts
- benchmark scenario data
- future HIL or controlled trial evidence

---

## 3. Data Categories

The project may involve multiple data categories with very different privacy implications.

### 3.1 Low-sensitivity technical metadata
Examples:
- software version
- benchmark seed values
- timing metrics
- backend status
- configuration version identifiers
- non-personal fault and event codes

Typical use:
- debugging
- benchmarking
- release validation
- safety traceability

---

### 3.2 Operational interaction metadata
Examples:
- session identifiers
- state transitions
- consent decision outcomes
- hazard classifications
- retreat reasons
- execution status
- force profile identifier used

Typical use:
- replay
- audit
- benchmark comparison
- fault analysis

Privacy note:
- this data can still become sensitive if it is tied to a real person identifier

---

### 3.3 Personal or person-linked metadata
Examples:
- subject profile identifiers
- caregiver-linked settings
- culture or contact preference selections
- individualized consent scope
- pseudonymous subject IDs

Typical use:
- policy enforcement
- consent logic
- runtime personalization within strict bounds

Privacy note:
- even pseudonymous IDs can become sensitive if linkable across sessions

---

### 3.4 Raw perception data
Examples:
- RGB frames
- depth frames
- thermal frames
- event camera streams
- microphone snippets if used for consent keywords
- raw proximity arrays
- raw tactile maps if contact involves a person

Typical use:
- perception debugging
- runtime sensing
- model tuning
- benchmark playback

Privacy note:
- this is often the highest-risk category and should be treated conservatively

---

### 3.5 Derived behavioral or contact data
Examples:
- approach timing
- contact duration
- estimated contact zone
- inferred comfort/risk flags
- motion traces around a human subject
- state transition history during interaction

Typical use:
- safety analysis
- benchmark metrics
- HIL or future study evidence

Privacy note:
- derived data can still reveal sensitive behavioral information even when raw media are absent

---

## 4. Minimum Data Rule

The default repository posture should be:

> retain the least sensitive form of data that still allows safety, debugging, replay, and benchmark objectives to be met.

That means:

- prefer event summaries over raw video when raw video is not essential
- prefer bounded force/contact summaries over continuous raw traces when practical
- prefer pseudonymous session identifiers over directly identifying subject names
- prefer opt-in capture over silent always-on retention

---

## 5. Data That Should Be Optional, Not Default

The following categories should not be treated as default persistent artifacts unless clearly justified:

- raw RGB video
- raw audio clips
- full thermal recordings
- long-duration subject-linked telemetry
- persistent biometric-like derived profiles
- unrestricted session history linked to one subject

If these are ever enabled, the repository should make that enablement explicit and reviewable.

---

## 6. Default Logging Direction

As the project adds structured logging, the preferred default is:

### Persist by default
- state transitions
- consent decision outcomes
- hazard classifications
- force-limit profile identifiers
- execution status
- retreat or abort reasons
- fault codes
- benchmark metrics
- replay-safe structured event records

### Do not persist by default
- raw face video
- raw audio
- directly identifying subject names
- unrestricted free-text operator notes containing personal details
- raw media exports with no retention boundary

This default supports auditability without unnecessary over-collection.

---

## 7. Consent Record Handling

Consent is central to IX-HapticSight, but consent records themselves require careful handling.

Recommended rules:

1. store only the minimum fields needed for runtime authorization and audit
2. prefer scoped consent over broad indefinite consent
3. preserve freshness and revocation status explicitly
4. avoid storing unnecessary personal context around the consent event
5. separate consent decision results from unnecessary raw input when possible

Examples:
- keeping a structured record that consent was granted for shoulder contact with a short TTL is usually stronger than storing a large raw media artifact forever
- storing a revocation event is important
- storing an unlimited archive of all raw interaction context is not automatically justified

---

## 8. Subject Identifiers

Where the system needs subject linkage across a session, it should prefer:

- pseudonymous identifiers
- session-scoped identifiers
- resettable linkage where possible

The system should avoid:
- direct legal names unless absolutely necessary
- identifiers that are stable forever without strong reason
- mixing identity, health-like context, and interaction logs casually

The repository should treat linkability itself as a privacy risk.

---

## 9. Video and Image Handling

The spec already points toward a conservative position.
That should remain true.

Preferred rules:

- video logging should be off by default
- image persistence should be off by default unless a benchmark or debugging workflow explicitly enables it
- if image or video persistence is enabled, the configuration should say so clearly
- if face or identity-bearing imagery is retained, the repository should document minimization or redaction expectations

A future stronger repository may add:
- redaction tooling
- cropped-region policies
- face/identity suppression workflows
- retention windows for media artifacts

Until then, the project should avoid overselling privacy protection it has not implemented.

---

## 10. Audio Handling

If microphone input is ever used for consent keywords or operator commands, the preferred direction is:

- process minimally
- avoid storing raw audio by default
- persist only structured decision events when possible
- require explicit enablement for retained audio artifacts

This keeps the system aligned with a minimum-data posture.

---

## 11. Replay and Benchmark Privacy Rules

Replay and benchmarking are valuable, but they can quietly turn into surveillance-style retention if left vague.

Recommended rules:

1. replay artifacts should prefer structured event streams
2. raw media should be optional, not assumed
3. benchmark packages should be sanitized before sharing
4. subject-linked identifiers in replay should be pseudonymous
5. shared artifacts should avoid unnecessary raw human data

A replay artifact should be useful for engineering review without becoming a casual archive of identifiable interaction footage.

---

## 12. Data Retention Direction

The repository should distinguish between:

### Ephemeral runtime data
Used for immediate control and discarded unless needed for audit or fault review.

Examples:
- current fused signal buffers
- transient execution progress
- short-lived perception buffers

### Short-term audit data
Retained long enough for debugging, safety review, or benchmark comparison.

Examples:
- structured event logs
- failure summaries
- retreat/abort records
- benchmark metrics reports

### Extended evidence data
Retained only when a specific evidence purpose exists.

Examples:
- HIL calibration records
- controlled benchmark bundles
- selected replay artifacts tied to a known test objective

The repo should not assume everything deserves indefinite retention.

---

## 13. Access Control Direction

As runtime and evidence tooling grow, access expectations should also be documented.

Preferred direction:
- operational configs separated from evidence bundles
- raw sensitive artifacts stored more restrictively than sanitized summaries
- clear distinction between developer diagnostics and shareable benchmark outputs
- no assumption that all team members need all data

The current repo does not yet implement a full access-control system.
This document sets the expectation that sensitivity tiers should eventually matter.

---

## 14. Configuration Expectations

Privacy-relevant behavior should not remain hidden in code.

Future configuration should eventually expose choices such as:

- whether raw media logging is enabled
- whether face- or identity-bearing imagery is retained
- retention windows for event logs
- pseudonymization mode
- benchmark export sanitization mode
- replay export sensitivity mode

That way privacy posture becomes inspectable rather than implicit.

---

## 15. Current Repository Mapping

Current baseline artifacts relevant to privacy and data handling include:

- `docs/spec.md`
- `docs/state_machine.md`
- `src/ohip/schemas.py`
- `src/ohip/consent_manager.py`

Important current signals:
- the project already talks about consent
- the state machine already references privacy defaults
- schemas already include consent-related data structures

What is still missing:
- structured event logging package
- replay package
- sanitization tooling
- retention configuration
- benchmark export privacy controls
- explicit policy bundle format for data handling

This document exists so those later additions have a clear direction.

---

## 16. Non-Claims

This repository should not claim, unless evidence later exists, that it is:

- fully privacy compliant in all jurisdictions
- anonymized by default in every future integration
- production-ready for sensitive real-world deployment
- sufficient on its own for legal or regulatory review
- a complete substitute for institutional privacy governance

The appropriate claim right now is narrower:
the repository is defining a conservative engineering privacy posture.

---

## 17. Review Questions

When new logging, replay, sensing, or benchmark code is added, reviewers should ask:

1. Is this data actually needed?
2. Can a less sensitive representation work instead?
3. Does this persist raw human data by default?
4. Is the retention purpose clear?
5. Is subject linkage stronger than necessary?
6. Can the artifact be shared safely in sanitized form?
7. Does documentation match actual behavior?

If those questions cannot be answered cleanly, the privacy design is too weak.

---

## 18. Final Rule

The repository should prefer smaller, more explicit, more temporary data capture over broad silent retention.

A safety-first human-facing system that ignores privacy boundaries is not disciplined enough.
