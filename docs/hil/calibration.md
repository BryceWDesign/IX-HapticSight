# HIL Calibration Strategy

This document defines the recommended calibration strategy for future hardware-in-the-loop (HIL) work in IX-HapticSight.

At the current repository stage, this is a **planning and evidence-discipline document**, not proof that any specific sensor or rig has already been calibrated.
Its job is to make future HIL evidence trustworthy by answering:

- what should be calibrated
- how calibration state should be recorded
- how calibration links back to benchmark and HIL artifacts
- what claims calibration does and does not support

Calibration matters because a measured-looking number without calibration discipline is weak evidence.

---

## 1. Purpose

A calibration strategy exists so that future HIL artifacts can answer:

- what sensor produced this measurement
- how that sensor was calibrated
- when it was calibrated
- what uncertainty or drift risk applied
- whether the measurement is trustworthy enough to support a repo claim

Without that chain, HIL artifacts become much easier to doubt.

---

## 2. Calibration Philosophy

IX-HapticSight should treat calibration as part of the evidence chain, not as a side note.

That means:

- a measured value should be traceable to a calibration record
- calibration state should be visible in artifact packaging
- calibration assumptions should be explicit
- stale or missing calibration should narrow claims, not widen them
- software-side event logs should not be presented as physical truth unless the sensing path is calibrated

This is especially important because future HIL evidence may be used to support claims about:

- bounded force behavior
- retreat timing
- thermal threshold detection
- proximity-trigger timing
- tactile contact spread or pressure concentration

---

## 3. What Should Be Calibrated

A future HIL setup for this repo should consider calibration for all measurement sources that materially affect interpretation.

### 3.1 Force and load measurement
Examples:
- load cell
- force/torque sensor
- instrumented contact fixture

Why it matters:
- contact force claims without calibration are weak
- overforce-trigger evidence depends on trustworthy thresholds

---

### 3.2 Thermal sensing
Examples:
- surface thermal sensor
- local thermal probe
- thermal ROI system

Why it matters:
- caution/stop thresholds depend on trustworthy temperature readings
- drift or offset can make safety timing evidence misleading

---

### 3.3 Proximity sensing
Examples:
- short-range proximity ring
- distance sensor array
- near-contact sensor cluster

Why it matters:
- near-contact and corridor-clearance evidence depends on trustworthy distance interpretation

---

### 3.4 Tactile sensing
Examples:
- tactile patch
- pressure-sensitive surface
- distributed contact sensing layer

Why it matters:
- contact area and local pressure claims depend on calibration and sensor repeatability

---

### 3.5 Time alignment
Examples:
- synchronized clocks between runtime log and instrument capture
- trigger channels
- timestamp offset characterization

Why it matters:
- many important future metrics are timing-sensitive
- if event logs and measured traces are not aligned, latency claims weaken quickly

---

## 4. Calibration Is Not One Thing

Calibration should be treated as multiple linked activities:

### 4.1 Initial calibration
The first controlled alignment of a measurement channel against a known reference.

### 4.2 Verification check
A quick check that calibration still appears valid before or after a trial set.

### 4.3 Recalibration
A deliberate recalibration after drift, hardware change, repair, or suspicious results.

### 4.4 Calibration invalidation
The explicit recognition that an earlier calibration may no longer be trustworthy.

This matters because “was calibrated once” is not enough.

---

## 5. Minimum Calibration Record Contents

Each calibration record should eventually include at least:

- calibration record ID
- instrument or sensor ID
- sensor type
- calibration date/time
- operator or automation source
- reference standard or method used
- configuration/fixture context
- key coefficients or offsets
- pass/fail or acceptance result
- known limitations or uncertainty notes
- expiration or review condition if applicable

This does not need to be bloated.
It does need to be explicit.

---

## 6. Recommended Calibration Categories

## 6.1 Force calibration
A force calibration record should ideally capture:

- reference load source or procedure
- measured vs expected values
- offset or bias correction if used
- scale factor if used
- range checked
- repeatability note
- saturation or noise behavior note if relevant

Why:
- force-limit and overforce evidence depend on it

---

## 6.2 Thermal calibration
A thermal calibration record should ideally capture:

- reference temperature source or controlled comparison point
- offset or correction model if used
- range checked
- environment note if relevant
- measurement lag note if relevant

Why:
- threshold and latency interpretations depend on it

---

## 6.3 Proximity calibration
A proximity calibration record should ideally capture:

- known-distance references
- operating range checked
- angle or target-surface caveats
- confidence behavior if used
- detection-dropout notes if relevant

Why:
- near-contact and stop-distance evidence depend on it

---

## 6.4 Tactile calibration
A tactile calibration record should ideally capture:

