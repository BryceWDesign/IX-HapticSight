"""
IX-HapticSight — Tests for canonical schemas and helpers.

These tests intentionally avoid external deps and package setup by
inserting the project's `src/` into sys.path and importing `ohip.*`.
"""

import os
import sys
from time import time
from datetime import datetime, timezone

# Make `ohip` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import (  # noqa: E402
    SafetyLevel, HazardClass, ConsentMode, ConsentSource, NudgeLevel,
    Vector3, RPY, Pose,
    ConsentRecord, SafetyMapCell, Nudge,
    ImpedanceProfile, ContactPlan, RestTargets,
    clamp, validate_priority
)


def test_consent_record_ttl_active_and_expired():
    now_ts = time()
    ts_iso = datetime.fromtimestamp(now_ts, timezone.utc).isoformat()

    rec = ConsentRecord(
        subject_id="anon",
        mode=ConsentMode.EXPLICIT,
        source=ConsentSource.VERBAL,
        timestamp=ts_iso,
        scope=["shoulder_contact"],
        ttl_s=1,
    )
    assert rec.is_active(now_ts) is True
    # 2 seconds later -> expired
    assert rec.is_active(now_ts + 2.0) is False


def test_safety_map_cell_roundtrip():
    cell = SafetyMapCell(cell=(1, 2, 3),
                         hazard_class=HazardClass.HOT,
                         level=SafetyLevel.YELLOW,
                         updated_ms=42)
    d = cell.to_dict()
    assert d["cell"] == [1, 2, 3]
    assert d["class"] == "hot"
    assert d["level"] == "YELLOW"

    back = SafetyMapCell.from_dict(d)
    assert back.cell == (1, 2, 3)
    assert back.hazard_class == HazardClass.HOT
    assert back.level == SafetyLevel.YELLOW
    assert back.updated_ms == 42


def test_nudge_roundtrip_and_expiry():
    pose = Pose(frame="W", xyz=Vector3(0.1, 0.2, 0.3), rpy=RPY(0.0, 0.0, 1.57))
    n = Nudge(
        level=NudgeLevel.GREEN,
        target=pose,
        normal=Vector3(0.0, 0.8, 0.6),
        rationale="test",
        priority=0.8,
        expires_in_ms=100,
    )
    d = n.to_dict()
    m = Nudge.from_dict(d)
    assert m.level == NudgeLevel.GREEN
    assert m.target.frame == "W"
    assert m.normal.y == 0.8

    # Expiry check: emitted at t=1.000 s, now=1.200 s -> expired (100 ms TTL)
    assert m.is_expired(now_utc_ms=1.2, emitted_ms=1000) is True
    # Not expired at 1.050 s
    assert m.is_expired(now_utc_ms=1.05, emitted_ms=1000) is False


def test_contact_plan_validate_defaults():
    pose = Pose(frame="W", xyz=Vector3(0.4, -0.1, 1.3), rpy=RPY(0.0, 0.0, 1.57))
    plan = ContactPlan.from_dict({
        "target": pose.to_dict(),
        "normal": [0.0, 0.8, 0.6],
        "peak_force_N": 1.0,
        "dwell_ms": 1500,
        "approach_speed_mps": 0.15,
        "release_speed_mps": 0.20,
        "impedance": {
            "normal_N_per_mm": [0.3, 0.6],
            "tangential_N_per_mm": [0.1, 0.3],
        },
        "rationale": "unit-test",
        "consent_mode": "explicit",
    })
    # validate() is called in from_dict(), but call again to ensure idempotence
    plan.validate()
    assert plan.peak_force_N <= 1.2
    assert 1000 <= plan.dwell_ms <= 3000


def test_rest_targets_to_dict_structure():
    rt = RestTargets()
    d = rt.to_dict()
    assert d["frame"] == "B"
    for key in ("index_tip", "middle_tip", "ring_tip", "little_tip"):
        assert key in d and len(d[key]) == 3
        assert all(isinstance(v, (int, float)) for v in d[key])


def test_utils_clamp_and_priority():
    assert clamp(2.0, 0.0, 1.0) == 1.0
    assert clamp(-1.0, 0.0, 1.0) == 0.0
    assert validate_priority(-0.5) == 0.0
    assert validate_priority(1.5) == 1.0
