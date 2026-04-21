"""
Force/torque interface models for IX-HapticSight.

This module defines backend-agnostic normalized structures for wrist or joint-
adjacent force/torque sensing. The goal is to make measured contact-related
signals explicit before they reach runtime coordination or safety logic.

This layer does not talk to hardware directly.
It defines the normalized payload shape that a hardware-specific adapter or
simulation bridge should produce.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Optional

from ohip.schemas import Vector3

from .signal_health import FreshnessPolicy, SignalQuality


@dataclass(frozen=True)
class ForceTorqueSample:
    """
    Normalized force/torque sample.

    Conventions:
    - vectors are expressed in the named `frame`
    - force is in newtons
    - torque is in newton-meters
    - `quality` carries health, freshness, and source metadata
    """

    frame: str
    force: Vector3
    torque: Vector3
    quality: SignalQuality

    def force_magnitude_N(self) -> float:
        return sqrt(self.force.x ** 2 + self.force.y ** 2 + self.force.z ** 2)

    def torque_magnitude_Nm(self) -> float:
        return sqrt(self.torque.x ** 2 + self.torque.y ** 2 + self.torque.z ** 2)

    def is_fresh(self, policy: FreshnessPolicy, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_fresh(policy, now_utc_s=now_utc_s)

    def is_usable(self, policy: Optional[FreshnessPolicy] = None, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_usable(policy, now_utc_s=now_utc_s)

    def to_dict(self) -> dict:
        return {
            "frame": self.frame,
            "force": self.force.as_list(),
            "torque": self.torque.as_list(),
            "quality": self.quality.freshness_summary(
                FreshnessPolicy(max_age_ms=0, required=False),
                now_utc_s=self.quality.sample_timestamp_utc_s,
            ),
        }


@dataclass(frozen=True)
class ContactForceAssessment:
    """
    Compact force/torque-derived contact assessment.

    This is not a full safety verdict. It is a normalized signal-side summary
    that higher layers can consume when deciding whether contact looks nominal,
    absent, uncertain, or excessive.
    """

    contact_detected: bool
    excessive_force: bool
    force_magnitude_N: float
    torque_magnitude_Nm: float
    threshold_contact_N: float
    threshold_excessive_N: float

    def to_dict(self) -> dict:
        return {
            "contact_detected": bool(self.contact_detected),
            "excessive_force": bool(self.excessive_force),
            "force_magnitude_N": float(self.force_magnitude_N),
            "torque_magnitude_Nm": float(self.torque_magnitude_Nm),
            "threshold_contact_N": float(self.threshold_contact_N),
            "threshold_excessive_N": float(self.threshold_excessive_N),
        }


def make_force_torque_sample(
    *,
    frame: str,
    force_xyz: Iterable[float],
    torque_xyz: Iterable[float],
    quality: SignalQuality,
) -> ForceTorqueSample:
    """
    Convenience constructor for adapters that start with list/tuple payloads.
    """
    force_vals = list(force_xyz)
    torque_vals = list(torque_xyz)

    if len(force_vals) != 3:
        raise ValueError("force_xyz must contain exactly 3 elements")
    if len(torque_vals) != 3:
        raise ValueError("torque_xyz must contain exactly 3 elements")

    return ForceTorqueSample(
        frame=str(frame),
        force=Vector3.from_list(force_vals),
        torque=Vector3.from_list(torque_vals),
        quality=quality,
    )


def assess_contact_force(
    sample: ForceTorqueSample,
    *,
    contact_threshold_N: float = 0.25,
    excessive_threshold_N: float = 2.0,
) -> ContactForceAssessment:
    """
    Derive a compact contact-force assessment from one normalized sample.

    Parameters are intentionally simple at this stage:
    - `contact_threshold_N` is the minimum force magnitude counted as contact
    - `excessive_threshold_N` is the level treated as suspicious or excessive

    Higher layers remain responsible for context, dwell, direction, and policy.
    """
    if contact_threshold_N < 0.0:
        raise ValueError("contact_threshold_N must be non-negative")
    if excessive_threshold_N < contact_threshold_N:
        raise ValueError("excessive_threshold_N must be >= contact_threshold_N")

    force_mag = sample.force_magnitude_N()
    torque_mag = sample.torque_magnitude_Nm()

    return ContactForceAssessment(
        contact_detected=force_mag >= float(contact_threshold_N),
        excessive_force=force_mag >= float(excessive_threshold_N),
        force_magnitude_N=float(force_mag),
        torque_magnitude_Nm=float(torque_mag),
        threshold_contact_N=float(contact_threshold_N),
        threshold_excessive_N=float(excessive_threshold_N),
    )


__all__ = [
    "ForceTorqueSample",
    "ContactForceAssessment",
    "make_force_torque_sample",
    "assess_contact_force",
]
