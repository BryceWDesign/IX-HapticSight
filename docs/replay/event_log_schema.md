# Event Log Schema

This document defines the structured event-log schema used by IX-HapticSight for:

- runtime audit trails
- replay inputs
- benchmark artifacts
- debugging bundles
- future evidence packaging

The current event-log implementation is JSONL-based and lives in:

- `src/ohip_logging/events.py`
- `src/ohip_logging/jsonl.py`
- `src/ohip_logging/recorder.py`
- `src/ohip_logging/replay.py`

This document is the reviewer-facing explanation of that schema.

---

## 1. Purpose

The event log exists to answer:

- what happened
- when it happened
- which session or request it belonged to
- what state the runtime believed it was in
- why a transition, denial, or fault occurred
- whether the resulting sequence can be replayed later

The goal is not to log everything forever.
The goal is to log enough structured information to support:
- audit
- debugging
- replay
- benchmark comparison
- future evidence bundling

---

## 2. Current Storage Format

The current event-log format is:

**newline-delimited JSON (`.jsonl`)**

Each line is one serialized event record.

Why JSONL:
- append-friendly
- easy to inspect
- easy to replay
- easy to store in artifacts
- simpler than inventing a custom binary format at this repo stage

Current utilities:
- append one or many events
- load all events
- iterate through an event log
- tail a log
- fetch last event
- overwrite a log deterministically

These are implemented in:
- `src/ohip_logging/jsonl.py`

---

## 3. Canonical Event Record Shape

The canonical structured event record is represented by `EventRecord` in:

- `src/ohip_logging/events.py`

Current fields are:

- `event_id`
- `kind`
- `session_id`
- `request_id`
- `interaction_state`
- `execution_state`
- `runtime_health`
- `reason_code`
- `created_at_utc_s`
- `details`

This is intentionally compact.

---

## 4. Field Definitions

## 4.1 `event_id`
**Type:** string

A unique or near-unique identifier for the event within a log or bundle.

Examples:
- `req-1:request`
- `req-1:consent`
- `req-1:decision`
- `sess-1:abort_transition`

Why it matters:
- allows targeted replay slicing
- allows range selection
- allows more deterministic comparisons

---

## 4.2 `kind`
**Type:** enum-like string

Current event kinds include:

- `REQUEST_RECEIVED`
- `CONSENT_EVALUATED`
- `SAFETY_EVALUATED`
- `PLAN_CREATED`
- `COORDINATION_DECIDED`
- `STATE_TRANSITION`
- `FAULT_APPLIED`
- `EXECUTION_STATUS`
- `RETREAT_STATUS`
- `SAFE_HOLD_STATUS`
- `BENCHMARK_MARKER`
- `REPLAY_MARKER`

Why it matters:
- drives replay filtering
- enables grouped analysis
- supports benchmark and audit categorization

---

## 4.3 `session_id`
**Type:** string or null

The runtime session the event belongs to.

Why it matters:
- groups related events across one runtime interaction context
- supports replay by session
- helps separate concurrent or batched evaluations later

---

## 4.4 `request_id`
**Type:** string or null

The request or execution request the event belongs to.

Why it matters:
- separates multiple requests within one session
- supports replay and analysis by request
- preserves causal trace between request, decision, and execution

---

## 4.5 `interaction_state`
**Type:** string or null

The runtime interaction state associated with the event.

Typical values:
- `IDLE`
- `VERIFY`
- `APPROACH`
- `PRECONTACT`
- `CONTACT`
- `RETREAT`
- `SAFE_HOLD`
- `FAULT_LATCHED`

Why it matters:
- supports audit and transition reasoning
- helps distinguish runtime posture during faults or denials

---

## 4.6 `execution_state`
**Type:** string or null

The runtime execution state associated with the event.

Typical values:
- `IDLE`
- `READY`
- `EXECUTING`
- `ABORTING`
- `RETREATING`
- `SAFE_HOLD`
- `FAULTED`
- `UNAVAILABLE`

Why it matters:
- keeps execution posture visible
- avoids forcing reviewers to infer execution state from scattered logs

---

## 4.7 `runtime_health`
**Type:** string or null

The runtime health summary associated with the event.

Typical values:
- `NOMINAL`
- `DEGRADED`
- `BLOCKED`
- `FAULTED`

Why it matters:
- makes degraded or faulted operation explicit
- helps group logs by severity context

---

## 4.8 `reason_code`
**Type:** string

A short, machine-friendly explanation of the event.

Examples:
- `consent_ok`
- `consent_missing_or_invalid`
- `safety_ok`
- `session_safety_red`
- `overforce`
- `operator_abort`

Why it matters:
- supports benchmark comparison
- supports replay filtering
- prevents event logs from becoming vague or prose-heavy

---

## 4.9 `created_at_utc_s`
**Type:** float

Unix-style UTC timestamp in seconds.

Why it matters:
- ordering
- replay timing
- merge behavior
- result packaging

At the current stage this is still software-side time, not certified timing evidence.

---

## 4.10 `details`
**Type:** mapping / object

Structured event-specific payload.