- sensitivity mapping method
- patch or region mapping notes
- area/pressure conversion assumptions
- known weak zones or dead zones
- repeatability notes

Why:
- contact-pressure and contact-area interpretation depend on it

---

## 6.5 Time alignment calibration
A timing alignment record should ideally capture:

- event-log time source
- instrument time source
- synchronization method
- observed offset
- jitter or uncertainty note
- trigger reference if used

Why:
- latency claims without timing alignment are fragile

---

## 7. Calibration and Repo Claims

Calibration should directly affect how strongly the repo speaks.

### Stronger claim posture
Possible when:
- the relevant sensor is calibrated
- the calibration is recent enough for the trial
- calibration record is linked into the evidence bundle
- measured trace matches the scenario claim

### Narrower claim posture
Required when:
- calibration is missing
- calibration is stale
- drift is suspected
- the measurement source is only approximate
- timing alignment is uncertain

This repo should always prefer the narrower claim when calibration support is weak.

---

## 8. Recommended Artifact Linkage

A future HIL artifact bundle should link every important measured trace to calibration state.

At minimum, a HIL run bundle should eventually include:

- trial ID
- benchmark/scenario ID if applicable
- instrument IDs
- calibration record IDs
- event log path
- measured trace paths
- pass/fail result
- operator note if needed

This allows a reviewer to ask:
“Which calibration record supports this measured curve?”
and get a real answer.

---

## 9. Calibration Freshness

Not all calibration records should be treated as indefinitely trustworthy.

A calibration strategy should define one or more of:

- calibration validity window
- number-of-runs limit before recheck
- drift-triggered invalidation
- hardware-change invalidation
- maintenance-triggered recheck
- pre-run / post-run verification rule

Exact values can be rig-specific later.
The important thing now is the concept:
**calibration freshness matters.**

---

## 10. Pre-Run Verification

Even before a full recalibration is needed, future HIL work should include lightweight pre-run verification where possible.

Examples:
- load-cell zero check
- baseline temperature sanity check
- proximity known-distance check
- tactile idle-state check
- timestamp sync sanity check

Purpose:
- catch obvious drift or setup mistakes before a trial is trusted

This is especially important for a repo that wants measurement-first credibility.

---

## 11. Post-Run Verification

After a trial block, future HIL procedures should consider post-run checks such as:

- force sensor zero drift check
- thermal baseline drift check
- proximity sanity recheck
- timestamp offset spot check

Purpose:
- show whether the run set likely remained within valid calibration bounds
- support later interpretation if something looked wrong

---

## 12. Calibration Failure and Invalidation

A good calibration strategy also defines what to do when calibration cannot be trusted.

Possible invalidation causes:
- failed pre-run check
- obvious zero drift
- damaged fixture
- sensor replacement
- unexplained offset jump
- timing desynchronization
- maintenance change without recalibration

If calibration is invalid, the repo should not silently continue making strong physical claims from those measurements.

At minimum, evidence should be tagged as:
- invalid
- degraded
- review needed
- not suitable for strong quantitative claims

---

## 13. Calibration and Benchmarking

Future HIL-aware benchmarks should eventually incorporate calibration awareness.

Examples:
- benchmark metadata includes calibration record IDs
- certain scenarios require valid calibration to count as strong evidence
- benchmark result quality can be downgraded if calibration freshness is not met

This keeps the benchmark layer honest once physical evidence enters the system.

---

## 14. Calibration and Event Logs

The runtime event log should not try to replace calibration records.
But future event or bundle metadata should reference calibration context where it matters.

Helpful future linkage could include:
- calibration record IDs in evidence bundle manifests
- measurement source IDs in benchmark artifacts
- timing synchronization record references
- sensor mode and trust-level notes

That is stronger than burying calibration in a separate notebook that reviewers never see.

---

## 15. Current Repo Gaps

Before real HIL calibration evidence can exist, the repo still needs:

- calibration record schema or template
- evidence bundle manifest conventions
- instrument ID conventions
- timing-alignment record conventions
- HIL run packaging structure
- actual measured trial data later

This document exists so those future additions have a disciplined frame.

---

## 16. Review Questions

When evaluating a proposed calibration workflow, ask:

1. What instrument is being calibrated?
2. What claim depends on that calibration?
3. What reference or method is used?
4. How is calibration freshness tracked?
5. How will a future reviewer find the calibration record from the HIL artifact?
6. What happens when calibration is invalid or uncertain?

If those answers are weak, the calibration strategy is weak.

---

## 17. Final Rule

A measured trace is only as trustworthy as the calibration chain behind it.

If calibration context is missing, the repo should narrow the claim instead of pretending the number is stronger than it is.
