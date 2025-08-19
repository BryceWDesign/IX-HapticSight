"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Contact Planner (spec §3, §7, §9, §10, §16)

Purpose
-------
Transform a policy-approved Nudge into a concrete ContactPlan that:
  • Respects configured envelopes (/configs/force_limits.yaml profile caps)
  • Chooses force/dwell/speeds and impedance inside safe ranges
  • Carries consent context forward for PRECONTACT verification (spec §5/§11)
The SafetyGate re-validates the plan against Safety Map and hardware paths.

No external deps. Python 3.10+.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

from .schemas import (
    Nudge,
    Pose,
    Vector3,
    ImpedanceProfile,
    ContactPlan,
    ConsentRecord,
    ConsentMode,
)


# ------------------------- #
#      PROFILE HELPERS      #
# ------------------------- #

def _load_profile(envelopes: Dict[str, Any], profile_name: Optional[str]) -> Dict[str, Any]:
    profiles = envelopes.get("profiles", {}) or {}
    defaults = envelopes.get("defaults", {}) or {}
    name = profile_name or defaults.get("social_touch_profile") or (list(profiles.keys())[0] if profiles else None)
    return dict(profiles.get(name, {})), name or "unknown"


def _within(lo: float, hi: float, val: float) -> float:
    """Clamp val to [lo, hi]."""
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val


def _tuple2(lohi: Tuple[float, float]) -> Tuple[float, float]:
    return (float(lohi[0]), float(lohi[1]))


# ------------------------- #
#      CONTACT PLANNER      #
# ------------------------- #

@dataclass
class PlannerHints:
    """
    Optional hints to bias plan selection (never exceed profile caps):
      - peak_force_target: desired force in N (will be clamped)
      - dwell_ms_target: desired dwell in ms (will be clamped)
      - approach_speed_mps / release_speed_mps: desired speeds (clamped)
    """
    peak_force_target: Optional[float] = None
    dwell_ms_target: Optional[int] = None
    approach_speed_mps: Optional[float] = None
    release_speed_mps: Optional[float] = None


class ContactPlanner:
    """
    Plan generator from Nudge → ContactPlan.

    Usage:
        planner = ContactPlanner(envelopes)  # parsed YAML dict
        plan = planner.plan(nudge, consent, profile_name=None, hints=None)
        if plan: ... hand to SafetyGate.dual_channel_ok(...)
    """

    def __init__(self, envelopes: Dict[str, Any]):
        self._env = envelopes or {}

    def plan(
        self,
        nudge: Nudge,
        consent: ConsentRecord,
        profile_name: Optional[str] = None,
        hints: Optional[PlannerHints] = None,
    ) -> Optional[ContactPlan]:
        """
        Create a ContactPlan within configured caps. Returns None if inputs incomplete.
        """
        if nudge is None or nudge.target is None:
            return None

        profile, pname = _load_profile(self._env, profile_name)

        # --- Caps from profile (with conservative fallbacks from spec) ---
        max_force_N = float(profile.get("max_force_N", 1.2))
        dwell_min = int(profile.get("dwell_ms_min", 1000))
        dwell_max = int(profile.get("dwell_ms_max", 3000))
        appr_cap = float(profile.get("approach_speed_mps", 0.15))
        rel_cap = float(profile.get("release_speed_mps", 0.20))

        imp_p = profile.get("impedance", {}) or {}
        n_lo, n_hi = _tuple2(imp_p.get("normal_N_per_mm", (0.3, 0.6)))
        t_lo, t_hi = _tuple2(imp_p.get("tangential_N_per_mm", (0.1, 0.3)))

        # --- Choose values inside envelopes ---
        # Force: aim slightly under cap (e.g., 0.85×) unless caller provides a target
        peak_force_target = hints.peak_force_target if hints and hints.peak_force_target is not None else 0.85 * max_force_N
        peak_force = min(float(peak_force_target), max_force_N)

        # Dwell: use target or center of range
        dwell_target = hints.dwell_ms_target if hints and hints.dwell_ms_target is not None else int(0.5 * (dwell_min + dwell_max))
        dwell_ms = int(_within(dwell_min, dwell_max, dwell_target))

        # Speeds: clamp to caps
        appr_target = hints.approach_speed_mps if hints and hints.approach_speed_mps is not None else appr_cap
        rel_target = hints.release_speed_mps if hints and hints.release_speed_mps is not None else rel_cap
        approach_speed = float(min(appr_target, appr_cap))
        release_speed = float(min(rel_target, rel_cap))

        # Impedance: use full allowed ranges (planner-level range; controller selects working point)
        impedance = ImpedanceProfile(
            normal_N_per_mm=(n_lo, n_hi),
            tangential_N_per_mm=(t_lo, t_hi),
        )

        # Consent context forwarded (PRECONTACT will re-check freshness)
        c_mode = consent.mode if isinstance(consent.mode, ConsentMode) else ConsentMode(str(consent.mode or "none"))

        # Build plan
        plan = ContactPlan(
            target=nudge.target,
            contact_normal=nudge.normal,
            peak_force_N=peak_force,
            dwell_ms=dwell_ms,
            approach_speed_mps=approach_speed,
            release_speed_mps=release_speed,
            impedance=impedance,
            rationale=nudge.rationale + f" [profile={pname}]",
            consent_mode=c_mode,
        )
        # Validate against schema rules (ranges, etc.)
        plan.validate()
        return plan
