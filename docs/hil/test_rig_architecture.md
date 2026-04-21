# HIL Test Rig Architecture

This document defines the recommended hardware-in-the-loop (HIL) test-rig architecture for IX-HapticSight.

At the current repository stage, this is a **planning and evidence-structure document**, not proof that the rig has been built or validated.
Its purpose is to define:

- what a credible HIL rig should contain
- what measurements it should produce
- how those measurements should map back to repository claims
- how future HIL evidence should be packaged

This is the bridge between the current software-first repo and future measured physical evidence.

---

## 1. Purpose

A HIL rig is needed because software benchmarks alone cannot answer the hardest questions in a human-facing interaction system.

Software benchmarks can help show:
- correct decision paths
- correct denial logic
- correct event emission
- correct replay behavior

They cannot by themselves show:
- real contact force behavior
- real retreat timing
- real backend response to faults
- real overforce detection latency
- real safe-hold fallback behavior under motion constraints

The HIL architecture exists to close that gap.

---

## 2. Current Repo Status

What the repo already has:

- protocol schemas
- runtime coordination
- structured event logging
- replay helpers
- interface models for:
  - force/torque
  - tactile
  - proximity
  - thermal
- simulated execution adapter
- deterministic benchmark runner
- benchmark reporting layer

What the repo does **not** yet have:

- a real HIL adapter
- calibrated physical test fixture definitions in code
- measured force traces
- measured retreat timing
- measured thermal trip behavior
- measured actuator abort timing

So this document is intentionally future-facing.

---

## 3. What the HIL Rig Should Prove

A serious HIL rig for IX-HapticSight should help answer questions like:

### Contact control questions
- does the system stay within expected force bounds
- how quickly does force rise and fall
- what peak force actually occurs at contact
- what happens when the requested dwell ends

### Fault behavior questions
- how fast does the system react to overforce
- what happens when a safety trigger occurs during motion
- can retreat begin reliably after fault detection
- when does the system fall back to safe hold instead

### Sensing questions
- are force/torque signals fresh enough
- can tactile signals reveal contact spread or pressure concentration
- does proximity support safer near-contact slowdown
- can thermal signals trigger a clean safety response

### Evidence questions
- can the event log be aligned with measured traces
- can a future reviewer reproduce what happened
- can a requirement be traced to a test and a measured artifact

That is the real value of a HIL rig here.

---

## 4. Recommended Rig Layers

A strong HIL rig for this repo should have five layers.

### Layer A — Structural test fixture
A stable physical fixture that represents the interaction surface or contact target.

Examples:
- compliant shoulder-shaped fixture
- flat pad with controlled compliance
- modular contact block with replaceable layers

Purpose:
- provide repeatable contact geometry
- support multiple material and compliance conditions
- make contact trials comparable

---

### Layer B — Sensing and instrumentation
The rig should include at least some of:

- calibrated load cell or force sensor
- 6-axis force-torque sensor where practical
- tactile patch or contact-pressure sensing surface where possible
- proximity sensing zone near the contact region
- thermal sensing point or surface sensor
- timing source for synchronized timestamps

Purpose:
- convert “it seemed okay” into measured data

---

### Layer C — Execution backend under test
The rig should exercise a real execution path, not only synthetic function calls.

Possible progression:
1. simulated execution adapter
2. middleware-connected execution adapter
3. physical actuator / controller bridge
4. higher-fidelity motion backend

Purpose:
- gradually increase realism while keeping observability

---

### Layer D — Safety and interrupt path
A HIL rig must explicitly test fault and stop behavior, not just nominal contact.

Examples:
- overforce injection
- artificial stale-signal condition
- simulated sensor drop
- backend refusal
- manual abort input
- safe-hold command path

Purpose:
- prove the system handles bad cases, not just happy paths

---

### Layer E — Evidence capture and packaging
The HIL rig should record artifacts in structured form.

Examples:
- measured force trace
- thermal trace
- event log JSONL
- benchmark scenario ID
- calibration reference
- fault-injection note
- operator note if needed
- run manifest

Purpose:
- make the result reviewable and traceable later

---

## 5. Recommended Initial Fixture

The first serious HIL fixture should stay narrow.

