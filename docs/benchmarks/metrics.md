# Benchmark Metrics

This document defines the current and planned metric vocabulary for IX-HapticSight benchmarks.

The purpose of this document is to make benchmark numbers interpretable.
A benchmark metric is only useful if a reviewer can answer:

- what the metric measures
- how it is counted
- what layer produced it
- what the metric does **not** prove

At the current repository stage, the benchmark layer is still mostly software-path and evidence-structure oriented.
That means the current metrics are strongest for:

- decision-path correctness
- execution-path acceptance or denial
- structured event emission
- timing of repository-side handling

The repo is **not** yet at a stage where physical contact quality, force-control quality, or real hardware timing claims should be made from benchmark numbers alone.

---

## 1. Purpose

The benchmark metric system exists to support:

- deterministic comparisons across repo changes
- clearer PASS/FAIL reasoning
- structured evidence summaries
- later CI-style regression checks
- future expansion into replay and HIL metrics

The benchmark system should prefer a small number of explicit, stable metrics over a large number of vague ones.

---

## 2. Metric Philosophy

IX-HapticSight metrics should follow these rules:

1. **Explicit definition**
   - every metric should say exactly what is counted

2. **Stable meaning**
   - metric names should not silently change meaning across versions

3. **Repository honesty**
   - a metric should not imply physical evidence that the current repo does not actually have

4. **Layer clarity**
   - it should be clear whether a metric comes from:
     - decision logic
     - execution adapter behavior
     - logging/replay
     - benchmark harness
     - future HIL data

5. **No “safety score” theater**
   - broad vanity scores are weaker than explicit measurements

---

## 3. Current Implemented Metrics

At the current repository stage, the benchmark runner emits these built-in metrics:

### `event_count`
**Unit:** `count`

**Definition:**  
The number of structured events buffered by the event recorder during one benchmark scenario.

**Produced by:**  
- `src/ohip_bench/runner.py`
- `src/ohip_logging/recorder.py`

**What it is useful for:**  
- checking that scenarios are producing a structured event trail
- detecting drift in event emission patterns
- providing a simple signal that logging did or did not occur

**What it does not prove:**  
- log completeness in a formal sense
- causal correctness of every event
- hardware truth
- physical safety

---

### `decision_duration_ms`
**Unit:** `ms`

**Definition:**  
Wall-clock elapsed time spent by the runtime service while handling one benchmark request inside the benchmark runner.

**Produced by:**  
- `src/ohip_bench/runner.py`

**What it is useful for:**  
- comparing repository-side processing changes
- identifying obvious regressions in benchmark-path runtime handling
- measuring coarse software-path timing changes

**What it does not prove:**  
- real-time guarantees
- middleware latency
- actuator latency
- physical stop time
- human-safe timing bounds

This is a repository-side timing metric, not a deployment safety timing metric.

---

## 4. Current Observed Fields That Behave Like Metrics

Some structured observation fields are not emitted as standalone numeric metrics yet, but they already function like benchmark evidence fields.

These include:

### `observed_status`
Examples:
- `APPROVED`
- `DENIED`
- `REQUIRES_VERIFICATION`
- `ERROR`

This is a categorical outcome field, not a numeric metric, but it is still central to benchmark evaluation.

---

### `observed_executable`
Examples:
- `True`
- `False`

This distinguishes:
- approved and executable
from
- approved but not executable
or
- denied

Again, not numeric, but extremely important.

---

### `observed_fault_reason`
Examples:
- `consent_missing_or_invalid`
- `session_safety_red`

This is a categorical evidence field rather than a numeric metric.
It helps detect whether the repo denied or faulted for the **right reason** rather than merely denying in general.

---

### `observed_execution_status`
Examples:
- `ACCEPTED`
- `REJECTED`
- `ABORTED`
- `SAFE_HOLD`

This is also categorical evidence rather than numeric measurement.

---

## 5. Why Current Metrics Are Intentionally Narrow

At this repo stage, narrow metrics are better than inflated metrics.

Why:
- the repo is still mostly benchmarking logic paths and structured evidence paths
- there is no HIL measurement layer yet
- there is no real actuator timing or real contact measurement integrated into benchmark results yet
- pretending otherwise would be fiction data

So the current metric layer is intentionally modest.

That is a strength, not a weakness.

---

## 6. Recommended Near-Term Metrics

The next wave of metrics should grow carefully from the current benchmark and runtime layers.

### 6.1 Decision-path metrics
These are still software-side metrics, but valuable.

