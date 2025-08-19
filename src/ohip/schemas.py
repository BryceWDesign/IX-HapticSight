"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Canonical data schemas (enums, dataclasses, JSON helpers)

This module defines the minimal, implementation-agnostic message types used
throughout the OHIP stack. It mirrors the normative structures in /docs/spec.md
(Consent Record, Safety Map Cell, Nudge, Contact Plan, Execution Log, etc.)
so different components (ROS2/LCM/ZeroMQ) can interoperate without surprises.

No external dependencies. Python 3.10+.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from time import time
from datetime import datetime, timezone


OHIP_SCHEMAS_VERSION = "v0.1.0"


# ------------------------- #
#        ENUMERATIONS       #
# ------------------------- #

class SafetyLevel(str, Enum):
    GREEN = "GREEN"   # safe — autonomous contact allowed within configured envelopes
    YELLOW = "YELLOW" # verify — require consent/confirmation/additional sensing
    RED = "RED"       # prohibited — contact/traversal blocked


class HazardClass(str, Enum):
    FIRE = "fire"
    BLADE = "blade"
    HOT = "hot"
    MOVING = "moving"
    LIQUID = "liquid"
    UNKNOWN = "unknown"


class ConsentMode(str, Enum):
    EXPLICIT = "explicit"   # contemporaneous, affirmative
    POLICY = "policy"       # institutional/caregiver profile allows limited contact
    NONE = "none"           # no consent in scope


class ConsentSource(str, Enum):
    VERBAL = "verbal"
    GESTURE = "gesture"
    UI = "ui"
    PROFILE = "profile"


class NudgeLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"  # should not be produced as a nudge to contact; included for completeness


# ------------------------- #
#     BASIC PRIMITIVES      #
# ------------------------- #

@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def as_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @staticmethod
    def from_list(vals: List[float]) -> "Vector3":
        assert len(vals) == 3, "Vector3 requires 3 elements"
        return Vector3(float(vals[0]), float(vals[1]), float(vals[2]))


@dataclass
class RPY:
    """Roll-Pitch-Yaw (radians)."""
    r: float
    p: float
    y: float

    def as_list(self) -> List[float]:
        return [self.r, self.p, self.y]

    @staticmethod
    def from_list(vals: List[float]) -> "RPY":
        assert len(vals) == 3, "RPY requires 3 elements"
        return RPY(float(vals[0]), float(vals[1]), float(vals[2]))


@dataclass
class Pose:
    """
    Cartesian pose w.r.t. a named frame.
    - frame: e.g., "W" (world), "B" (body), "E" (end-effector)
    """
    frame: str
    xyz: Vector3
    rpy: RPY

    def to_dict(self) -> Dict[str, Any]:
        return {"frame": self.frame, "xyz": self.xyz.as_list(), "rpy": self.rpy.as_list()}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Pose":
        return Pose(
            frame=str(d.get("frame", "W")),
            xyz=Vector3.from_list(d["xyz"]),
            rpy=RPY.from_list(d["rpy"]),
        )


# ------------------------- #
#       CORE MESSAGES       #
# ------------------------- #

@dataclass
class ConsentRecord:
    subject_id: str                     # anonymized or pseudonymous ID
    mode: ConsentMode                   # explicit | policy | none
    source: ConsentSource               # verbal | gesture | ui | profile
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scope: List[str] = field(default_factory=list)  # e.g., ["shoulder_contact"]
    ttl_s: int = 60

    def is_active(self, now_utc: Optional[float] = None) -> bool:
        """Return True if consent is still within TTL."""
        if self.mode == ConsentMode.NONE:
            return False
        now = now_utc if now_utc is not None else time()
        try:
            t0 = datetime.fromisoformat(self.timestamp).timestamp()
        except Exception:
            return False
        return (now - t0) <= float(self.ttl_s)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        d["source"] = self.source.value
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ConsentRecord":
        return ConsentRecord(
            subject_id=str(d["subject_id"]),
            mode=ConsentMode(d.get("mode", "none")),
            source=ConsentSource(d.get("source", "ui")),
            timestamp=str(d.get("timestamp", datetime.now(timezone.utc).isoformat())),
            scope=list(d.get("scope", [])),
            ttl_s=int(d.get("ttl_s", 60)),
        )