Recommended v1 fixture:
- one shoulder-support-style contact region
- compliant target surface
- one force measurement path
- one basic retreat path
- one backend stop path

Why narrow:
- smaller scope means stronger evidence sooner
- fewer variables means clearer debugging
- easier alignment with current repo mission

The repo does **not** need a humanoid rig first.
It needs a **repeatable, instrumented contact rig** first.

---

## 6. Minimum Instrumentation Set

If the HIL rig had to start with the minimum credible measurement stack, I would choose:

1. **Calibrated force measurement**
   - non-negotiable

2. **Timestamped event logging**
   - already fits the repo direction

3. **One controlled actuator or motion backend**
   - even if simple

4. **One hard abort path**
   - to measure stop behavior

5. **One retreat-capable motion path**
   - to measure withdrawal behavior

Everything else is valuable, but those are the minimum “this is becoming real” pieces.

---

## 7. Recommended Optional Instrumentation

As the rig matures, add:

- tactile patch sensing
- short-range proximity sensing
- thermal sensing on the interaction surface
- synchronized video reference for lab-only debugging
- motion capture or encoder-derived pose history
- external timing or trigger channel for fault injection correlation

These make the evidence richer, but they should not replace the basics.

---

## 8. Example HIL Trial Classes

The first trial catalog should be small and explicit.

### Trial class A — Nominal bounded contact
Goal:
- verify measured force remains within expected limits
- verify dwell behavior
- verify release behavior

### Trial class B — Overforce interruption
Goal:
- trigger force threshold
- verify abort or retreat behavior
- measure detection-to-response timing

### Trial class C — Retreat path trial
Goal:
- begin nominal approach/contact
- force retreat condition
- verify retreat start and completion timing

### Trial class D — Safe-hold fallback trial
Goal:
- make retreat unavailable or unsafe
- verify safe-hold path is explicit and measurable

### Trial class E — Sensor freshness/fault trial
Goal:
- inject stale or invalid sensor condition
- verify runtime denial or interruption behavior

These trial classes map directly to the repo’s strongest safety claims.

---

## 9. Recommended Artifact Set Per Trial

Each HIL trial should eventually produce a bundle with at least:

- trial ID
- benchmark/scenario ID if applicable
- rig configuration ID
- calibration reference IDs
- event log path
- measured force trace path
- optional thermal/proximity/tactile trace paths
- expected outcome
- observed outcome
- operator note if needed
- timestamp window
- pass/fail/error result
- reason code

That is the minimum artifact discipline needed to make a future HIL result trustworthy.

---

## 10. Mapping Back to Repo Requirements

The HIL rig should not become a disconnected lab toy.
Its outputs should map back to documented repo structure:

- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`
- `docs/governance/safety_case.md`
- `docs/benchmarks/metrics.md`

Examples:
- overforce trial maps to force and fault invariants
- retreat timing trial maps to retreat semantics
- safe-hold fallback trial maps to fault-handling expectations
- event-log correlation maps to replay/logging evidence

That traceability is the real point.

---

## 11. Recommended HIL Data Flow

A future HIL run should ideally look like this:

1. choose explicit scenario or trial definition
2. load rig configuration and calibration references
3. initialize runtime service / execution backend
4. run the trial
5. capture:
   - event log
   - measured traces
   - execution backend status
   - timing markers
6. package the artifact bundle
7. compare expected vs observed outcomes
8. update benchmark/reporting layer where appropriate

This preserves continuity with the current repo architecture.

---

## 12. Current Gaps Before Real HIL Work

Before real HIL can be credible, the repo still needs:

- calibration conventions
- fault-injection procedure conventions
- artifact manifest conventions
- stronger event-log schema versioning
- clearer trial ID / bundle ID conventions
- actual physical backend integration later

That is why this doc belongs before any strong HIL claims.

---

## 13. Review Questions

When evaluating a proposed HIL rig plan, ask:

1. What exact repo claim does this rig test?
2. What is physically measured?
3. How are timestamps aligned?
4. What makes the trial repeatable?
5. What artifact bundle comes out of it?
6. How does the result trace back to repo requirements?

If those answers are weak, the rig design is weak.

---

## 14. Final Rule

A HIL rig should reduce uncertainty about physical behavior.

If it produces impressive-looking demos without traceable measurements, it is not strong enough for this repo.
