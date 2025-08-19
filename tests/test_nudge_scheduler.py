"""
IX-HapticSight — Tests for EngagementScheduler behavior.

Covers:
- Consent gates (YELLOW without consent, GREEN with explicit consent)
- Debounce (suppress identical nudges within window)
- Social cooldown (blocks human-touch nudges, allows object nudges)
- Safety-map filtering (RED targets are ignored)
- Ranking preference (shoulder prioritized on distress)
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Make `ohip` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.nudge_scheduler import (  # noqa: E402
    EngagementScheduler,
    PolicyProfile,
)
from ohip.schemas import (  # noqa: E402
    Pose, Vector3, RPY,
    ConsentRecord, ConsentMode, ConsentSource,
    SafetyLevel,
)


# Utility poses reused across tests
POSE_SHOULDER = Pose(frame="W", xyz=Vector3(0.42, -0.18, 1.36), rpy=RPY(0.0, 0.0, 1.57))
POSE_TABLE = Pose(frame="W", xyz=Vector3(0.80, 0.10, 0.90), rpy=RPY(0.0, 0.0, 0.0))


def risk_green(_pose: Pose) -> SafetyLevel:
    return SafetyLevel.GREEN


def risk_red_if_shoulder(p: Pose) -> SafetyLevel:
    # Treat the exact shoulder pose as RED; everything else GREEN.
    if (abs(p.xyz.x - POSE_SHOULDER.xyz.x) < 1e-9 and
        abs(p.xyz.y - POSE_SHOULDER.xyz.y) < 1e-9 and
        abs(p.xyz.z - POSE_SHOULDER.xyz.z) < 1e-9):
        return SafetyLevel.RED
    return SafetyLevel.GREEN


def make_affordances() -> list[dict]:
    return [
        {
            "name": "shoulder",
            "category": "human",
            "pose": POSE_SHOULDER.to_dict(),
            "utility": 0.90,
            "safety_level": "GREEN",
        },
        {
            "name": "flat_surface",
            "category": "object",
            "pose": POSE_TABLE.to_dict(),
            "utility": 0.40,
            "safety_level": "GREEN",
        },
    ]


def explicit_consent(subject="person-1") -> ConsentRecord:
    return ConsentRecord(
        subject_id=subject,
        mode=ConsentMode.EXPLICIT,
        source=ConsentSource.VERBAL,
        scope=["shoulder_contact"],
        ttl_s=60,
    )


def expired_consent(subject="person-1") -> ConsentRecord:
    old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    return ConsentRecord(
        subject_id=subject,
        mode=ConsentMode.EXPLICIT,
        source=ConsentSource.VERBAL,
        timestamp=old,
        scope=["shoulder_contact"],
        ttl_s=60,  # expired by timestamp
    )


def no_consent(subject="person-1") -> ConsentRecord:
    return ConsentRecord(
        subject_id=subject,
        mode=ConsentMode.NONE,
        source=ConsentSource.UI,
        scope=["shoulder_contact"],
        ttl_s=60,
    )


def test_yellow_without_consent():
    policy = PolicyProfile()  # require_explicit_for_social=True by default
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.9}

    nudge = sched.decide(human_state, no_consent(), make_affordances(), risk_green)
    assert nudge is not None
    assert nudge.level.name == "YELLOW"
    assert "Consent required" in nudge.rationale


def test_green_with_explicit_consent():
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.8}

    nudge = sched.decide(human_state, explicit_consent(), make_affordances(), risk_green)
    assert nudge is not None
    assert nudge.level.name == "GREEN"
    # Shoulder should be preferred on distress; rationale reflects that path.
    assert "Shoulder support" in nudge.rationale


def test_expired_consent_behaves_as_yellow():
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.8}

    nudge = sched.decide(human_state, expired_consent(), make_affordances(), risk_green)
    assert nudge is not None
    # Expired → treated as absent under require_explicit_for_social
    assert nudge.level.name in ("YELLOW",)  # requires verification
    assert "Consent required" in nudge.rationale


def test_debounce_blocks_immediate_repeat():
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.8}
    aff = make_affordances()

    n1 = sched.decide(human_state, explicit_consent(), aff, risk_green)
    n2 = sched.decide(human_state, explicit_consent(), aff, risk_green)  # immediate repeat
    assert n1 is not None
    assert n2 is None  # suppressed by debounce window


def test_social_cooldown_blocks_human_allows_object():
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.8}
    aff = make_affordances()

    # First: get a shoulder nudge and mark it executed.
    n1 = sched.decide(human_state, explicit_consent(), aff, risk_green)
    assert n1 is not None and "Shoulder support" in n1.rationale
    sched.notify_contact_executed()

    # Second: within cooldown, shoulder is blocked; object nudge should pass.
    n2 = sched.decide(human_state, explicit_consent(), aff, risk_green)
    assert n2 is not None
    assert "Object interaction" in n2.rationale  # object chosen while shoulder blocked


def test_safety_map_filters_red_targets():
    policy = PolicyProfile()
    sched = EngagementScheduler(policy)
    human_state = {"present": True, "distress": 0.9}
    aff = make_affordances()

    # Risk map marks shoulder corridor/target RED; scheduler must ignore it and pick object.
    nudge = sched.decide(human_state, explicit_consent(), aff, risk_red_if_shoulder)
    assert nudge is not None
    assert "Object interaction" in nudge.rationale  # shoulder filtered out