@dataclass
class SafetyMapCell:
    """Safety voxel/tile classification aligned to scene grid."""
    cell: Tuple[int, int, int]
    hazard_class: HazardClass
    level: SafetyLevel
    updated_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell": list(self.cell),
            "class": self.hazard_class.value,
            "level": self.level.value,
            "updated_ms": int(self.updated_ms),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SafetyMapCell":
        cell = d.get("cell", [0, 0, 0])
        assert len(cell) == 3, "SafetyMapCell.cell must be [i,j,k]"
        return SafetyMapCell(
            cell=(int(cell[0]), int(cell[1]), int(cell[2])),
            hazard_class=HazardClass(d.get("class", "unknown")),
            level=SafetyLevel(d.get("level", "RED")),
            updated_ms=int(d.get("updated_ms", 0)),
        )


@dataclass
class Nudge:
    """Engagement suggestion emitted by the scheduler."""
    level: NudgeLevel
    target: Pose
    normal: Vector3
    rationale: str
    priority: float           # 0..1
    expires_in_ms: int        # validity window for acting

    def is_expired(self, now_utc_ms: Optional[int] = None, emitted_ms: Optional[int] = None) -> bool:
        """
        True if current time exceeds (emitted_ms + expires_in_ms).
        If emitted_ms is None, treat as expired (defensive).
        """
        if emitted_ms is None:
            return True
        now_ms = int((time() if now_utc_ms is None else now_utc_ms) * 1000.0)
        return now_ms > (int(emitted_ms) + int(self.expires_in_ms))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "target": self.target.to_dict(),
            "normal": self.normal.as_list(),
            "rationale": self.rationale,
            "priority": float(self.priority),
            "expires_in_ms": int(self.expires_in_ms),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Nudge":
        return Nudge(
            level=NudgeLevel(d.get("level", "RED")),
            target=Pose.from_dict(d["target"]),
            normal=Vector3.from_list(d.get("normal", [0.0, 0.0, 1.0])),
            rationale=str(d.get("rationale", "")),
            priority=float(d.get("priority", 0.0)),
            expires_in_ms=int(d.get("expires_in_ms", 0)),
        )


@dataclass
class ImpedanceProfile:
    normal_N_per_mm: Tuple[float, float]     # (min, max)
    tangential_N_per_mm: Tuple[float, float] # (min, max)


