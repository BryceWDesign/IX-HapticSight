# Benchmark Overview

This document defines the benchmark philosophy and current benchmark architecture for IX-HapticSight.

The benchmark layer exists to turn repository claims into repeatable scenario checks.
It is not a certification artifact.
It is not real-world deployment proof.
It is a structured way to ask:

- what scenario was tested
- what outcome was expected
- what outcome was observed
- what metrics were recorded
- whether the result matched the expectation

That is the minimum discipline required for a serious interaction-governance repo.

---

## 1. Purpose

The benchmark system exists to support:

- deterministic regression checks
- explicit scenario-based evaluation
- structured result comparison across repo changes
- replay-friendly evidence generation
- clearer separation between claims and measured repository behavior

The benchmark layer is intended to answer:
“Did the current repo behave the way the repo says it should?”

That is narrower than asking whether a deployed robot is safe in the real world.

---

## 2. Benchmark Philosophy

IX-HapticSight benchmarks should follow these rules:

1. **Scenario first**
   - every run starts from an explicit scenario definition
   - no hidden assumptions
   - no mystery runtime conditions

2. **Expectation first**
   - each scenario declares what should happen
   - approval, denial, fault behavior, and execution behavior should be explicit

3. **Structured observation**
   - results should be collected as machine-readable observation records
   - event counts and execution outcomes should not depend on casual console reading

4. **Determinism over theater**
   - benchmark value comes from repeatability, not dramatic demos

5. **Repository truth, not hype**
   - benchmark results are evidence about the repo’s current behavior
   - they are not blanket safety guarantees

---

## 3. Current Benchmark Components

The current benchmark layer includes:

### Core models
- `src/ohip_bench/models.py`
  - scenario, expectation, observation, metric, and result structures

### Runner
- `src/ohip_bench/runner.py`
  - deterministic scenario execution against a fresh runtime service

### Built-in scenarios
- `src/ohip_bench/scenarios.py`
  - current catalog of consent and safety scenarios

### Reporting
- `src/ohip_bench/reporting.py`
  - result summarization and export helpers

### Related runtime dependencies
- `src/ohip_runtime/runtime_service.py`
- `src/ohip_logging/`
- `src/ohip_interfaces/`
- `src/ohip/`

The benchmark layer does not stand alone.
It evaluates the integrated behavior of those layers.

---

## 4. Current Benchmark Domains

The benchmark model supports these domains:

- `CONSENT`
- `SAFETY`
- `PLANNING`
- `EXECUTION`
- `LOGGING`
- `REPLAY`
- `INTEGRATION`

At the current repository stage, the strongest implemented coverage is in:

- consent-path evaluation
- safety-path denial behavior
- runtime integration behavior through the service layer

Future versions should increase coverage for:
- execution fault behavior
- replay integrity
- logging completeness
- HIL evidence ingestion
- state-transition invariants

---

## 5. Current Scenario Flow

A typical benchmark run currently works like this:

1. build a fresh runtime service
2. create a fresh interaction session from scenario inputs
3. optionally apply explicit consent based on scenario inputs
4. construct a runtime request and optional nudge
5. execute the runtime request
6. collect:
   - decision outcome
   - execution response if present
   - active fault reason if present
   - structured event count
   - timing metrics
7. compare observed output against the scenario expectation
8. emit a structured benchmark result

This is intentionally boring.
That is a strength.

---

## 6. What a Benchmark Scenario Contains

A benchmark scenario currently contains:

- `scenario_id`
- `title`
- `domain`
- `description`
- `inputs`
- `expectation`
- `tags`

The expectation may include:
- expected decision status
- expected executable flag
- expected fault reason
- expected execution status

This means the benchmark system can distinguish:
- “approved but not executable”
- “denied with the wrong reason”
- “approved but wrong execution backend response”

That is already more useful than vague pass/fail prose.

---

## 7. What a Benchmark Result Contains

A benchmark result currently contains:

