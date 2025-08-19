# IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP) Specification
**Version:** v0.1 (2025-08-08)  
**Author:** Bryce  
**Scope:** Safety-first mapping from visual perception → human-aware touch behaviors for robots/XR agents.  
**License:** MIT + Responsible Use Addendum (see `/LICENSE`). This spec is normative for “OHIP v0.1”.

---

## 1. Purpose & Non-Goals
**Purpose.** Define a minimal, deterministic interface that turns multi-modal perception into safe, predictable, human-centred haptic actions (rest, approach, contact, retreat), with dual safety interlocks and auditable logs.

**Non-Goals.**
- Emotional simulation, “expressiveness,” or non-functional theatrics.
- Weaponized, coercive, or unsafe deployments (prohibited by license).
- Binding to a single middleware stack (ROS2/LCM/etc. are implementation choices).

---

## 2. Key Terms (Normative)
- **Rest Marker** — A 3D target pose for each fingertip/palm indicating non-threatening idle position(s) rendered to operator/HUD and respected by the controller when idle.
- **Engagement Nudge** — A prioritized suggestion (vector + rationale) to interact with a **GREEN** entity given consent/safety.
- **Safety Map** — Scene-aligned hazards/constraints with tri-level semantics: **GREEN** (safe), **YELLOW** (verify), **RED** (prohibited).
- **Social-Touch Protocol** — Parameterized gestures considered culturally safe by default (e.g., light shoulder contact), governed by consent policy.
- **Dual-Channel Veto** — Contact executes only if **(A)** software safety passes **and** **(B)** independent hardware/firmware limits are within bounds. Either may veto.
- **Consent** — Explicit (verbal/gesture UI) or policy-driven (clinician/caregiver profiles) authorization to touch. No consent ⇒ no contact (except emergency extraction as policy-defined).

---

## 3. System Architecture (Reference)
Perception → Segmentation → Safety Map → Affordance → Human State/Affect
| | | | |
└───────┬────┴───────┬─────┴──────┬────┴──────────┬─────┘
v v v v
Risk Assessor Surface Planner Consent Manager Logger
\ | /
\ | /
└────── Engagement Scheduler ──────┐
v
Rest Pose Generator | Contact Planner
\ | /
\ | /
└── Dual-Channel Veto ─→ Motion Exec

**Perception Inputs (configurable):**  

RGB; Depth (stereo/ToF); IR/Thermal; Event camera (optional); Tactile arrays; Current/torque; Microphone (keyword/consent only); Proximity; IMU.

---

## 4. Safety Semantics (Tri-Level)
- **GREEN (Safe):** Contact allowed within configured force/torque/temperature/current envelopes.  
- **YELLOW (Verify):** Additional check required (explicit consent, multi-sensor confirmation, or operator OK).  
- **RED (Prohibited):** Contact and traversal blocked. Planner must re-route or halt.

**Normative Rule:** Any **RED** voxel/region intersecting the planned approach or contact normal MUST abort execution and command an immediate retreat.

---

## 5. State Machine (Normative)

[IDLE]
| on nudge(GREEN) & consent -> APPROACH
| on nudge(YELLOW) -> VERIFY
| on hazard(RED) -> SAFE_HOLD

[VERIFY]
| if confirmation -> APPROACH
| else -> IDLE

[APPROACH]
| pre-contact checks (risk ≤ thresh) -> PRECONTACT
| hazard(RED) or veto -> RETREAT

[PRECONTACT]
| impedance priming -> CONTACT
| timeout -> RETREAT

[CONTACT]
| dwell(T_dwell) within force profile -> RELEASE
| overforce/thermal/current -> EMERGENCY_RETREAT

[RELEASE]
| complete -> IDLE (via REST)

[RETREAT]
| path clear -> IDLE (via REST)

[EMERGENCY_RETREAT]
| notify -> SAFE_HOLD -> IDLE (manual/auto per policy)

[SAFE_HOLD]
| freeze motion, hands to REST, status signal -> IDLE when clear

