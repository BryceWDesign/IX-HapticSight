"""
Thermal interface models for IX-HapticSight.

This module defines backend-agnostic normalized structures for local thermal
sensing. The goal is to expose surface or near-surface temperature state in a
form that runtime safety and contact-governance logic can reason about without
depending on device-specific payloads.

This module does not talk to hardware directly.
It defines normalized payloads that adapters or simulators should emit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from ohip.schemas import Vector3

from .signal_health import FreshnessPolicy, SignalQuality


@dataclass(frozen=True)
class ThermalSample:
    """
    One normalized thermal reading.

    Fields:
    - `zone_id`: logical sensor zone or ROI identifier
    - `temperature_c`: measured temperature in Celsius
    - `location_xyz`: optional estimated location of the reading in the named frame
    - `confidence`: optional [0, 1] confidence-like score from the adapter
    """

    zone_id: str
    temperature_c: float
    location_xyz: Optional[Vector3] = None
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "zone_id": self.zone_id,
            "temperature_c": float(self.temperature_c),
            "location_xyz": self.location_xyz.as_list() if self.location_xyz is not None else None,
            "confidence": float(self.confidence),
        }


@dataclass(frozen=True)
class ThermalFrame:
    """
    Normalized thermal frame for one sensor surface or thermal ROI set.
    """

    sensor_name: str
    frame: str
    quality: SignalQuality
    samples: tuple[ThermalSample, ...] = field(default_factory=tuple)

    def sample_count(self) -> int:
        return len(self.samples)

    def has_samples(self) -> bool:
        return self.sample_count() > 0

    def max_temperature_c(self) -> Optional[float]:
        if not self.samples:
            return None
        return float(max(sample.temperature_c for sample in self.samples))

    def min_temperature_c(self) -> Optional[float]:
        if not self.samples:
            return None
        return float(min(sample.temperature_c for sample in self.samples))

    def hottest_sample(self) -> Optional[ThermalSample]:
        if not self.samples:
            return None
        return max(self.samples, key=lambda sample: sample.temperature_c)

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
            "samples": [sample.to_dict() for sample in self.samples],
        }


@dataclass(frozen=True)
class ThermalAssessment:
    """
    Compact thermal summary suitable for runtime safety checks.
    """

    heat_detected: bool
    over_limit: bool
    sample_count: int
    hottest_temperature_c: Optional[float]
    caution_temperature_c: float
    stop_temperature_c: float

    def to_dict(self) -> dict:
        return {
            "heat_detected": bool(self.heat_detected),
            "over_limit": bool(self.over_limit),
            "sample_count": int(self.sample_count),
            "hottest_temperature_c": None if self.hottest_temperature_c is None else float(self.hottest_temperature_c),
            "caution_temperature_c": float(self.caution_temperature_c),
            "stop_temperature_c": float(self.stop_temperature_c),
        }


def make_thermal_sample(
    *,
    zone_id: str,
    temperature_c: float,
    location_xyz: Optional[Iterable[float]] = None,
    confidence: float = 1.0,
) -> ThermalSample:
    location = list(location_xyz) if location_xyz is not None else None

    if location is not None and len(location) != 3:
        raise ValueError("location_xyz must contain exactly 3 elements when provided")
    if not (0.0 <= float(confidence) <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")

    return ThermalSample(
        zone_id=str(zone_id),
        temperature_c=float(temperature_c),
        location_xyz=Vector3.from_list(location) if location is not None else None,
        confidence=float(confidence),
    )


def assess_thermal(
    thermal_frame: ThermalFrame,
    *,
    caution_temperature_c: float = 38.0,
    stop_temperature_c: float = 45.0,
) -> ThermalAssessment:
    """
    Derive a compact thermal assessment from a normalized thermal frame.

    Semantics:
    - `heat_detected`: there is at least one sample at or above the caution threshold
    - `over_limit`: hottest sample is at or above the stop threshold
    """
    if stop_temperature_c < caution_temperature_c:
        raise ValueError("stop_temperature_c must be >= caution_temperature_c")

    hottest = thermal_frame.max_temperature_c()
    heat_detected = hottest is not None and hottest >= float(caution_temperature_c)
    over_limit = hottest is not None and hottest >= float(stop_temperature_c)

    return ThermalAssessment(
        heat_detected=bool(heat_detected),
        over_limit=bool(over_limit),
        sample_count=thermal_frame.sample_count(),
        hottest_temperature_c=None if hottest is None else float(hottest),
        caution_temperature_c=float(caution_temperature_c),
        stop_temperature_c=float(stop_temperature_c),
    )


__all__ = [
    "ThermalSample",
    "ThermalFrame",
    "ThermalAssessment",
    "make_thermal_sample",
    "assess_thermal",
]