Examples:
- request parameters
- consent decision details
- safety decision flags
- planning result presence
- execution acceptance state
- fault severity/disposition
- transition source/target state details

Why it matters:
- allows event-specific information without changing the top-level schema for every event kind

Risk:
- if uncontrolled, `details` can become a junk drawer

Rule:
- `details` should remain structured, scoped, and relevant

---

## 5. Current Event Kinds and Their Typical Details

## 5.1 `REQUEST_RECEIVED`
Typical details:
- interaction kind
- request source
- target name
- requested scope
- requires contact flag
- consent freshness requirement
- subject ID
- request timestamp
- notes

---

## 5.2 `CONSENT_EVALUATED`
Typical details:
- decision status
- consent mode
- consent validity
- consent freshness
- scope allowed
- evaluation timestamp

---

## 5.3 `SAFETY_EVALUATED`
Typical details:
- decision status
- safety level
- may approach
- may contact
- requires retreat
- requires safe hold
- evaluation timestamp

---

## 5.4 `PLAN_CREATED`
Typical details:
- planning status
- degraded flag
- has plan flag
- serialized plan if present
- planning timestamp

---

## 5.5 `COORDINATION_DECIDED`
Typical details:
- final decision status
- executable flag
- decision timestamp
- consent status
- safety status
- planning status
- plan presence

---

## 5.6 `STATE_TRANSITION`
Typical details:
- from interaction state
- to interaction state
- from execution state
- to execution state

This is one of the most important event kinds for later audit and replay quality.

---

## 5.7 `FAULT_APPLIED`
Typical details:
- source
- severity
- disposition
- latched flag
- abort/retreat/safe-hold flags
- fault timestamp
- optional fault details

`RETREAT_STATUS` and `SAFE_HOLD_STATUS` use the same structural style with more specific kind labels.

---

## 5.8 `EXECUTION_STATUS`
Typical details:
- safety level
- accepted flag
- backend status
- progress

This is the main execution-side event kind in the current repo.

---

## 6. Serialization Rules

Current serialization rules:

1. each event is serialized as one JSON object per line
2. top-level records are sorted consistently by JSON serializer configuration
3. blank lines are ignored on read
4. non-object JSON lines are rejected
5. invalid JSON raises an explicit error

This is implemented in:
- `src/ohip_logging/jsonl.py`

The goal is deterministic, simple behavior rather than cleverness.

---

## 7. Replay Expectations

The replay layer currently assumes that event logs:

- preserve order as written
- preserve event IDs
- preserve event kinds
- preserve state fields
- preserve reason codes
- preserve replay-relevant details

Replay helpers live in:
- `src/ohip_logging/replay.py`

Current replay features include:
- iterate through an event stream
- filter by session
- filter by request
- filter by kind
- select a contiguous range between event IDs
- merge multiple streams deterministically
- produce simple summaries

This means the event log schema must remain replay-friendly.

---

## 8. Current Schema Strengths

The current event-log schema is already strong in a few important ways:

- compact and explicit
- request/session aware
- reason-code aware
- replay-aware
- append-friendly
- deterministic enough for benchmark use

That is a good foundation for a repo at this stage.

---

## 9. Current Schema Limits

Important current limits include:

- no explicit schema version field yet
- no artifact manifest linkage yet
- no cryptographic integrity or signing yet
- no redaction/sanitization metadata yet
- no event source trust-level field yet
- no explicit HIL trace linkage yet

Those should remain visible as future work.

---

## 10. Recommended Near-Term Schema Additions

The next highest-value additions would be:

### 10.1 `schema_version`
A top-level schema version field to make future log compatibility clearer.

### 10.2 `source_mode`
A top-level event source mode such as:
- live
- replay
- simulation
- benchmark

This would strengthen replay and trust-boundary clarity.

### 10.3 `artifact_id`
A field linking events to a benchmark bundle, replay bundle, or future HIL evidence bundle.

### 10.4 `sensitivity`
A field for export/privacy handling of event records when logs become more widely shared.

### 10.5 `trace_links`
A structured field for linking events to:
- requirements
- invariants
- benchmark scenarios
- HIL evidence later

These are not required to use the current system, but they would improve long-term traceability.

---

## 11. Privacy and Security Notes

The event log should remain aligned with:
- `docs/governance/privacy_data_handling.md`
- `docs/governance/threat_model.md`

Practical implications:
- avoid stuffing raw sensitive media into `details`
- avoid directly identifying subject data unless strictly needed
- preserve structured reasons and states without over-collecting sensitive artifacts
- treat event logs as integrity-relevant artifacts once they become evidence

---

## 12. Review Questions

When changing the event schema, reviewers should ask:

1. Does this field improve auditability or replayability?
2. Is this top-level field really top-level, or should it live in `details`?
3. Does this change preserve compatibility or clearly break it?
4. Does this field increase privacy exposure?
5. Does this field increase ambiguity instead of reducing it?
6. Will this still be easy to replay and compare later?

If those answers are weak, the schema change is probably weak.

---

## 13. Final Rule

The event log schema should help a reviewer reconstruct what happened without guessing.

If an event trail cannot explain the runtime story clearly, the schema is not strong enough.
