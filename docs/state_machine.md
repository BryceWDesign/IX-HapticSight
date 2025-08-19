# IX-HapticSight — OHIP State Machine (v0.1)

This document formalizes the **finite-state machine (FSM)** referenced in the spec for safe visual→haptic behavior. It defines:
- States, transitions, guards, and timing
- Safety invariants (must-hold properties)
- Liveness guarantees (system won’t deadlock)
- Edge cases and recovery

See `/docs/spec.md` §5 for the overview.

---

## 1) States

- **IDLE** — Hands at REST; monitoring only.
- **VERIFY** — Awaiting consent/confirmation or extra sensing for **YELLOW** targets.
- **APPROACH** — Motion toward target within safe corridor.
- **PRECONTACT** — Impedance priming, last-moment re-check.
- **CONTACT** — Controlled force profile, dwell timing.
- **RELEASE** — Smooth exit, retract from contact.
- **RETREAT** — Back off after block, timeout, or plan change.
- **EMERGENCY_RETREAT** — Immediate escape after overforce/thermal/current.
- **SAFE_HOLD** — Freeze posture; wait for hazards to clear or operator input.

---

## 2) Diagram (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> VERIFY: nudge(YELLOW)
    IDLE --> APPROACH: nudge(GREEN) & consent
    IDLE --> SAFE_HOLD: hazard(RED)

    VERIFY --> APPROACH: confirmation_ok
    VERIFY --> IDLE: denied | timeout
    VERIFY --> SAFE_HOLD: hazard(RED)

    APPROACH --> PRECONTACT: corridor_ok & recheck_ok
    APPROACH --> RETREAT: veto | plan_change | timeout
    APPROACH --> SAFE_HOLD: hazard(RED)

    PRECONTACT --> CONTACT: impedance_ok & risk_ok
    PRECONTACT --> RETREAT: veto | timeout
    PRECONTACT --> SAFE_HOLD: hazard(RED)

    CONTACT --> RELEASE: dwell_ok
    CONTACT --> EMERGENCY_RETREAT: overforce | overtemp | overcurrent
    CONTACT --> SAFE_HOLD: hazard(RED)

    RELEASE --> IDLE: clear
    RETREAT --> IDLE: rest_reached
    EMERGENCY_RETREAT --> SAFE_HOLD: signal
    SAFE_HOLD --> IDLE: clear
3) Transitions & Guards (Normative)
From → To	Trigger / Guard	Max Latency
IDLE → VERIFY	nudge.level == YELLOW	≤ 50 ms
IDLE → APPROACH	nudge.level == GREEN and consent.is_active()	≤ 50 ms
IDLE → SAFE_HOLD	hazard == RED	≤ 100 ms
VERIFY → APPROACH	confirmation_ok (verbal/gesture/UI/multi-sensor)	≤ 50 ms
VERIFY → IDLE	denied or timeout	≤ 50 ms
VERIFY → SAFE_HOLD	hazard == RED	≤ 100 ms
APPROACH → PRECONTACT	corridor_ok and recheck_ok (risk ≤ thresholds @ ≥20 Hz)	≤ 50 ms
APPROACH → RETREAT	veto (software/hw) or plan_change or timeout	≤ 50 ms
APPROACH → SAFE_HOLD	hazard == RED	≤ 100 ms
PRECONTACT → CONTACT	impedance_ok and risk_ok	≤ 20 ms
PRECONTACT → RETREAT	veto or timeout	≤ 50 ms
PRECONTACT → SAFE_HOLD	hazard == RED	≤ 100 ms
CONTACT → RELEASE	dwell_ok	≤ 20 ms
CONTACT → EMERGENCY_RETREAT	overforce | overtemp | overcurrent (any)	ISR ≤ 10 ms + drive stop ≤ 90 ms
CONTACT → SAFE_HOLD	hazard == RED	≤ 100 ms
RELEASE → IDLE	clear (rest achieved)	≤ 200 ms
RETREAT → IDLE	rest_reached	≤ 200 ms
EMERGENCY_RETREAT → SAFE_HOLD	signal (halt & annunciation)	≤ 100 ms
SAFE_HOLD → IDLE	clear (hazard removed; operator OK if required)	≤ 100 ms

Note: RED→halt path must meet the end-to-end ≤ 100 ms requirement (firmware ISR ≤ 10 ms + stop profile ≤ 90 ms).

4) Safety Invariants (Must-Hold)