#### `decision_status_match`
**Type:** boolean or categorical  
**Meaning:** whether observed decision status matched expectation

#### `execution_status_match`
**Type:** boolean or categorical  
**Meaning:** whether observed execution status matched expectation

#### `fault_reason_match`
**Type:** boolean or categorical  
**Meaning:** whether the observed fault reason matched expectation

These could remain implicit through PASS/FAIL logic, but exposing them directly would strengthen reporting.

---

### 6.2 Logging-path metrics
These would tighten evidence quality.

#### `state_transition_event_count`
How many transition events were emitted

#### `fault_event_count`
How many structured fault events were emitted

#### `execution_status_event_count`
How many execution-status events were emitted

#### `event_order_valid`
Whether the event sequence satisfies expected ordering constraints

These would be especially useful once replay-integrity benchmarks are added.

---

### 6.3 Replay-path metrics
Once replay-integrity benchmarks exist, useful metrics include:

#### `replay_event_count_match`
Whether replayed event count matched source event count

#### `replay_first_event_match`
Whether first replayed event matched source first event

#### `replay_last_event_match`
Whether last replayed event matched source last event

#### `replay_order_integrity`
Whether replay preserved event ordering

These would strengthen the evidence story around reproducibility.

---

### 6.4 Execution-path metrics
Once the simulated execution adapter is benchmarked more explicitly, useful metrics include:

#### `execution_acceptance_rate`
Fraction of scenarios whose execution requests were accepted

#### `abort_path_success_rate`
Fraction of abort scenarios that reached the expected execution state

#### `safe_hold_path_success_rate`
Fraction of safe-hold scenarios that reached the expected execution state

#### `execution_progress_terminal_consistency`
Whether terminal execution states behave consistently across scenarios

These are still software-path metrics unless backed by real runtime measurements.

---

## 7. Future HIL Metrics

This is where the metric system becomes much more serious.

Once HIL scaffolding is connected to actual measurements, the benchmark/evidence layer should eventually support metrics like:

### 7.1 Contact metrics
- peak measured force
- dwell duration
- contact onset latency
- contact release latency
- contact-zone localization error

### 7.2 Retreat metrics
- retreat start latency
- retreat completion time
- retreat failure rate
- safe-hold fallback rate

### 7.3 Fault metrics
- overforce detection latency
- thermal threshold trigger latency
- watchdog-trigger latency
- fault-to-hold transition latency

### 7.4 Logging/evidence metrics
- evidence bundle completeness
- missing-event rate
- traceability coverage ratio

These would be strong metrics **only if backed by actual instrumentation**, not simulation theater.

---

## 8. Metric Naming Rules

Metric names should aim to be:

- concise
- literal
- stable
- not marketing language

Good:
- `event_count`
- `decision_duration_ms`
- `fault_event_count`

Bad:
- `interaction_quality_score`
- `trust_index`
- `safety_rating`

Those broad names hide too much and suggest more evidence than the repo has.

---

## 9. Metric Units

Units should always be explicit where applicable.

Common units for this repo include:

- `count`
- `ms`
- `s`
- `N`
- `Nm`
- `kPa`
- `mm`
- `C`

If a metric has no natural physical unit, it should either:
- be categorical, or
- be clearly unitless

---

## 10. Relationship to PASS/FAIL

PASS/FAIL is not a metric.
It is an outcome.

Metrics support the reasoning behind PASS/FAIL.

Example:
- PASS because:
  - expected status matched
  - expected execution status matched
  - event count was present
  - no unexpected fault reason occurred

The repo should not collapse all evidence into one pass/fail badge and call it a day.

---

## 11. Current Metric Gaps

Important current gaps include:

- no explicit event-order metrics
- no explicit replay-integrity metrics
- no dedicated safe-hold or abort benchmark metrics
- no force/thermal/proximity/tactile physical metrics in benchmark outputs
- no HIL metrics yet
- no benchmark artifact manifest completeness metric yet

These gaps should remain visible.

---

## 12. Review Questions

When adding a new metric, reviewers should ask:

1. What exactly does this metric measure?
2. What layer produced it?
3. Does the metric imply more evidence than the repo actually has?
4. Is the metric stable enough to compare across runs?
5. Is the metric useful for a real reviewer, or just decorative?

If those answers are weak, the metric is weak.

---

## 13. Final Rule

A benchmark metric should reduce ambiguity, not create it.

If a number sounds impressive but cannot be tied to a precise definition and an actual evidence source, it should not be in this repo.
