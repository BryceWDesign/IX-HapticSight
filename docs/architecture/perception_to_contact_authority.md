# Perception-to-Contact Safety Authority

The v0.2 architecture separates four forms of authority that are often accidentally mixed together in robot prototypes.

1. **Perception authority:** a model may estimate what is present.
2. **Task authority:** a planner or LLM may propose what the robot should attempt.
3. **Safety authority:** deterministic logic independently decides what physical authority may be granted.
4. **Execution authority:** a controller may execute only inside the granted force, speed, state, and timeout envelope.

No layer is allowed to silently inherit a stronger authority from the layer above it.

## Perception quorum

Two independently trained reference models can inspect the same RGB-D frame. The quorum computes total agreement, critical-class disagreement, mean confidence, and uncertainty. Human, hot, liquid, and sharp disagreements are treated more strictly than ordinary background disagreement.

The reference models are intentionally simple. The design point is the *quorum boundary*, not a claim that the supplied synthetic-calibration models are production vision.

## Safety authority

The independent authority emits one of three dispositions:

- `ALLOW`: request already fits the current measured envelope.
- `MODIFY`: action may proceed only after force and/or speed is reduced.
- `DENY`: no physical authority is granted.

The authority also emits a bounded counterfactual, for example that separation must increase, confidence must improve, or consent must be reacquired.

## Cycle invariants

After a decision is granted, the runtime still re-checks invariants every cycle. Permission is not permanent. Consent loss, stale sensors, unexpected measured force, perception disagreement, E-stop, or watchdog failure can terminate authority after motion has begun.

## Recovery

Recovery is explicit rather than left to learned policy behavior:

- zero effort when already in problematic contact;
- retract when safe motion away from the hazard is available;
- safe hold when uncertainty or timing prevents a trustworthy retreat;
- operator required for latched faults or E-stop.

## Evidence

Decisions and runtime transitions can be recorded into a SHA-256 evidence chain. The hash chain does not prove the physical truth of a sensor measurement, but it can detect later modification of recorded evidence.
