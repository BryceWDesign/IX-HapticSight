"""
Proximity interface models for IX-HapticSight.

This module defines backend-agnostic normalized structures for short-range
proximity sensing. The goal is to expose near-contact and corridor-clearance
state in a form that runtime safety and contact-governance logic can reason
about without depending on device-specific payloads.

This module does not talk to hardware directly.
It defines normalized payloads that adapters or simulators should emit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from ohip.schemas import Vector3

from .signal_health import FreshnessPolicy, SignalQuality


@dataclass(frozen=True)
class ProximityReturn:
    """
    One normalized proximity return.

    Fields:
    - `zone_id`: logical sensing zone or ray identifier
    - `distance_mm`: measured distance to nearest return
    - `direction_xyz`: normalized or device-defined sensing direction
    - `point_xyz`: optional nearest-point estimate in the named frame
    - `confidence`: optional [0, 1] confidence-like score from the adapter
    """

    zone_id: str
    distance_mm: float
    direction_xyz: Vector3
    point_xyz: Optional[Vector3] = None
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "distance_mm": float(self.distance_mm),
            "direction_xyz": self.direction_xyz.as_list(),
            "point_xyz": self.point_xyz.as_list() if self.point_xyz is not None else None,
            "confidence": float(self.confidence),
        }


@dataclass(frozen=True)
class ProximityFrame:
    """
    Normalized proximity frame for one sensing surface, ring, or viewpoint.

    This representation supports multiple per-zone returns rather than a raw
    vendor-specific array layout.
    """

    sensor_name: str
    frame: str
    quality: SignalQuality
    returns: tuple[ProximityReturn, ...] = field(default_factory=tuple)

    def return_count(self) -> int:
        return len(self.returns)

    def has_returns(self) -> bool:
        return self.return_count() > 0

    def min_distance_mm(self) -> Optional[float]:
        if not self.returns:
            return None
        return float(min(ret.distance_mm for ret in self.returns))

    def max_distance_mm(self) -> Optional[float]:
        if not self.returns:
            return None
        return float(max(ret.distance_mm for ret in self.returns))

    def nearest_return(self) -> Optional[ProximityReturn]:
        if not self.returns:
            return None
        return min(self.returns, key=lambda ret: ret.distance_mm)

    def is_fresh(self, policy: FreshnessPolicy, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_fresh(policy, now_utc_s=now_utc_s)

    def is_usable(self, policy: Optional[FreshnessPolicy] = None, *, now_utc_s: Optional[float] = None) -> bool:
        return self.quality.is_usable(policy, now_utc_s=now_utc_s)

    def to_dict(self) -> dict:
        return {
            "sensor_name": self.sensor_name,
            "frame": self.frame,
            "quality": self.quality.freshness_summary(
                FreshnessPolicy(max_age_ms=0, required=False),
                now_utc_s=self.quality.sample_timestamp_utc_s,
            ),
            "returns": [ret.to_dict() for ret in self.returns],
        }


@dataclass(frozen=True)
class ProximityAssessment:
    """
    Compact proximity summary suitable for runtime safety and pre-contact checks.
    """

    object_detected: bool
    near_contact: bool
    corridor_clear: bool
    return_count: int
    nearest_distance_mm: Optional[float]
    caution_distance_mm: float
    stop_distance_mm: float

    def to_dict(self) -> dict:
        return {
            "object_detected": bool(self.object_detected),
            "near_contact": bool(self.near_contact),
            "corridor_clear": bool(self.corridor_clear),
            "return_count": int(self.return_count),
            "nearest_distance_mm": None if self.nearest_distance_mm is None else float(self.nearest_distance_mm),
            "caution_distance_mm": float(self.caution_distance_mm),
            "stop_distance_mm": float(self.stop_distance_mm),
        }


def make_proximity_return(
    *,
    zone_id: str,
    distance_mm: float,
    direction_xyz: Iterable[float],
    point_xyz: Optional[Iterable[float]] = None,
    confidence: float = 1.0,
) -> ProximityReturn:
    direction = list(direction_xyz)
    point = list(point_xyz) if point_xyz is not None else None

    if len(direction) != 3:
        raise ValueError("direction_xyz must contain exactly 3 elements")
    if point is not None and len(point) != 3:
        raise ValueError("point_xyz must contain exactly 3 elements when provided")
    if distance_mm < 0.0:
        raise ValueError("distance_mm must be non-negative")
    if not (0.0 <= float(confidence) <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")

    return ProximityReturn(
        zone_id=str(zone_id),
        distance_mm=float(distance_mm),
        direction_xyz=Vector3.from_list(direction),
        point_xyz=Vector3.from_list(point) if point is not None else None,
        confidence=float(confidence),
    )


def assess_proximity(
    proximity_frame: ProximityFrame,
    *,
    caution_distance_mm: float = 120.0,
    stop_distance_mm: float = 40.0,
) -> ProximityAssessment:
    """
    Derive a compact proximity assessment from a normalized proximity frame.

    Semantics:
    - `object_detected`: there is at least one return
    - `near_contact`: nearest distance is at or below caution distance
    - `corridor_clear`: no return is at or below stop distance
    """
    if caution_distance_mm < 0.0:
        raise ValueError("caution_distance_mm must be non-negative")
    if stop_distance_mm < 0.0:
        raise ValueError("stop_distance_mm must be non-negative")
    if stop_distance_mm > caution_distance_mm:
        raise ValueError("stop_distance_mm must be <= caution_distance_mm")

    nearest = proximity_frame.min_distance_mm()
    object_detected = nearest is not None

    return ProximityAssessment(
        object_detected=object_detected,
        near_contact=bool(object_detected and nearest <= float(caution_distance_mm)),
        corridor_clear=bool((nearest is None) or (nearest > float(stop_distance_mm))),
        return_count=proximity_frame.return_count(),
        nearest_distance_mm=None if nearest is None else float(nearest),
        caution_distance_mm=float(caution_distance_mm),
        stop_distance_mm=float(stop_distance_mm),
    )


__all__ = [
    "ProximityReturn",
    "ProximityFrame",
    "ProximityAssessment",
    "make_proximity_return",
    "assess_proximity",
]
