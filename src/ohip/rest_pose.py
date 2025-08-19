"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Rest Pose Generator (spec §8, §5)

Purpose
-------
Provide deterministic fingertip/palm "REST" targets and lightweight helpers to:
  • Transform body-frame rest targets into world-frame coordinates
  • Estimate/plan a time-bounded return-to-rest (spec requires 500–800 ms)
  • Check whether current fingertip positions are within rest tolerances

Notes
-----
- This module is kinematics-agnostic (no joint-space ops). It outputs Cartesian
  targets you can feed to your motion layer.
- Uses schemas.RestTargets defaults unless overridden.
- Controller jerk/accel caps are documented in /configs/force_limits.yaml; we
  provide simple linear interpolation utilities that upper-bound timing per spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from typing import Dict, Tuple

from .schemas import Pose, Vector3, RestTargets, RPY


# ------------------------- #
#   ROTATIONS & TRANSFORMS  #
# ------------------------- #

def _rpy_to_rot(rpy: RPY) -> Tuple[Tuple[float, float, float],
                                   Tuple[float, float, float],
                                   Tuple[float, float, float]]:
    """
    Convert roll-pitch-yaw (radians) to 3x3 rotation matrix.
    Right-handed, ZYX convention (yaw->pitch->roll), matching common robotics frames.
    """
    cr, sr = cos(rpy.r), sin(rpy.r)
    cp, sp = cos(rpy.p), sin(rpy.p)
    cy, sy = cos(rpy.y), sin(rpy.y)

    # R = Rz(yaw) * Ry(pitch) * Rx(roll)
    r00 = cy * cp
    r01 = cy * sp * sr - sy * cr
    r02 = cy * sp * cr + sy * sr

    r10 = sy * cp
    r11 = sy * sp * sr + cy * cr
    r12 = sy * sp * cr - cy * sr

    r20 = -sp
    r21 = cp * sr
    r22 = cp * cr

    return ((r00, r01, r02),
            (r10, r11, r12),
            (r20, r21, r22))


def _apply_rot(R: Tuple[Tuple[float, float, float], ...], v: Vector3) -> Vector3:
    x = R[0][0] * v.x + R[0][1] * v.y + R[0][2] * v.z
    y = R[1][0] * v.x + R[1][1] * v.y + R[1][2] * v.z
    z = R[2][0] * v.x + R[2][1] * v.y + R[2][2] * v.z
    return Vector3(x, y, z)


def _add(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(a.x + b.x, a.y + b.y, a.z + b.z)


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)


def _norm(v: Vector3) -> float:
    return (v.x * v.x + v.y * v.y + v.z * v.z) ** 0.5


def _scale(v: Vector3, s: float) -> Vector3:
    return Vector3(v.x * s, v.y * s, v.z * s)


# ------------------------- #
#     REST POSE GENERATOR   #
# ------------------------- #

@dataclass
class RestConfig:
    """
    Tuning parameters for rest behavior.
    """
    # Allowed positional error (meters) to consider "at rest"
    rest_pos_tol_m: float = 0.01  # 10 mm
    # Target time window for return-to-rest per spec (seconds)
    target_time_low_s: float = 0.50
    target_time_high_s: float = 0.80
    # Max allowed Cartesian speed toward rest (m/s) for visible, non-startle motion
    max_return_speed_mps: float = 0.25


class RestPoseGenerator:
    """
    Generate world-frame rest targets and provide helpers to guide return-to-rest motion.

    Typical usage:
        gen = RestPoseGenerator()
        targets_W = gen.targets_world(pose_body_in_world)
        within = gen.within_rest(current_tips_W, targets_W)
        step = gen.interpolate_step(current_tips_W, targets_W, dt_s=0.02)
    """

    def __init__(self, rest_targets: RestTargets | None = None, cfg: RestConfig | None = None):
        self.rest_targets = rest_targets or RestTargets()
        self.cfg = cfg or RestConfig()

    # ---------- Targets ---------- #

    def targets_world(self, body_pose_W: Pose) -> Dict[str, Vector3]:
        """
        Transform default body-frame rest targets into world frame using body pose.
        """
        R = _rpy_to_rot(body_pose_W.rpy)
        origin = body_pose_W.xyz

        def xform(pt_B: Vector3) -> Vector3:
            return _add(origin, _apply_rot(R, pt_B))

        return {
            "index_tip":  xform(self.rest_targets.index_tip),
            "middle_tip": xform(self.rest_targets.middle_tip),
            "ring_tip":   xform(self.rest_targets.ring_tip),
            "little_tip": xform(self.rest_targets.little_tip),
        }

    # ---------- Checks ---------- #

    def within_rest(self, current_tips_W: Dict[str, Vector3], targets_W: Dict[str, Vector3]) -> bool:
        """
        True if all fingertips are within positional tolerance of the world rest targets.
        """
        tol = self.cfg.rest_pos_tol_m
        for k, tgt in targets_W.items():
            cur = current_tips_W.get(k)
            if cur is None:
                return False
            if _norm(_sub(cur, tgt)) > tol:
                return False
        return True

    # ---------- Timing ---------- #

    def estimate_return_time_s(self, current_tips_W: Dict[str, Vector3], targets_W: Dict[str, Vector3],
                               speed_mps: float | None = None) -> float:
        """
        Estimate time to rest using max distance among fingertips and a speed cap.
        Clamped into [target_time_low_s, target_time_high_s].
        """
        if not current_tips_W:
            return self.cfg.target_time_high_s
        vmax = 0.0
        for k, tgt in targets_W.items():
            cur = current_tips_W.get(k)
            if cur is None:
                continue
            vmax = max(vmax, _norm(_sub(cur, tgt)))
        speed = min(float(speed_mps or self.cfg.max_return_speed_mps), self.cfg.max_return_speed_mps)
        raw = vmax / max(speed, 1e-6)
        return max(self.cfg.target_time_low_s, min(raw, self.cfg.target_time_high_s))

    # ---------- Interpolation ---------- #

    def interpolate_step(self,
                         current_tips_W: Dict[str, Vector3],
                         targets_W: Dict[str, Vector3],
                         dt_s: float,
                         speed_mps: float | None = None) -> Dict[str, Vector3]:
        """
        Produce the next waypoint for each fingertip toward rest using capped linear steps.

        This is a **Cartesian** helper, not a joint-space controller. Your motion layer
        can track these tip targets or convert them into end-effector motions.

        The step size is min(speed * dt, distance_to_target) for each fingertip.
        """
        speed_cap = min(float(speed_mps or self.cfg.max_return_speed_mps), self.cfg.max_return_speed_mps)
        next_pos: Dict[str, Vector3] = {}

        for k, tgt in targets_W.items():
            cur = current_tips_W.get(k, tgt)
            delta = _sub(tgt, cur)
            dist = _norm(delta)
            if dist <= 1e-6:
                next_pos[k] = tgt
                continue
            step_mag = min(speed_cap * max(dt_s, 1e-6), dist)
            step = _scale(delta, step_mag / dist)
            next_pos[k] = _add(cur, step)

        return next_pos

    # ---------- Convenience ---------- #

    def time_window_ok(self, t_s: float) -> bool:
        """
        Check if a proposed return-to-rest time lies within the recommended
        (spec) window of 0.50–0.80 seconds.
        """
        return self.cfg.target_time_low_s <= t_s <= self.cfg.target_time_high_s
