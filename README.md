# IX-HapticSight

**IX-HapticSight** is a safety-first optical-haptic interaction architecture for bounded human-facing robot behavior.

The repository is built around one narrow idea:

> convert perception, consent state, safety state, and bounded contact rules into explicit approach, contact, retreat, and safe-hold behavior that can be inspected, tested, replayed, and benchmarked.

This repo is **not** positioned as a broad “emotion-aware robot” claim, a production deployment stack, or a certified collaborative robot package. It is a **measurement-first, audit-friendly reference architecture** with working code, tests, structured logging, replay helpers, interface abstractions, and deterministic benchmark support.

---

## Current Status

**Current maturity:** strong repository architecture / reference-runtime stage

What the repo currently includes:

- deterministic OHIP protocol core
- backend-agnostic runtime coordination layer
- explicit runtime session and fault models
- structured JSONL event logging
- replay helpers for event streams
- normalized interface models for:
  - force/torque
  - tactile
  - proximity
  - thermal
  - execution adapters
- in-memory simulated execution adapter
- deterministic benchmark runner, scenario catalog, and reporting helpers
- expanded safety, governance, replay, benchmark, and HIL-prep documentation
- unit tests and CI workflow

What it does **not** currently include:

- real hardware integration
- HIL measured data
- certified safety evidence
- production deployment approval
- medical or therapeutic validation
- blanket privacy or compliance claims

That line matters. This repo is strongest when it stays precise.

---

## What the Repository Is Trying to Do

IX-HapticSight is trying to make one difficult boundary explicit:

**when a machine is allowed to approach, touch, withdraw, or stop around a person — and how that decision is made visible and reviewable.**

The repo is built around:

- bounded interaction semantics
- consent-aware contact authorization
- safety-veto authority over convenience behavior
- explicit retreat and safe-hold semantics
- replayable event trails
- scenario-based benchmark evaluation
- traceable evidence growth toward future HIL work

---

## What the Repository Is Not

This repository is **not**:

- a general social robotics framework
- a claim of human-emotion understanding
- a production manipulator stack
- a guarantee of safe real-world touch
- a substitute for hardware safety engineering
- a substitute for regulatory, institutional, or legal review
- a proof of collaborative-robot certification
- a finished physical system

The right way to read this repo is:

**bounded concept-stage architecture with real code, real tests, real structured artifacts, and explicit evidence limits.**

---

## Repository Structure

### Protocol core
`src/ohip/`

Stable reference-implementation layer for:
- schemas
- consent management
- contact planning
- engagement scheduling
- rest pose generation
- safety gating

### Runtime layer
`src/ohip_runtime/`

Backend-agnostic runtime ownership for:
- interaction session state
- runtime fault models
- coordination requests and decisions
- runtime coordinator
- session store
- configuration wiring
- high-level runtime service

### Interface layer
`src/ohip_interfaces/`

Normalized sensing and execution contracts for:
- signal health and freshness
- force/torque samples
- tactile frames
- proximity frames
- thermal frames
- execution adapter contracts
- simulated execution adapter

### Logging and replay
`src/ohip_logging/`

Structured evidence layer for:
- event records
- JSONL event logs
- event recorder
- replay helpers

### Benchmark layer
`src/ohip_bench/`

Deterministic evaluation layer for:
- benchmark models
- benchmark runner
- built-in scenario catalog
- benchmark reporting

### Supporting assets
- `configs/` — force and culture profile configuration
- `docs/` — spec, state machine, safety, governance, replay, benchmark, and HIL-prep docs
- `examples/` — quickstart reference path
- `sim/` — simulation scene assets
- `tests/` — unit and integration-style repository tests
- `.github/workflows/tests.yml` — CI test workflow

---

## Documentation Map

Start here if you want the repo’s architectural story in order:

