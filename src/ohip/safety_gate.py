"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Safety Gate (spec §4, §5, §10)

Purpose
-------
Provide a single, deterministic interface for **dual-channel safety**:

  • Software path: validate plans against envelopes & Safety Map
  • Hardware/Firmware path: query independent faults (E-stop, over-temp/current/torque, watchdog)

Either channel may veto. Blocks are **edge-latched** until cleared by operator
or policy (see spec invariants).

Design notes
------------
- No external deps. Python 3.10+.
- Envelopes are passed in (parsed from /configs/force_limits.yaml).
- Safety Map is accessed via a callable risk_query(Pose) -> SafetyLevel.
- Hardware faults are provided via a minimal interface (see HardwareInterface).

This module does not command motion; it only reasons about *permission to proceed*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Dict, Any, List
from time import time

from .schemas import (
    Pose,
    Vector3,
    SafetyLevel,
    ContactPlan,
)


# ----------------------------------------------------------------------
# Hardware/Firmware status interface (implementation-specific adapter)
# ----------------------------------------------------------------------

@dataclass
class HardwareStatusSnapshot:
    """Point-in-time status as reported by an independent safety chain."""
    e_stop: bool = False
    overtemp: bool = False
    overcurrent: bool = False
    overtorque: bool = False
    watchdog_fault: bool = False


class HardwareInterface:
    """
    Minimal adapter. Users provide an instance whose `read()` returns HardwareStatusSnapshot.
    In real systems, this may talk to drives/PLCs/safety MCU.
    """
    def read(self) -> HardwareStatusSnapshot:  # pragma: no cover (interface)
        return HardwareStatusSnapshot()


# ----------------------------------------------------------------------
# SafetyGate
# ----------------------------------------------------------------------