**Timing Guards (defaults; tune per hardware & HIL tests):**
- Hazard-to-halt (RED trip → stop): **≤ 100 ms**
- Planned contact re-validate cadence: **≥ 20 Hz**
- Contact loop (impedance control): **500–1000 Hz** (controller domain)
- Vision loop (seg/affordance): **≥ 30 FPS** (end-to-end ≤ 50 ms)

---

## 6. Timing Budget (Target, on mid-range edge GPU)
- Frame capture + sync: 2–6 ms  
- Segmentation (fp16): 8–18 ms  
- Affordance classifier: 2–6 ms  
- Human state/affect: 4–10 ms  
- Risk assessor + map fuse: 2–5 ms  
- Scheduler + policy: 0.5–2 ms  
- Contact planning microcycle: 1–4 ms  
**Total perception→decision E2E:** ~20–50 ms (95th percentile ≤ 60 ms).  
**Safety ISR path (RED → halt):** firmware/hardware path ≤ 10 ms + drive stop ≤ 90 ms.

---

## 7. Social-Touch Protocol v0.1 (Default Parameters)
**Gesture:** Lateral shoulder contact (proximal deltoid region).  
**Approach:** From visible arc, palm open, velocity ≤ 0.15 m/s within last 15 cm.  
**Force Profile (example defaults, tune in HIL):** peak 1.0 N (clamped), slope-limited; normal impedance target 0.3–0.6 N/mm; dwell 1.0–3.0 s; smooth in/out 250–400 ms.  
**Announcements:** “May I place my hand on your shoulder for support?” (verbal/light cue). No response ⇒ no contact, unless policy profile grants caregiver/clinical override.  
**Never:** Face, hair, hands, torso contact without explicit contemporaneous consent.  
**Cultural Profiles:** YAML tables adjust default gestures/thresholds per locale.

> **Note:** Values above are conservative starting points and MUST be verified against hardware end-effector, skin compliance, and institutional policy before live trials.

---

## 8. Rest Markers (Geometry)
- **Hands visible** below chest, palms readable, elbows in.  
- **Fingertip 3D targets** relative to body frame `B`:  
  - `index_tip`: `[+0.18, +0.12, +0.85] m`  
  - `middle_tip`: `[+0.17, +0.10, +0.85] m`  
  - `ring_tip`:  `[+0.16, +0.08, +0.85] m`  
  - `little_tip`:`[+0.15, +0.06, +0.85] m`  
  - mirrored for opposite hand; yaw outward ≤ 10°.  
- Renderer/HUD MUST display rest targets in FOV; controller returns to rest within **500–800 ms** of losing nudge/consent.

---

## 9. Engagement Scheduler (Policy Logic)
**Inputs:** `human_state`, `affordances`, `risk_map`, `consent`, `task_queue`, `cooldowns`.  
**Outputs:** `nudge = {level, target_pose, contact_normal, rationale, priority}`.

**Priority Heuristics (suggested):**
1. Safety > Consent > Task goal > Efficiency.  
2. Prefer GREEN items with social utility (support, handoff).  
3. Debounce identical nudges within 2–5 s; avoid “nagging”.  
4. Cooldown after any human contact: **≥ 10 s** (unless explicitly re-invited).