- scenario ID
- domain
- outcome (`PASS`, `FAIL`, `ERROR`, `SKIPPED`)
- structured observation
- structured metrics
- reason code
- start and finish times
- derived duration

A structured observation may include:
- observed decision status
- observed executable flag
- observed fault reason
- observed execution status
- event count

This gives the repository a baseline evidence spine.

---

## 8. Current Limitations

The benchmark layer is useful, but it is still early-stage.

Current limitations include:

- scenarios are still relatively small in number
- there is no hardware-in-the-loop path yet
- there is no real robot backend under test
- most metrics are currently high-level, not physical
- benchmark scenarios still emphasize logic-path correctness over physical execution truth
- there is not yet a persistent benchmark artifact manifest system

That is acceptable as long as the repo stays honest about it.

---

## 9. What Current Benchmarks Do Prove

Current benchmarks can help prove things such as:

- a consent path allows or blocks contact as expected
- a safety-red session blocks execution as expected
- runtime service emits a structured event trail
- execution adapter behavior is accepted, rejected, or faulted as expected
- scenario expectations are compared in a repeatable way

That is meaningful repository evidence.

---

## 10. What Current Benchmarks Do Not Prove

Current benchmarks do **not** prove:

- real-world physical safety
- human comfort or acceptance
- force quality under real hardware contact
- certified collaborative behavior
- hardware watchdog latency
- thermal dissipation safety in physical deployment
- regulatory compliance
- medical or therapeutic suitability

Those require stronger evidence classes later.

---

## 11. Relationship to Replay

The benchmark system is designed to align with the structured logging and replay layer.

This matters because a serious benchmark should be:

- re-runnable
- reviewable
- inspectable after the fact

The replay layer supports that by preserving structured event trails that can later be:
- compared
- reloaded
- grouped
- inspected by session, request, and event kind

Benchmarking without replay is weaker.
Replay without scenario expectations is also weaker.
They are stronger together.

---

## 12. Relationship to HIL

The current benchmark layer is software-first.

The next major maturity step is to connect it to HIL-style evidence, where scenarios may eventually include:

- calibrated load-cell data
- overforce timing checks
- retreat timing measurements
- backend fault injection records
- thermal trip behavior
- stop/hold timing results

That is not implemented yet, but the current benchmark structure is intentionally shaped so that future evidence can be added without rewriting the whole system.

---

## 13. Benchmark Outcome Semantics

### PASS
Observed behavior matched the explicit expectation.

### FAIL
Scenario executed, but observed behavior did not match the expectation.

### ERROR
The benchmark itself could not run correctly because of malformed input or a runner/runtime issue.

### SKIPPED
Scenario was intentionally not executed.

These distinctions matter.
A FAIL says the repo behavior diverged from expectation.
An ERROR says the benchmark setup or execution path itself was broken.

---

## 14. Reporting Direction

The reporting layer currently supports:

- aggregate counts
- per-domain grouping
- per-outcome grouping
- pass-rate summaries
- export-friendly dictionaries

That is enough for local inspection and future CI-style checks.

Later reporting could add:
- baseline-vs-head comparisons
- event-count drift alerts
- trend snapshots
- benchmark artifact manifests

---

## 15. Review Questions

When adding a new benchmark, reviewers should ask:

1. Is the scenario explicit?
2. Is the expectation explicit?
3. Does the scenario measure something real about the repository?
4. Is the result structured and reproducible?
5. Is the benchmark claiming more than it actually tests?
6. Can the output be replayed or reviewed later?

If those answers are weak, the benchmark is probably weak too.

---

## 16. Near-Term Priorities

The highest-value next benchmark improvements are:

1. expand the built-in scenario catalog
2. add replay-integrity benchmarks
3. add event-log completeness benchmarks
4. add execution-fault and safe-hold benchmark cases
5. add state-transition expectation benchmarks
6. prepare HIL-compatible evidence bundle conventions

---

## 17. Final Rule

A benchmark is only valuable if it narrows uncertainty.

If it cannot tell a reviewer what happened, why it mattered, and whether it matched the stated expectation, it is just decoration.