@dataclass
class ContactPlan:
    """Concrete contact execution plan (bounded by safety envelopes)."""
    target: Pose
    contact_normal: Vector3
    peak_force_N: float
    dwell_ms: int
    approach_speed_mps: float
    release_speed_mps: float
    impedance: ImpedanceProfile
    rationale: str = ""
    consent_mode: ConsentMode = ConsentMode.NONE

    def validate(self) -> None:
        assert self.peak_force_N >= 0.0, "peak_force_N must be >= 0"
        assert 0 <= self.dwell_ms <= 10000, "dwell_ms out of bounds"
        assert 0 < self.approach_speed_mps <= 1.0, "approach_speed_mps out of safe range"
        assert 0 < self.release_speed_mps <= 1.0, "release_speed_mps out of safe range"
        lo_n, hi_n = self.impedance.normal_N_per_mm
        lo_t, hi_t = self.impedance.tangential_N_per_mm
        for lo, hi, name in [(lo_n, hi_n, "normal_N_per_mm"), (lo_t, hi_t, "tangential_N_per_mm")]:
            assert 0.0 <= lo <= hi, f"impedance {name} invalid (min <= max required)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target.to_dict(),
            "normal": self.contact_normal.as_list(),
            "peak_force_N": float(self.peak_force_N),
            "dwell_ms": int(self.dwell_ms),
            "approach_speed_mps": float(self.approach_speed_mps),
            "release_speed_mps": float(self.release_speed_mps),
            "impedance": {
                "normal_N_per_mm": list(self.impedance.normal_N_per_mm),
                "tangential_N_per_mm": list(self.impedance.tangential_N_per_mm),
            },
            "rationale": self.rationale,
            "consent_mode": self.consent_mode.value,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ContactPlan":
        imp = d.get("impedance", {})
        profile = ImpedanceProfile(
            normal_N_per_mm=tuple(map(float, imp.get("normal_N_per_mm", [0.3, 0.6]))),   # spec defaults
            tangential_N_per_mm=tuple(map(float, imp.get("tangential_N_per_mm", [0.1, 0.3]))),
        )
        plan = ContactPlan(
            target=Pose.from_dict(d["target"]),
            contact_normal=Vector3.from_list(d.get("normal", [0.0, 0.0, 1.0])),
            peak_force_N=float(d.get("peak_force_N", 1.0)),
            dwell_ms=int(d.get("dwell_ms", 1500)),
            approach_speed_mps=float(d.get("approach_speed_mps", 0.15)),
            release_speed_mps=float(d.get("release_speed_mps", 0.2)),
            impedance=profile,
            rationale=str(d.get("rationale", "")),
            consent_mode=ConsentMode(d.get("consent_mode", "none")),
        )
        plan.validate()
        return plan


@dataclass
class ContactExecutionLog:
    """Minimal, PII-minimized execution record for auditing."""
    event: str = "contact"
    target: str = "shoulder"
    force_peak_N: float = 0.0
    dwell_ms: int = 0
    consent_mode: ConsentMode = ConsentMode.NONE
    veto_triggered: bool = False
    hash_video: Optional[str] = None
    faces_blurred: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "target": self.target,
            "force_peak_N": float(self.force_peak_N),
            "dwell_ms": int(self.dwell_ms),
            "consent_mode": self.consent_mode.value,
            "veto_triggered": bool(self.veto_triggered),
            "hash_video": self.hash_video,
            "faces_blurred": bool(self.faces_blurred),
            "timestamp": self.timestamp,
        }


@dataclass
class RestTargets:
    """3D rest targets for each fingertip (body frame `B` by convention)."""
    frame: str = "B"
    index_tip: Vector3 = field(default_factory=lambda: Vector3(+0.18, +0.12, +0.85))
    middle_tip: Vector3 = field(default_factory=lambda: Vector3(+0.17, +0.10, +0.85))
    ring_tip: Vector3 = field(default_factory=lambda: Vector3(+0.16, +0.08, +0.85))
    little_tip: Vector3 = field(default_factory=lambda: Vector3(+0.15, +0.06, +0.85))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "index_tip": self.index_tip.as_list(),
            "middle_tip": self.middle_tip.as_list(),
            "ring_tip": self.ring_tip.as_list(),
            "little_tip": self.little_tip.as_list(),
        }


# ------------------------- #
#     UTILITY FUNCTIONS     #
# ------------------------- #

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(val: float, lo: float, hi: float) -> float:
    assert lo <= hi, "invalid clamp bounds"
    return hi if val > hi else lo if val < lo else val


def validate_priority(p: float) -> float:
    return clamp(float(p), 0.0, 1.0)


# ------------------------- #
#          EXPORTS          #
# ------------------------- #

__all__ = [
    "OHIP_SCHEMAS_VERSION",
    # enums
    "SafetyLevel", "HazardClass", "ConsentMode", "ConsentSource", "NudgeLevel",
    # primitives
    "Vector3", "RPY", "Pose",
    # core messages
    "ConsentRecord", "SafetyMapCell", "Nudge",
    "ImpedanceProfile", "ContactPlan", "ContactExecutionLog",
    "RestTargets",
    # utils
    "now_utc_iso", "clamp", "validate_priority",
]