Hard-Stop Priority: If any channel reports hazard == RED, motion is halted and future motion is blocked until cleared.

Dual-Channel Veto: Any veto (software OR hardware) cancels current plan; block is edge-latched until operator clear.

Consent Gate: Social touch (e.g., shoulder) requires active consent (explicit or policy) at the moment of PRECONTACT; stale consent is treated as absent.

Envelope Respect: Force/torque/temperature/current never exceed configured limits; exceeding triggers EMERGENCY_RETREAT.

No Hidden Motion: When not in APPROACH/PRECONTACT/CONTACT/RELEASE/RETREAT, controller must maintain REST geometry (hands visible, non-threatening).

Privacy Default: Video logging is off by default; if enabled, face-blur must be applied before persistence/export.

5) Liveness Guarantees

No Deadlock: Every non-terminal state has at least one time-bounded exit (timeout or clear).

Cooldowns Not Blocking Safety: Social cooldown never blocks RETREAT/EMERGENCY_RETREAT/SAFE_HOLD.

Recovery: From SAFE_HOLD, system always has a path to IDLE once hazards clear and latches reset.

6) Timing Budgets (Reference)

Perception→decision (95th percentile): ≤ 60 ms (spec target 20–50 ms).

Safety ISR path: ≤ 10 ms firmware/hw, drive stop ≤ 90 ms.

Contact control loop: 500–1000 Hz local impedance controller.

Risk re-validate cadence during motion: ≥ 20 Hz.

7) Pseudocode (Reference)

state = "IDLE"
while True:
    hazard = read_hazard()
    if hazard == "RED":
        halt_motion()
        state = "SAFE_HOLD"

    if state == "IDLE":
        nudge = get_nudge()
        if nudge and nudge.level == "GREEN" and consent_active_now():
            plan = plan_contact(nudge)
            if plan and veto_clear(plan):
                state = "APPROACH"
            else:
                state = "IDLE"
        elif nudge and nudge.level == "YELLOW":
            request_confirmation()
            state = "VERIFY"

    elif state == "VERIFY":
        if confirmed(): state = "APPROACH"
        elif timed_out() or denied(): state = "IDLE"

    elif state == "APPROACH":
        if !recheck_ok() or veto(): state = "RETREAT"
        elif at_precontact_gate(): state = "PRECONTACT"

    elif state == "PRECONTACT":
        if !risk_ok() or !impedance_ok() or timeout(): state = "RETREAT"
        else: state = "CONTACT"

    elif state == "CONTACT":
        if over_limit(): state = "EMERGENCY_RETREAT"
        elif dwell_ok(): state = "RELEASE"

    elif state == "RELEASE":
        go_to_rest()
        if at_rest(): state = "IDLE"

    elif state == "RETREAT":
        back_off_to_rest()
        if at_rest(): state = "IDLE"

    elif state == "EMERGENCY_RETREAT":
        immediate_escape()
        signal_halt()
        state = "SAFE_HOLD"

    elif state == "SAFE_HOLD":
        freeze_pose()
        if hazards_cleared() and operator_clear(): state = "IDLE"

8) Edge Cases & Resolutions

Consent TTL Expired During APPROACH

Re-check at PRECONTACT; if expired → RETREAT and prompt for reconfirmation.

Sudden Occlusion of Target

recheck_ok fails → RETREAT; re-localize before re-approach.

Sensor Disagreement (e.g., thermal says hot, RGB says safe)

Favor the most conservative sensor (treat as YELLOW/RED); planner must re-route or hold.

Network/Clock Drift

If monotonic clocks disagree beyond 5 ms, safety latches to SAFE_HOLD until resync.

Cooldown vs. Emergency

Cooldowns never inhibit safety motion; only inhibit new social contact nudges.

9) Conformance Checklist

 All RED hazards halt within ≤ 100 ms E2E.

 PRECONTACT verifies consent freshness and risk prior to force ramp.

 CONTACT never exceeds envelope; violations trigger EMERGENCY_RETREAT.

 SAFE_HOLD freezes motion and annunciates status.

 Log entries created for VERIFY→APPROACH, CONTACT start/end, veto, emergency, and hold.

10) Versioning

FSM v0.1 corresponds to /docs/spec.md v0.1 and /src/ohip/* APIs OHIP_SCHEMAS_VERSION == v0.1.0.

Breaking changes to states/transitions bump minor version.
