"""
IX-HapticSight — Tests for the runtime coordinator layer.

These tests verify that the new backend-agnostic runtime coordinator:
- respects consent for contact requests
- produces executable decisions only when consent + safety + planning align
- blocks RED safety targets
- pushes the session toward safer runtime states when denied
"""

import os
import sys

# Make both `ohip` and `ohip_runtime` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.consent_manager import ConsentManager  # noqa: E402
from ohip.contact_planner import ContactPlanner  # noqa: E402
from ohip.safety_gate import SafetyGate  # noqa: E402
from ohip.schemas import (  # noqa: E402
    Nudge,
    NudgeLevel,
    Pose,
    RPY,
    SafetyLevel,
    Vector3,
)
from ohip_runtime.coordinator import RuntimeCoordinator  # noqa: E402
from ohip_runtime.requests import (  # noqa: E402
    DecisionStatus,
    InteractionKind,
    InteractionRequest,
    RequestSource,
)
from ohip_runtime.state import (  # noqa: E402
    InteractionSession,
    InteractionState,
)


POSE_START = Pose(frame="W", xyz=Vector3(0.10, 0.00, 1.00), rpy=RPY(0.0, 0.0, 0.0))
POSE_SHOULDER = Pose(frame="W", xyz=Vector3(0.42, -0.18, 1.36), rpy=RPY(0.0, 0.0, 1.57))


def risk_green(_pose: Pose) -> SafetyLevel:
    return SafetyLevel.GREEN


def risk_red(_pose: Pose) -> SafetyLevel:
    return SafetyLevel.RED


def make_envelopes() -> dict:
    return {
        "defaults": {
            "social_touch_profile": "default_social",
        },
        "profiles": {
            "default_social": {
                "max_force_N": 1.2,
                "dwell_ms_min": 1000,
                "dwell_ms_max": 3000,
                "approach_speed_mps": 0.15,
                "release_speed_mps": 0.20,
                "impedance": {
                    "normal_N_per_mm": [0.3, 0.6],
                    "tangential_N_per_mm": [0.1, 0.3],
                },
            }
        },
        "safety": {
            "red_stop_ms": 100,
        },
    }


def make_runtime() -> RuntimeCoordinator:
    envelopes = make_envelopes()
    consent = ConsentManager()
    planner = ContactPlanner(envelopes)
    gate = SafetyGate(envelopes)
    return RuntimeCoordinator(
        consent_manager=consent,
        contact_planner=planner,
        safety_gate=gate,
        risk_query=risk_green,
    )


def make_session() -> InteractionSession:
    return InteractionSession(
        session_id="sess-1",
        subject_id="person-1",
        interaction_state=InteractionState.IDLE,
        safety_level=SafetyLevel.GREEN,
    )


def make_contact_request() -> InteractionRequest:
    return InteractionRequest(
        request_id="req-contact-1",
        session_id="sess-1",
        subject_id="person-1",
        interaction_kind=InteractionKind.SUPPORT_CONTACT,
        source=RequestSource.OPERATOR,
        target_name="shoulder",
        requested_scope="shoulder_contact",
        requires_contact=True,
    )


def make_approach_request() -> InteractionRequest:
    return InteractionRequest(
        request_id="req-approach-1",
        session_id="sess-1",
        subject_id="person-1",
        interaction_kind=InteractionKind.APPROACH_ONLY,
        source=RequestSource.OPERATOR,
        target_name="shoulder",
        requested_scope="shoulder_contact",
        requires_contact=False,
    )


def make_nudge() -> Nudge:
    return Nudge(
        level=NudgeLevel.GREEN,
        target=POSE_SHOULDER,
        normal=Vector3(0.0, 0.8, 0.6),
        rationale="test shoulder support",
        priority=0.9,
        expires_in_ms=500,
    )


def test_contact_request_without_consent_is_denied():
    runtime = make_runtime()
    session = make_session()
    request = make_contact_request()

    decision = runtime.decide(
        session=session,
        request=request,
        nudge=make_nudge(),
        start_pose=POSE_START,
    )

    assert decision.status == DecisionStatus.DENIED
    assert decision.executable is False
    assert decision.consent.consent_valid is False
    assert "consent_missing_or_invalid" in decision.reason_code


def test_contact_request_with_explicit_consent_is_executable():
    runtime = make_runtime()
    session = make_session()
    request = make_contact_request()

    runtime._consent.grant_explicit(
        subject_id="person-1",
        scopes=["shoulder_contact"],
        source="verbal",
    )

    decision = runtime.decide(
        session=session,
        request=request,
        nudge=make_nudge(),
        start_pose=POSE_START,
    )

    assert decision.status == DecisionStatus.APPROVED
    assert decision.executable is True
    assert decision.consent.consent_valid is True
    assert decision.consent.scope_allowed is True
    assert decision.safety.may_contact is True
    assert decision.planning is not None
    assert decision.planning.plan is not None

    runtime.apply_decision_to_session(session=session, decision=decision)
    assert session.active_plan_id == request.request_id
    assert session.active_fault is None


def test_red_target_veto_blocks_contact_even_with_consent():
    envelopes = make_envelopes()
    consent = ConsentManager()
    planner = ContactPlanner(envelopes)
    gate = SafetyGate(envelopes)
    runtime = RuntimeCoordinator(
        consent_manager=consent,
        contact_planner=planner,
        safety_gate=gate,
        risk_query=risk_red,
    )

    session = make_session()
    request = make_contact_request()

    consent.grant_explicit(
        subject_id="person-1",
        scopes=["shoulder_contact"],
        source="verbal",
    )

    decision = runtime.decide(
        session=session,
        request=request,
        nudge=make_nudge(),
        start_pose=POSE_START,
    )

    assert decision.status == DecisionStatus.DENIED
    assert decision.executable is False
    assert decision.safety.safety_level == SafetyLevel.RED
    assert "target RED" in decision.reason_code


def test_latched_safety_gate_pushes_session_to_safe_hold():
    runtime = make_runtime()
    session = make_session()
    request = make_approach_request()

    runtime._safety.trip("manual_trip_for_test")

    decision = runtime.decide(
        session=session,
        request=request,
        nudge=make_nudge(),
        start_pose=POSE_START,
    )

    assert decision.status == DecisionStatus.DENIED
    assert decision.safety.requires_safe_hold is True

    runtime.apply_decision_to_session(session=session, decision=decision)
    assert session.interaction_state == InteractionState.SAFE_HOLD
    assert session.active_fault is not None
    assert session.active_fault.requires_safe_hold is True
