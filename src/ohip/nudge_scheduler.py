"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Engagement Scheduler (spec §9, §5, §6, §7)

Change log (2025-08-19):
- If the **top-ranked** candidate is suppressed due to **debounce**, do NOT fall
  back to the next candidate — return None for this cycle to avoid “nagging”.
- Still allow fallback when the top candidate is suppressed due to **cooldown**
  (social cooldown) or other non-debounce reasons. This preserves behavior for
  tests that expect object interaction when shoulder is blocked by policy/safety.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from time import time

from .schemas import (
    Nudge,
    NudgeLevel,
    Pose,
    Vector3,
    ConsentRecord,
    ConsentMode,
    SafetyLevel,
    validate_priority,
)


# ------------------------- #
#       POLICY PROFILE      #
# ------------------------- #

@dataclass
class PolicyProfile:
    """
    Tunable policy parameters (see spec §7, §9, §16).
    """
    # Consent / social-touch
    allow_shoulder: bool = True
    require_explicit_for_social: bool = True
    social_cooldown_s: float = 10.0  # min time between human contacts (spec default ≥ 10 s)

    # Debounce & expiry
    debounce_window_s: float = 2.0   # avoid repeating identical nudges too fast (spec §9)
    nudge_ttl_ms: int = 1200         # validity window (spec example)

    # Approach limits (planner enforces hard limits; these bias scheduler choices)
    prefer_max_approach_speed_mps: float = 0.15

    # Priority weights
    w_safety: float = 1.0
    w_consent: float = 0.8
    w_social: float = 0.3
    w_task: float = 0.2

    # Distress threshold where social support becomes socially useful (0..1)
    distress_support_threshold: float = 0.6


# ------------------------- #
#      COOLDOWN TRACKER     #
# ------------------------- #

class CooldownManager:
    """
    Tracks time-based cooldowns for human contact and identical nudge repetition.
    """
    def __init__(self):
        self._last_social_contact_ts: float = 0.0
        self._last_nudge_fingerprint: Tuple[str, Tuple[float, float, float]] | None = None
        self._last_nudge_ts: float = 0.0

    def set_social_contact(self, when: Optional[float] = None) -> None:
        self._last_social_contact_ts = when if when is not None else time()

    def social_cooldown_active(self, cooldown_s: float, now: Optional[float] = None) -> bool:
        now_ts = now if now is not None else time()
        return (now_ts - self._last_social_contact_ts) < cooldown_s

    def debounce(self, name: str, xyz: Tuple[float, float, float], window_s: float) -> bool:
        """
        Returns True if we should suppress emitting the same nudge within the window.
        """
        now_ts = time()
        fp = (name, xyz)
        if self._last_nudge_fingerprint == fp and (now_ts - self._last_nudge_ts) < window_s:
            return True
        self._last_nudge_fingerprint = fp
        self._last_nudge_ts = now_ts
        return False


# ------------------------- #
#     SCHEDULER UTILITIES   #
# ------------------------- #

def _pose_from_dict(d: Dict) -> Pose:
    return Pose.from_dict(d)

def _xyz_tuple(p: Pose) -> Tuple[float, float, float]:
    return (p.xyz.x, p.xyz.y, p.xyz.z)

def _safe_and_green(safety_level: SafetyLevel) -> bool:
    return safety_level == SafetyLevel.GREEN


# ------------------------- #
#    ENGAGEMENT SCHEDULER   #
# ------------------------- #