1. `docs/spec.md`
2. `docs/state_machine.md`
3. `docs/index.md`
4. `ROADMAP.md`
5. `docs/architecture/runtime_overview.md`
6. `docs/safety/invariants.md`
7. `docs/safety/requirements_traceability.md`
8. `docs/governance/safety_case.md`
9. `docs/benchmarks/overview.md`
10. `docs/replay/event_log_schema.md`
11. `docs/hil/test_rig_architecture.md`

If you only want the high-level direction:
- `ROADMAP.md`
- `docs/governance/standards_crosswalk.md`
- `docs/governance/safety_case.md`

---

## Runtime Flow

At the current repository stage, the main runtime story is:

1. create or load an interaction session
2. submit an explicit interaction request
3. evaluate consent
4. evaluate safety
5. build a bounded planning outcome if allowed
6. record the full structured decision trail
7. optionally submit a bounded execution request
8. record execution status, transitions, faults, retreat, or safe-hold behavior
9. replay or benchmark the resulting event trail later

That flow is represented across:
- `src/ohip_runtime/`
- `src/ohip_logging/`
- `src/ohip_interfaces/`
- `src/ohip_bench/`

---

## Structured Logging and Replay

A major part of this upgrade is that important behavior is no longer supposed to disappear into console output.

Current logging/replay support includes:

- structured event records
- append-friendly JSONL logs
- request/decision/fault/transition/execution event helpers
- replay loading and slicing
- replay filtering by:
  - session
  - request
  - event kind
  - event range

This matters because a safety-first interaction repo should be explainable **after the fact**, not only impressive in the moment.

Relevant files:
- `src/ohip_logging/events.py`
- `src/ohip_logging/jsonl.py`
- `src/ohip_logging/recorder.py`
- `src/ohip_logging/replay.py`

---

## Benchmarking

The repo now includes a deterministic benchmark layer.

Current benchmark support includes:

- explicit scenario definitions
- explicit expectations
- structured observations
- structured benchmark results
- small built-in scenario catalog
- reporting helpers for summaries and pass rates

Current built-in scenarios focus on:
- explicit-consent approval path
- missing-consent denial path
- RED-safety denial path

Relevant files:
- `src/ohip_bench/models.py`
- `src/ohip_bench/runner.py`
- `src/ohip_bench/scenarios.py`
- `src/ohip_bench/reporting.py`

And the reviewer-facing docs:
- `docs/benchmarks/overview.md`
- `docs/benchmarks/scenario_catalog.md`
- `docs/benchmarks/metrics.md`

---

## HIL Preparation

This repo now includes HIL-prep documentation, but not HIL proof.

Current HIL-prep docs define:
- recommended test-rig architecture
- calibration strategy
- fault-injection strategy

These are here so future physical evidence can be:
- bounded
- calibrated
- traceable
- linked back to repo requirements and claims

Relevant docs:
- `docs/hil/test_rig_architecture.md`
- `docs/hil/calibration.md`
- `docs/hil/fault_injection.md`

This is **evidence preparation**, not evidence completion.

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
pip install -e .
```

2. Run tests
```bash
pytest -q
```

3. Run the quickstart smoke path
```bash
python examples/quickstart.py --scene sim/scenes/basic_room.json --verbose
```

4. Inspect the benchmark catalog
```bash
python - <<'PY'
from ohip_bench.scenarios import make_core_catalog
catalog = make_core_catalog()
print([scenario.scenario_id for scenario in catalog])
PY
```

Release Gate

A release should be checked against:

CHANGELOG.md
RELEASE_CHECKLIST.md

That checklist is there to stop the repo from becoming more polished than it is supported.

License

This repository is released under the license terms in LICENSE
.

Do not rely on shorthand descriptions in old summaries. The authoritative licensing terms are the ones in the actual license file.

Author

Bryce Lovell

Final Positioning

The strongest way to understand IX-HapticSight is this:

It is not trying to prove that robots “understand people.”
It is trying to make human-facing approach, contact, retreat, and safe-hold behavior more bounded, testable, replayable, and auditable.

That is a narrower claim.
It is also the more credible one.