**Example JSON (nudge):**
```json
{
  "level": "GREEN",
  "target": {"frame":"W","xyz":[0.42, -0.18, 1.36],"rpy":[0,0,1.57]},
  "normal": [0.0, 0.8, 0.6],
  "rationale": "Shoulder support (distress cues + consent=yes)",
  "priority": 0.82,
  "expires_in_ms": 1200
}
10. Safety Interlocks (Dual Channel)

Software Path: risk gate, thermal/current monitor, joint/EE force limits, approach corridor validator.

Hardware/Firmware Path: independent current/torque clamp, thermal cutoff, E-stop chain, watchdog (≤ 10 ms ISR).

Veto Contract: Either channel may block; blocks are edge-latched until operator clears.

11. Data Schemas (Canonical)

Consent Record
{
  "subject_id":"anon-7f3e",
  "mode":"explicit|policy|none",
  "source":"verbal|gesture|ui|profile",
  "timestamp":"2025-08-08T23:17:00Z",
  "scope":["shoulder_contact"],
  "ttl_s":60
}

Safety Map Tile
{"cell":[i,j,k],"class":"fire|blade|hot|moving|liquid|unknown","level":"GREEN|YELLOW|RED","updated_ms":62}

Contact Execution Log (PII-minimized)
{
  "event":"contact",
  "target":"shoulder",
  "force_peak_N":0.92,
  "dwell_ms":1320,
  "consent_mode":"explicit",
  "veto_triggered":false,
  "hash_video":"sha256:…", 
  "faces_blurred":true
}

12. Interfaces (Implementation-Agnostic)

Transport: ROS2/LCM/ZeroMQ acceptable. Messages SHOULD mirror schemas above.

Rates: Perception topics ≥ 30 Hz; safety status ≥ 100 Hz; control ≥ 500 Hz (local loop).

Clock: Monotonic source; all logs timestamped; drift budget ≤ 5 ms between nodes.

13. Testing Strategy

Simulation (required before HIL):

Scenes: flat surface, cup handoff, warm kettle (YELLOW), space heater (RED), human mannequin with affect cues.

Asserts: nudge correctness, veto on RED, cooldown adherence, latency budgets.

Hardware-in-the-Loop (HIL):

Force verification with calibrated load cell on dummy shoulder; overforce → EMERGENCY_RETREAT within ≤ 60 ms from threshold crossing.

Thermal/current trips using instrumented end-effector.

E-stop: chain integrity, ISR latency, recovery ritual.

Red-Team Safety:

Adversarial scenes (reflective surfaces, occlusions, sudden motion).

Privacy checks: PII never written unless explicitly enabled; face-blur pipeline validated.

14. Compliance & Policy Mapping (Guidance)

ISO 10218 / ISO/TS 15066: Use their collaborative force/pressure guidance to set limits; document HIL derivation.

Facility Policy: Clinical/caregiver overrides require signed institutional profile configs.

Privacy: Default logging = technical metrics only; video logs off by default; opt-in with face-blur.

15. Learning Boundaries

Learned policies MAY tune within envelopes (approach speed, path smoothing, micro-pose).

Learned policies MUST NOT change hard limits, consent rules, or safety semantics without a signed release and re-certification test run.

16. Configuration Files (Examples)

/configs/force_limits.yaml
end_effector:
  max_force_N: 1.2
  max_torque_Nm: 0.15
  approach_speed_mps: 0.15
  release_speed_mps: 0.2
  impedance:
    normal_N_per_mm: [0.3, 0.6]
    tangential_N_per_mm: [0.1, 0.3]
safety:
  red_stop_ms: 100
  revalidate_hz: 20

/configs/culture_profiles.yaml
default:
  allow_shoulder: true
  announce_verbal: true
  cooldown_s: 10
  prohibited_regions: [face, hair, hands, torso]
jp:
  allow_bow_gesture: true
  allow_shoulder: true
  announce_verbal: true
  cooldown_s: 12

17. Reference API (Pseudocode)
frame = camera.read()
semantic = segmentor(frame, depth=depth)
risk = risk_fuser(semantic, thermal=ir, motion=flow)
human = human_state(frame)
consent = consent_mgr.query(human, ui=ui_state)

rest = rest_pose(robot_kin, scene=semantic)

nudge = scheduler.decide(human, consent, affordances(frame, depth),
                         risk, policy=profile)

if nudge.level == "GREEN" and dual_veto.software_ok(nudge, risk):
    plan = contact_planner(nudge, limits, impedance_profile)
    if dual_veto.hardware_ok(plan):
        motion.exec(plan)
    else:
        motion.to_rest(rest)
else:
    motion.to_rest(rest)
18. Roadmap

v0.2: Full state machine tests, formal safety proofs (invariants), CI sim scenes

v0.3: Culture/consent UX kit, multi-modal consent (gesture/GUI)

v1.0: Hardware-certified reference stack + safety case package

19. Notes

This specification is part of the IX-HapticSight project. It was originally conceived during discussions on safe, human-supportive AI interaction. Inspiration includes contemporary advances in AI modeling. See README for background.