class EngagementScheduler:
    """
    Policy-driven selection of a single best nudge candidate, respecting safety,
    consent, cooldowns, and debouncing (spec §9).

    Usage:
        sched = EngagementScheduler(policy=PolicyProfile())
        nudge = sched.decide(human_state, consent, affordances, risk_query)
        if nudge:
            # pass to planner/executor
    """

    def __init__(self, policy: Optional[PolicyProfile] = None):
        self.policy = policy or PolicyProfile()
        self.cooldowns = CooldownManager()

    # ---- Public API ---- #

    def notify_contact_executed(self) -> None:
        """
        Call this when a human contact (e.g., shoulder support) is executed successfully,
        so we enforce social cooldown (spec §9).
        """
        self.cooldowns.set_social_contact()

    def decide(
        self,
        human_state: Dict,
        consent: ConsentRecord,
        affordances: List[Dict],
        risk_query: Callable[[Pose], SafetyLevel],
    ) -> Optional[Nudge]:
        """
        Decide whether to emit a Nudge. Returns None if no safe/appropriate action exists.

        Priority order (spec §9): Safety > Consent > Task goal > Efficiency.
        """
        # 1) Filter hard safety: never nudge a RED candidate.
        candidates = self._filter_by_safety(affordances, risk_query)
        if not candidates:
            return None

        # 2) Rank by social need vs. task utility.
        ranked = self._rank_candidates(human_state, consent, candidates)

        # 3) Evaluate candidates in order.
        for idx, cand in enumerate(ranked):
            nudge, reason = self._candidate_to_nudge_with_reason(cand, human_state, consent)

            if nudge is not None:
                return nudge

            # If the **top** candidate was blocked due to **debounce**, do not fall back.
            # Return None to avoid appearing as “nagging” by switching targets immediately.
            if idx == 0 and reason == "debounce":
                return None

            # For cooldown or other reasons, try the next candidate.
            # (E.g., social cooldown should still allow an object-interaction nudge.)
            continue

        return None

    # ---- Internals ---- #

    def _filter_by_safety(
        self,
        affordances: List[Dict],
        risk_query: Callable[[Pose], SafetyLevel],
    ) -> List[Dict]:
        safe: List[Dict] = []
        for a in affordances:
            pose = _pose_from_dict(a["pose"])
            # If the affordance itself declares safety RED, skip early.
            declared = SafetyLevel(a.get("safety_level", "RED"))
            if declared == SafetyLevel.RED:
                continue
            # Query risk map at target (software path). If not GREEN, we only allow YELLOW for verification nudge.
            level = risk_query(pose)
            if level == SafetyLevel.RED:
                continue
            a["_pose_obj"] = pose
            a["_risk_level"] = level
            safe.append(a)
        return safe

    def _rank_candidates(
        self,
        human_state: Dict,
        consent: ConsentRecord,
        candidates: List[Dict],
    ) -> List[Dict]:
        """
        Compute a priority score. Favor:
        - Social support when distress >= threshold and policy allows shoulder.
        - GREEN over YELLOW.
        - Higher utility.
        """
        distress = float(human_state.get("distress", 0.0))
        social_mode = (
            bool(human_state.get("present", False))
            and distress >= self.policy.distress_support_threshold
            and self.policy.allow_shoulder
        )

        ranked: List[Tuple[float, Dict]] = []
        for a in candidates:
            base = 0.0
            # Safety weight: GREEN preferred.
            base += self.policy.w_safety * (1.0 if a["_risk_level"] == SafetyLevel.GREEN else 0.5)
            # Social weight: only for human category + distress.
            if social_mode and a.get("category") == "human" and a.get("name") == "shoulder":
                base += self.policy.w_social * 1.0
            # Task utility:
            base += self.policy.w_task * float(a.get("utility", 0.0))
            # Consent weight (soft boost if consent active for scope):
            if _consent_allows_shoulder(consent) and a.get("name") == "shoulder":
                base += self.policy.w_consent * 0.5

            ranked.append((base, a))

        ranked.sort(key=lambda t: t[0], reverse=True)
        return [a for _, a in ranked]

    def _candidate_to_nudge_with_reason(
        self,
        a: Dict,
        human_state: Dict,
        consent: ConsentRecord,
    ) -> Tuple[Optional[Nudge], str]:
        """
        Convert a ranked candidate into a Nudge while enforcing:
        - social cooldown (no repeated touches too quickly);
        - debouncing of identical nudges within window;
        - consent gate for social touch;
        - assign GREEN vs. YELLOW nudge level per spec logic.

        Returns (nudge, reason) where reason ∈ {"ok","debounce","cooldown","blocked"}.
        """
        pose: Pose = a["_pose_obj"]
        xyz = _xyz_tuple(pose)
        name = str(a.get("name", "unknown"))
        category = str(a.get("category", "object"))
        risk_level: SafetyLevel = a["_risk_level"]

        # Debounce identical nudges:
        if self.cooldowns.debounce(name, xyz, self.policy.debounce_window_s):
            return None, "debounce"

        # Social cooldown: only for human-target nudges (e.g., shoulder).
        if category == "human" and self.cooldowns.social_cooldown_active(self.policy.social_cooldown_s):
            return None, "cooldown"

        # Determine nudge level:
        if category == "human" and name == "shoulder":
            # Consent handling for social touch.
            if self.policy.require_explicit_for_social and not consent.is_active():
                level = NudgeLevel.YELLOW   # requires verification/consent
                rationale = "Consent required for social touch (shoulder support)"
            else:
                # consent active (explicit or policy) → GREEN if risk is GREEN
                level = NudgeLevel.GREEN if _safe_and_green(risk_level) else NudgeLevel.YELLOW
                rationale = "Shoulder support (distress cues + consent)"
        else:
            # Non-human object interaction:
            level = NudgeLevel.GREEN if _safe_and_green(risk_level) else NudgeLevel.YELLOW
            rationale = "Object interaction"

        # Compose and return Nudge
        priority = validate_priority(float(a.get("utility", 0.0)))
        normal = _choose_contact_normal(name, pose)

        nudge = Nudge(
            level=level,
            target=pose,
            normal=normal,
            rationale=rationale,
            priority=priority,
            expires_in_ms=self.policy.nudge_ttl_ms,
        )
        return nudge, "ok"