class SafetyGate:
    """
    Veto authority for OHIP. See spec §10 (Dual-Channel Veto).

    Typical usage:
        gate = SafetyGate(envelopes, hw_iface, timers)
        ok_sw, why_sw = gate.software_ok(plan, risk_query, start_pose=current_pose)
        ok_hw, why_hw = gate.hardware_ok()
        if gate.dual_channel_ok(plan, risk_query, current_pose):
            # safe to hand off to Motion Exec
        else:
            # handle veto; reasons in gate.last_reason()

    Latching:
        - `trip(reason)` latches a block (manual clear required).
        - `monitor_runtime(feedback)` may auto-trip on measured over-limits.
    """

    def __init__(
        self,
        envelopes: Dict[str, Any],
        hw_iface: Optional[HardwareInterface] = None,
        timers: Optional[Dict[str, Any]] = None,
        active_profile: Optional[str] = None,
    ) -> None:
        """
        envelopes: parsed dict from /configs/force_limits.yaml
        timers: optional dict; uses envelopes['safety'] if omitted
        active_profile: name inside envelopes['profiles'] to apply by default
        """
        self._env = envelopes or {}
        self._profiles = dict(self._env.get("profiles", {}))
        self._defaults = dict(self._env.get("defaults", {}))
        self._safety = dict(self._env.get("safety", {}))
        self._controller = dict(self._env.get("controller", {}))

        self._profile_name = (
            active_profile
            or self._defaults.get("social_touch_profile")
            or next(iter(self._profiles.keys()), None)
        )
        self._profile = dict(self._profiles.get(self._profile_name, {}))

        self._hw = hw_iface or HardwareInterface()
        self._latched: bool = False
        self._latched_reason: str = ""
        self._latched_ts: float = 0.0

        # Cache some caps
        self._red_stop_ms = int(self._safety.get("red_stop_ms", 100))

    # ---------------- Public API ---------------- #

    def dual_channel_ok(
        self,
        plan: ContactPlan,
        risk_query: Callable[[Pose], SafetyLevel],
        start_pose: Optional[Pose] = None,
    ) -> bool:
        """True only if both software and hardware paths pass and no latch is active."""
        if self._latched:
            return False
        ok_sw, _ = self.software_ok(plan, risk_query, start_pose)
        ok_hw, _ = self.hardware_ok()
        return bool(ok_sw and ok_hw)

    def software_ok(
        self,
        plan: ContactPlan,
        risk_query: Callable[[Pose], SafetyLevel],
        start_pose: Optional[Pose] = None,
    ) -> Tuple[bool, str]:
        """
        Software path validation:
          1) Envelopes (force, speed, dwell, impedance)
          2) Safety Map: target is not RED
          3) (Optional) Corridor sampling from start_pose to target (no RED)
        """
        # 0) If latched, fail fast
        if self._latched:
            return False, "latched"

        # 1) Envelopes
        ok_env, why_env = self._check_envelopes(plan)
        if not ok_env:
            return False, f"envelope_veto: {why_env}"

        # 2) Target cell safety
        lvl_target = risk_query(plan.target)
        if lvl_target == SafetyLevel.RED:
            return False, "safety_map: target RED"

        # 3) Optional corridor sampling (straight-line coarse check)
        if start_pose is not None:
            if not self._corridor_green(start_pose, plan.target, risk_query):
                return False, "safety_map: corridor contains RED"

        return True, "ok"

    def hardware_ok(self) -> Tuple[bool, str]:
        """Hardware path: read independent faults (E-stop, over-limits, watchdog)."""
        if self._latched:
            return False, "latched"

        snap = self._hw.read()
        if snap.e_stop:
            return False, "hw_veto: e_stop"
        if snap.watchdog_fault:
            return False, "hw_veto: watchdog_fault"
        if snap.overtemp:
            return False, "hw_veto: overtemp"
        if snap.overcurrent:
            return False, "hw_veto: overcurrent"
        if snap.overtorque:
            return False, "hw_veto: overtorque"
        return True, "ok"

    def trip(self, reason: str) -> None:
        """Latch a block. Requires explicit operator clear."""
        self._latched = True
        self._latched_reason = reason
        self._latched_ts = time()

    def clear_latch(self) -> None:
        """Clear the safety latch (operator/policy controlled)."""
        self._latched = False
        self._latched_reason = ""
        self._latched_ts = 0.0

    def is_latched(self) -> bool:
        return self._latched

    def last_reason(self) -> str:
        return self._latched_reason

    def monitor_runtime(self, feedback: Dict[str, float]) -> Optional[str]:
        """
        Optional runtime guard; can be called at high rate with measured signals to auto-trip.
        feedback keys (all optional; add as available):
            - force_peak_N
            - ee_temp_C
            - ee_current_A
            - ee_torque_Nm
        Returns reason if trip occurred.
        """
        if self._latched:
            return self._latched_reason

        # Thermal cap from profile (if present)
        max_temp = self._profile.get("max_surface_temp_C", None)
        if max_temp is not None:
            if float(feedback.get("ee_temp_C", -1e9)) > float(max_temp):
                self.trip("runtime_overtemp")
                return self._latched_reason

        # Peak force (measured) should not exceed plan/profile caps dramatically.
        max_force = float(self._profile.get("max_force_N", 0.0))
        if "force_peak_N" in feedback and max_force > 0.0:
            if float(feedback["force_peak_N"]) > max_force:
                self.trip("runtime_overforce")
                return self._latched_reason

        # Current/torque are generally enforced by hardware; treat here as best-effort.
        if float(feedback.get("ee_torque_Nm", 0.0)) > float(self._profile.get("max_torque_Nm", 1e9)):
            self.trip("runtime_overtorque")
            return self._latched_reason

        # Current threshold may be controller-specific; only trip if provided and >0 cap exists.
        # (Most systems defer to hardware for overcurrent.)
        return None

    # ---------------- Internals ---------------- #

    def _check_envelopes(self, plan: ContactPlan) -> Tuple[bool, str]:
        """Compare planned magnitudes against profile caps and controller bounds."""
        prof = self._profile

        def cap(name: str, default: float = 0.0) -> float:
            return float(prof.get(name, default))

        # Force / dwell
        max_force = cap("max_force_N", 0.0)
        if max_force and plan.peak_force_N > max_force:
            return False, f"peak_force_N {plan.peak_force_N:.3f} > cap {max_force:.3f}"

        dwell_min = int(prof.get("dwell_ms_min", 0))
        dwell_max = int(prof.get("dwell_ms_max", 10_000))
        if not (dwell_min <= plan.dwell_ms <= dwell_max):
            return False, f"dwell_ms {plan.dwell_ms} outside [{dwell_min},{dwell_max}]"

        # Speeds
        if "approach_speed_mps" in prof and plan.approach_speed_mps > cap("approach_speed_mps"):
            return False, f"approach_speed_mps {plan.approach_speed_mps:.3f} > cap {cap('approach_speed_mps'):.3f}"
        if "release_speed_mps" in prof and plan.release_speed_mps > cap("release_speed_mps"):
            return False, f"release_speed_mps {plan.release_speed_mps:.3f} > cap {cap('release_speed_mps'):.3f}"

        # Impedance ranges
        n_lo, n_hi = plan.impedance.normal_N_per_mm
        t_lo, t_hi = plan.impedance.tangential_N_per_mm
        p_n = prof.get("impedance", {}).get("normal_N_per_mm", None)
        p_t = prof.get("impedance", {}).get("tangential_N_per_mm", None)
        if p_n:
            lo, hi = float(p_n[0]), float(p_n[1])
            if not (lo <= n_lo <= n_hi <= hi):
                return False, f"normal_impedance {n_lo}-{n_hi} outside [{lo}-{hi}]"
        if p_t:
            lo, hi = float(p_t[0]), float(p_t[1])
            if not (lo <= t_lo <= t_hi <= hi):
                return False, f"tangential_impedance {t_lo}-{t_hi} outside [{lo}-{hi}]"

        return True, "ok"

    def _corridor_green(
        self,
        start: Pose,
        target: Pose,
        risk_query: Callable[[Pose], SafetyLevel],
        samples: int = 10,
    ) -> bool:
        """
        Coarse straight-line sampling between start and target.
        Any RED along the corridor vetoes (spec §4/§5).
        """
        sx, sy, sz = start.xyz.x, start.xyz.y, start.xyz.z
        tx, ty, tz = target.xyz.x, target.xyz.y, target.xyz.z
        rx, ry, rz = (tx - sx), (ty - sy), (tz - sz)

        for k in range(1, samples + 1):
            alpha = k / float(samples + 1)
            px, py, pz = sx + alpha * rx, sy + alpha * ry, sz + alpha * rz
            p = Pose(frame=target.frame, xyz=Vector3(px, py, pz), rpy=target.rpy)
            if risk_query(p) == SafetyLevel.RED:
                return False
        return True
