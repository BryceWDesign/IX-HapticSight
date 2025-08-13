# IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)

**Status:** Public specification (reference implementation WIP)  
**Author:** Bryce Wooster 
**Purpose:** Define a safety-first interface that transforms visual recognition into instinctive, human-safe touch behaviors for robots, XR agents, and other physical AI systems.

---

## Overview

**IX-HapticSight** is a specification and reference framework for mapping computer vision inputs to safe, human-aware haptic actions.

It is designed to ensure that robots and XR agents:
- Maintain non-threatening resting postures.
- Proactively avoid hazards using visual danger mapping.
- Initiate culturally safe and consent-aware contact in appropriate contexts.
- Log all interactions for transparency and auditing.

---

## Core Features

### **1. Rest State Markers**
- Fingertip visual targets in the field of view (FOV) indicating “safe rest” positions when idle.  
- Prevents aimless or potentially threatening hand movements.

### **2. Engagement Nudges**
- Context-driven prompts to interact with **safe** objects, surfaces, or human touchpoints (e.g., a shoulder for emotional support).  
- Prioritized based on object safety classification (green/yellow/red) and human emotional cues.

### **3. Visual Danger Mapping**
- Green: Safe contact.  
- Yellow: Requires verification or confirmation.  
- Red: Contact prohibited — reroute or halt motion.

### **4. Social-Touch Protocol**
- Focus on non-invasive, supportive gestures (e.g., shoulder contact with limited force and dwell time).  
- Explicit consent required unless in configured caregiver/medical override modes.  
- Cultural sensitivity profiles available.

---

## Why This Matters

In human-robot interaction, *how* and *when* contact occurs can make the difference between safe, trusted systems and unsafe, rejected ones.

IX-HapticSight offers:
- **Predictable, transparent touch behavior**  
- **Hard-coded safety layers** on top of learned policies  
- **A clear, extensible protocol** for integration into any robot control stack

---

## Architecture Snapshot

Perception → Semantic Segmentation → Safety Map → Affordance Classifier
| | | |
└────────────┬───────┴──────────────┬─────┴───────────────┬───┘
v v v
Human State Risk Assessor Surface Planner
| | |
└──────────┬───────────┴───────────┬──────────┘
v v
Engagement Scheduler Rest Pose Generator
| |
v v
Contact Planner ←→ Force/Impedance Controller
|
v
Motion Exec (with dual-channel safety veto)


---

## Safety & Compliance

- Dual independent safety paths (software + hardware E-stop).  
- ISO 10218 / ISO 15066 inspired force limits for collaborative robots.  
- Continuous interaction logging.  
- Privacy-by-design for human data.

---

## Getting Started

**/docs/spec.md** — Full semantics, state machines, and timing budgets (coming soon)  
**/src/** — Reference stubs for vision, safety mapping, engagement scheduling, and motion planning (coming soon)

---

## License

Released under the MIT License with a **Responsible Use Addendum** prohibiting weaponization, coercion, or unsafe deployment. See [`LICENSE`](LICENSE) for full terms.

---

## Background

IX-HapticSight originated from discussions on how physical AI systems could interact naturally, safely, and supportively with humans.  
The design draws inspiration from advances in AI models such as **OpenAI’s GPT-5**, particularly in affect recognition and context-driven behavior planning.

> *Side note:* Conceived and documented as a personal gesture to mark GPT-5’s “birthday” — a subtle nod to the collaboration between human insight and AI inspiration that made this specification possible.

---

## Credits

- **Primary Author:** Bryce Wooster 
- **Acknowledgment:** Inspired in part by advances in AI from OpenAI’s GPT-5. No endorsement or co-authorship implied.