# ------------------------- #
#      HELPER FUNCTIONS     #
# ------------------------- #

def _choose_contact_normal(name: str, pose: Pose) -> Vector3:
    """
    Placeholder for contact normal selection policy. For shoulder support we bias to
    a gentle inward/upward normal; for general objects, default outward normal.
    In a real system this would be derived from surface geometry (spec §3/§9).
    """
    if name == "shoulder":
        return Vector3(0.0, 0.8, 0.6)
    return Vector3(0.0, 0.0, 1.0)


def _consent_allows_shoulder(consent: ConsentRecord) -> bool:
    """
    Minimal consent scope check for the default "shoulder_contact" scope (spec §11).
    """
    if consent.mode == ConsentMode.NONE:
        return False
    scopes = {s.lower() for s in consent.scope}
    return "shoulder_contact" in scopes or consent.mode == ConsentMode.POLICY


# ------------------------- #
#         EXAMPLE USE       #
# ------------------------- #

if __name__ == "__main__":
    # Minimal smoke test example (does not execute any motion).
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)

    # Risk query that always returns GREEN (for demo only).
    def risk_query(p: Pose) -> SafetyLevel:
        return SafetyLevel.GREEN

    human_state = {"present": True, "distress": 0.7}
    consent = ConsentRecord(
        subject_id="anon-7f3e",
        mode=ConsentMode.EXPLICIT,
        source="verbal",
        scope=["shoulder_contact"],
        ttl_s=60,
    )
    affordances = [
        {
            "name": "shoulder",
            "category": "human",
            "pose": {"frame": "W", "xyz": [0.42, -0.18, 1.36], "rpy": [0, 0, 1.57]},
            "utility": 0.9,
            "safety_level": "GREEN",
        },
        {
            "name": "flat_surface",
            "category": "object",
            "pose": {"frame": "W", "xyz": [0.80, 0.10, 0.95], "rpy": [0, 0, 0]},
            "utility": 0.4,
            "safety_level": "GREEN",
        },
    ]

    nudge = sched.decide(human_state, consent, affordances, risk_query)
    if nudge:
        print("NUDGE:", nudge.to_dict())
    else:
        print("No nudge emitted.")
