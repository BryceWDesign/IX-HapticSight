"""XR observability payloads for hazard, intent, consent and force authority."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from ohip.schemas import SafetyLevel


@dataclass(frozen=True)
class XRHazardMarker:
    marker_id: str
    xyz_m: tuple[float, float, float]
    size_m: float
    level: SafetyLevel
    label: str
    confidence: float

    def to_dict(self) -> dict:
        doc = asdict(self)
        doc["level"] = self.level.value
        return doc


@dataclass(frozen=True)
class XRState:
    session_id: str
    consent_active: bool
    safety_authority: str
    force_cap_N: float
    speed_cap_mps: float
    controller_state: str
    reason: str
    markers: tuple[XRHazardMarker, ...] = ()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "consent_active": self.consent_active,
            "safety_authority": self.safety_authority,
            "force_cap_N": self.force_cap_N,
            "speed_cap_mps": self.speed_cap_mps,
            "controller_state": self.controller_state,
            "reason": self.reason,
            "markers": [m.to_dict() for m in self.markers],
        }
