"""
Tactile interface models for IX-HapticSight.

This module defines backend-agnostic normalized structures for tactile sensing.
The goal is to expose tactile contact state in a form that runtime safety and
contact-governance logic can reason about without depending on device-specific
payloads.

This module does not talk to hardware directly.
It defines normalized payloads that adapters or simulators should emit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from ohip.schemas import Vector3

from .signal_health import FreshnessPolicy, SignalQuality


@dataclass(frozen=True)
class TactilePatch:
    """
    One localized tactile contact patch.

    Fields:
    - `patch_id`: stable identifier for the active patch within one frame
    - `location_xyz`: patch center in the named sensor or body frame
    - `normal_xyz`: estimated outward contact normal
    - `area_mm2`: estimated contact area
    - `pressure_kpa`: estimated average pressure
    - `shear_xy_kpa`: estimated tangential shear vector in the local patch plane
    """

    patch_id: str
    location_xyz: Vector3
    normal_xyz: Vector3
    area_mm2: float
    pressure_kpa: float
    shear_xy_kpa: tuple[float, float] = (0.0, 0.0)

    def shear_magnitude_kpa(self) -> float:
        x, y = self.shear_xy_kpa
        return float((x ** 2 + y ** 2) ** 0.5)

    def to_dict(self) -> dict:
        return {
            "patch_id": self.patch_id,
            "location_xyz": self.location_xyz.as_list(),
            "normal_xyz": self.normal_xyz.as_list(),
            "area_mm2": float(self.area_mm2),
            "pressure_kpa": float(self.pressure_kpa),
            "shear_xy_kpa": [float(self.shear_xy_kpa[0]), float(self.shear_xy_kpa[1])],
        }


@dataclass(frozen=True)
class TactileFrame:
    """
    Normalized tactile frame for one sensing surface and sample time.

    This representation supports sparse contact patches rather than requiring
    a dense raw taxel map. That keeps the interface smaller and easier to use
    in runtime logic, replay, and benchmarks.
    """

    surface_name: str
    frame: str
    quality: SignalQuality
    patches: tuple[TactilePatch, ...] = field(default_factory=tuple)

    def patch_count(self) -> int:
        return len(self.patches)

    def has_contact(self) -> bool:
        return self.patch_count() > 0

    def total_area_mm2(self) -> float:
        return float(sum(patch.area_mm2 for patch in self.patches))

    def max_pressure_kpa(self) -> float:
        if not self.patches:
            return 0.0
        return float(max(patch.pressure_kpa for patch in self.patches))

    def max_shear_kpa(self) -> float:
        if not self.patches:
            return 0.0
        return float(max(patch.shear_magnitude_kpa() for patch in self.patches))

    def is_fresh(self, policy: FreshnessPolicy, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_fresh(policy, now_utc_s=now_utc_s)

    def is_usable(self, policy: Optional[FreshnessPolicy] = None, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_usable(policy, now_utc_s=now_utc_s)

    def to_dict(self) -> dict:
        return {
            "surface_name": self.surface_name,
            "frame": self.frame,
            "quality": self.quality.freshness_summary(
                FreshnessPolicy(max_age_ms=0, required=False),
                now_utc_s=self.quality.sample_timestamp_utc_s,
            ),
            "patches": [patch.to_dict() for patch in self.patches],
        }


@dataclass(frozen=True)
class TactileContactAssessment:
    """
    Compact tactile summary suitable for runtime safety and contact checks.
    """

    contact_detected: bool
    multi_patch_contact: bool
    patch_count: int
    total_area_mm2: float
    max_pressure_kpa: float
    max_shear_kpa: float
    excessive_pressure: bool
    excessive_shear: bool

    def to_dict(self) -> dict:
        return {
            "contact_detected": bool(self.contact_detected),
            "multi_patch_contact": bool(self.multi_patch_contact),
            "patch_count": int(self.patch_count),
            "total_area_mm2": float(self.total_area_mm2),
            "max_pressure_kpa": float(self.max_pressure_kpa),
            "max_shear_kpa": float(self.max_shear_kpa),
            "excessive_pressure": bool(self.excessive_pressure),
            "excessive_shear": bool(self.excessive_shear),
        }


def make_tactile_patch(
    *,
    patch_id: str,
    location_xyz: Iterable[float],
    normal_xyz: Iterable[float],
    area_mm2: float,
    pressure_kpa: float,
    shear_xy_kpa: Iterable[float] = (0.0, 0.0),
) -> TactilePatch:
    loc = list(location_xyz)
    normal = list(normal_xyz)
    shear = list(shear_xy_kpa)

    if len(loc) != 3:
        raise ValueError("location_xyz must contain exactly 3 elements")
    if len(normal) != 3:
        raise ValueError("normal_xyz must contain exactly 3 elements")
    if len(shear) != 2:
        raise ValueError("shear_xy_kpa must contain exactly 2 elements")
    if area_mm2 < 0.0:
        raise ValueError("area_mm2 must be non-negative")
    if pressure_kpa < 0.0:
        raise ValueError("pressure_kpa must be non-negative")

    return TactilePatch(
        patch_id=str(patch_id),
        location_xyz=Vector3.from_list(loc),
        normal_xyz=Vector3.from_list(normal),
        area_mm2=float(area_mm2),
        pressure_kpa=float(pressure_kpa),
        shear_xy_kpa=(float(shear[0]), float(shear[1])),
    )


def assess_tactile_contact(
    tactile_frame: TactileFrame,
    *,
    pressure_threshold_kpa: float = 0.5,
    excessive_pressure_threshold_kpa: float = 10.0,
    excessive_shear_threshold_kpa: float = 5.0,
) -> TactileContactAssessment:
    """
    Derive a compact tactile contact assessment from a normalized tactile frame.
    """
    if pressure_threshold_kpa < 0.0:
        raise ValueError("pressure_threshold_kpa must be non-negative")
    if excessive_pressure_threshold_kpa < pressure_threshold_kpa:
        raise ValueError("excessive_pressure_threshold_kpa must be >= pressure_threshold_kpa")
    if excessive_shear_threshold_kpa < 0.0:
        raise ValueError("excessive_shear_threshold_kpa must be non-negative")

    patch_count = tactile_frame.patch_count()
    total_area = tactile_frame.total_area_mm2()
    max_pressure = tactile_frame.max_pressure_kpa()
    max_shear = tactile_frame.max_shear_kpa()

    return TactileContactAssessment(
        contact_detected=patch_count > 0 and max_pressure >= float(pressure_threshold_kpa),
        multi_patch_contact=patch_count > 1,
        patch_count=patch_count,
        total_area_mm2=float(total_area),
        max_pressure_kpa=float(max_pressure),
        max_shear_kpa=float(max_shear),
        excessive_pressure=max_pressure >= float(excessive_pressure_threshold_kpa),
        excessive_shear=max_shear >= float(excessive_shear_threshold_kpa),
    )


__all__ = [
    "TactilePatch",
    "TactileFrame",
    "TactileContactAssessment",
    "make_tactile_patch",
    "assess_tactile_contact",
]
