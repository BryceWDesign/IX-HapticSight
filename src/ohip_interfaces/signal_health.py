"""
Signal health and freshness models for IX-HapticSight.

This module defines backend-agnostic metadata structures that can be shared by:
- force/torque interfaces
- tactile interfaces
- proximity interfaces
- thermal interfaces
- future scene-perception interfaces

The goal is to make signal trust explicit before those signals are consumed by
runtime coordination or safety logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Optional


class SignalHealth(str, Enum):
    """
    Health classification for one normalized signal source.
    """

    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


class SignalSourceMode(str, Enum):
    """
    Source labeling to prevent confusion between live, replay, and simulated data.
    """

    LIVE = "LIVE"
    REPLAY = "REPLAY"
    SIMULATION = "SIMULATION"
    BENCHMARK = "BENCHMARK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FreshnessPolicy:
    """
    Freshness expectations for a signal stream.

    `max_age_ms` is the maximum acceptable age for the most recent sample.
    When `required` is False, staleness may narrow behavior rather than block it.
    """

    max_age_ms: int
    required: bool = True

    def is_fresh(self, *, sample_timestamp_utc_s: float, now_utc_s: Optional[float] = None) -> bool:
        now = float(now_utc_s if now_utc_s is not None else time())
        age_ms = (now - float(sample_timestamp_utc_s)) * 1000.0
        return age_ms <= float(self.max_age_ms)


@dataclass(frozen=True)
class SignalQuality:
    """
    Quality metadata for a normalized signal sample.

    This structure is intentionally generic so multiple sensing modalities can
    reuse it without inventing separate freshness or health semantics.
    """

    source_mode: SignalSourceMode
    health: SignalHealth
    sample_timestamp_utc_s: float
    received_timestamp_utc_s: float = field(default_factory=time)
    sequence_id: Optional[int] = None
    source_name: str = ""
    frame: str = ""
    note: str = ""

    def age_ms(self, *, now_utc_s: Optional[float] = None) -> float:
        now = float(now_utc_s if now_utc_s is not None else time())
        return max(0.0, (now - float(self.sample_timestamp_utc_s)) * 1000.0)

    def transport_latency_ms(self) -> float:
        return max(0.0, (float(self.received_timestamp_utc_s) - float(self.sample_timestamp_utc_s)) * 1000.0)

    def is_fresh(self, policy: FreshnessPolicy, *, now_utc_s: Optional[float] = None) -> bool:
        return policy.is_fresh(
            sample_timestamp_utc_s=self.sample_timestamp_utc_s,
            now_utc_s=now_utc_s,
        )

    def is_usable(self, policy: Optional[FreshnessPolicy] = None, *, now_utc_s: Optional[float] = None) -> bool:
        if self.health in {SignalHealth.INVALID, SignalHealth.UNAVAILABLE}:
            return False
        if policy is None:
            return self.health in {SignalHealth.NOMINAL, SignalHealth.DEGRADED}
        fresh = self.is_fresh(policy, now_utc_s=now_utc_s)
        if policy.required:
            return fresh and self.health in {SignalHealth.NOMINAL, SignalHealth.DEGRADED}
        return self.health in {SignalHealth.NOMINAL, SignalHealth.DEGRADED}

    def freshness_summary(
        self,
        policy: FreshnessPolicy,
        *,
        now_utc_s: Optional[float] = None,
    ) -> dict[str, object]:
        return {
            "source_mode": self.source_mode.value,
            "health": self.health.value,
            "sample_timestamp_utc_s": float(self.sample_timestamp_utc_s),
            "received_timestamp_utc_s": float(self.received_timestamp_utc_s),
            "age_ms": self.age_ms(now_utc_s=now_utc_s),
            "max_age_ms": int(policy.max_age_ms),
            "required": bool(policy.required),
            "fresh": bool(self.is_fresh(policy, now_utc_s=now_utc_s)),
            "usable": bool(self.is_usable(policy, now_utc_s=now_utc_s)),
            "sequence_id": self.sequence_id,
            "source_name": self.source_name,
            "frame": self.frame,
            "note": self.note,
        }


@dataclass(frozen=True)
class MultiSignalFreshness:
    """
    Compact multi-modality freshness summary for runtime checks.

    This is a generic interface-side summary and does not replace the runtime's
    richer SignalFreshness model. It exists so interface layers can expose a
    normalized freshness snapshot before runtime code consumes signal payloads.
    """

    force_torque: bool = False
    tactile: bool = False
    proximity: bool = False
    thermal: bool = False
    scene: bool = False

    def all_required(
        self,
        *,
        require_force_torque: bool = False,
        require_tactile: bool = False,
        require_proximity: bool = False,
        require_thermal: bool = False,
        require_scene: bool = False,
    ) -> bool:
        checks = [
            (require_force_torque, self.force_torque),
            (require_tactile, self.tactile),
            (require_proximity, self.proximity),
            (require_thermal, self.thermal),
            (require_scene, self.scene),
        ]
        return all(actual for required, actual in checks if required)

    def any_available(self) -> bool:
        return any([
            self.force_torque,
            self.tactile,
            self.proximity,
            self.thermal,
            self.scene,
        ])


__all__ = [
    "SignalHealth",
    "SignalSourceMode",
    "FreshnessPolicy",
    "SignalQuality",
    "MultiSignalFreshness",
]
