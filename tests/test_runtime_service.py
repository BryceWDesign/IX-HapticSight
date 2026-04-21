"""
IX-HapticSight — Tests for the high-level runtime service.

These tests verify that RuntimeService can:
- load and update explicit session state
- record the full decision trail for one request
- submit executable plans to an execution adapter
- persist structured events to JSONL
- handle blocked requests conservatively
- drive abort and safe-hold flows through the same service layer
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Make project packages importable without packaging/install
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
from ohip_interfaces.simulated_execution_adapter import (  # noqa: E402
    SimulatedExecutionAdapter,
)
from ohip_logging.events import EventKind  # noqa: E402
from ohip_logging.jsonl import load_event_log  # noqa: E402
from ohip_logging.recorder import EventRecorder  # noqa: E402
from ohip_runtime.coordinator import RuntimeCoordinator  # noqa: E402
from ohip_runtime.requests import (  # noqa: E402
    InteractionKind,
    InteractionRequest,
    RequestSource,
)
from ohip_runtime.runtime_service import RuntimeService  # noqa: E402
from ohip_runtime.session_store import SessionStore  # noqa: E402
from ohip_runtime.state import (  # noqa: E402
    ExecutionState,
    InteractionSession,
    InteractionState,
    RuntimeHealth,
)


POSE_START = Pose(
    frame="W",
    xyz=Vector3(0.10, 0.00, 1.00),
    rpy=RPY(0.0, 0.0, 0.0),
)

POSE_TARGET = Pose(
    frame="W",
    xyz=Vector3(0.42, -0.18, 1.36),
    rpy=RPY(0.0, 0.0, 1.57),
)


def risk_green(_pose: Pose) -> SafetyLevel:
    return SafetyLevel.GREEN


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


def make_session() -> InteractionSession:
    return InteractionSession(
        session_id="sess-1",
        subject_id="person-1",
        interaction_state=InteractionState.IDLE,
        execution_state=ExecutionState.IDLE,
        runtime_health=RuntimeHealth.NOMINAL,
        safety_level=SafetyLevel.GREEN,
        consent_valid=False,
        consent_fresh=False,
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


def make_nudge() -> Nudge:
    return Nudge(
        level=NudgeLevel.GREEN,
        target=POSE_TARGET,
        normal=Vector3(0.0, 0.8, 0.6),
        rationale="test shoulder support",
        priority=0.9,
        expires_in_ms=500,
    )


def build_service(log_path: Path):
    envelopes = make_envelopes()
    consent_manager = ConsentManager()
    planner = ContactPlanner(envelopes)
    gate = SafetyGate(envelopes)
    coordinator = RuntimeCoordinator(
        consent_manager=consent_manager,
        contact_planner=planner,
        safety_gate=gate,
        risk_query=risk_green,
    )
    store = SessionStore()
    recorder = EventRecorder.from_path(log_path)
    adapter = SimulatedExecutionAdapter()
    service = RuntimeService(
        session_store=store,
        coordinator=coordinator,
        recorder=recorder,
        execution_adapter=adapter,
    )
    return service, consent_manager, recorder, adapter


def test_runtime_service_executes_approved_request_and_logs_events():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "runtime_events.jsonl"
        service, consent_manager, recorder, _adapter = build_service(log_path)

        service.upsert_session(make_session())

        consent_manager.grant_explicit(
            subject_id="person-1",
            scopes=["shoulder_contact"],
            source="verbal",
        )

        result = service.handle_request(
            request=make_contact_request(),
            nudge=make_nudge(),
            start_pose=POSE_START,
        )

        assert result.decision.status.name == "APPROVED"
        assert result.decision.executable is True
        assert result.executed is True
        assert result.execution_response is not None
        assert result.execution_response.accepted is True

        session = service.require_session("sess-1")
        assert session.active_plan_id == "req-contact-1"
        assert session.active_fault is None
        assert session.consent_valid is True
        assert session.consent_fresh is True

        buffered = recorder.buffer()
        assert len(buffered) == 6
        assert [event.kind for event in buffered] == [
            EventKind.REQUEST_RECEIVED,
            EventKind.CONSENT_EVALUATED,
            EventKind.SAFETY_EVALUATED,
            EventKind.PLAN_CREATED,
            EventKind.COORDINATION_DECIDED,
            EventKind.EXECUTION_STATUS,
        ]

        loaded = load_event_log(log_path)
        assert len(loaded) == 6
        assert loaded[-1].kind == EventKind.EXECUTION_STATUS
        assert loaded[-1].details["accepted"] is True
        assert loaded[-1].details["backend_status"] == "ACCEPTED"


def test_runtime_service_blocks_missing_consent_and_records_fault():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "runtime_events_denied.jsonl"
        service, _consent_manager, recorder, _adapter = build_service(log_path)

        service.upsert_session(make_session())

        result = service.handle_request(
            request=make_contact_request(),
            nudge=make_nudge(),
            start_pose=POSE_START,
        )

        assert result.decision.status.name == "DENIED"
        assert result.executed is False
        assert result.execution_response is None

        session = service.require_session("sess-1")
        assert session.active_fault is not None
        assert session.runtime_health == RuntimeHealth.BLOCKED
        assert session.active_fault.reason_code == "consent_missing_or_invalid"

        buffered = recorder.buffer()
        assert len(buffered) == 5
        assert [event.kind for event in buffered] == [
            EventKind.REQUEST_RECEIVED,
            EventKind.CONSENT_EVALUATED,
            EventKind.SAFETY_EVALUATED,
            EventKind.COORDINATION_DECIDED,
            EventKind.FAULT_APPLIED,
        ]

        loaded = load_event_log(log_path)
        assert len(loaded) == 5
        assert loaded[-1].kind == EventKind.FAULT_APPLIED
        assert loaded[-1].reason_code == "consent_missing_or_invalid"


def test_runtime_service_abort_session_records_transition_and_status():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "runtime_abort.jsonl"
        service, consent_manager, recorder, _adapter = build_service(log_path)

        service.upsert_session(make_session())
        consent_manager.grant_explicit(
            subject_id="person-1",
            scopes=["shoulder_contact"],
            source="verbal",
        )

        result = service.handle_request(
            request=make_contact_request(),
            nudge=make_nudge(),
            start_pose=POSE_START,
        )
        assert result.executed is True

        response = service.abort_session(
            session_id="sess-1",
            reason_code="operator_abort",
        )
        assert response is not None
        assert response.accepted is True
        assert response.status.name == "ABORTED"

        session = service.require_session("sess-1")
        assert session.execution_state == ExecutionState.ABORTING

        buffered = recorder.buffer()
        assert buffered[-2].kind == EventKind.STATE_TRANSITION
        assert buffered[-2].reason_code == "operator_abort"
        assert buffered[-1].kind == EventKind.EXECUTION_STATUS
        assert buffered[-1].details["backend_status"] == "ABORTED"


def test_runtime_service_safe_hold_session_records_transition_and_status():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "runtime_safe_hold.jsonl"
        service, consent_manager, recorder, _adapter = build_service(log_path)

        service.upsert_session(make_session())
        consent_manager.grant_explicit(
            subject_id="person-1",
            scopes=["shoulder_contact"],
            source="verbal",
        )

        result = service.handle_request(
            request=make_contact_request(),
            nudge=make_nudge(),
            start_pose=POSE_START,
        )
        assert result.executed is True

        response = service.safe_hold_session(
            session_id="sess-1",
            reason_code="manual_safe_hold",
        )
        assert response is not None
        assert response.accepted is True
        assert response.status.name == "SAFE_HOLD"

        session = service.require_session("sess-1")
        assert session.interaction_state == InteractionState.SAFE_HOLD
        assert session.execution_state == ExecutionState.SAFE_HOLD

        buffered = recorder.buffer()
        assert buffered[-2].kind == EventKind.STATE_TRANSITION
        assert buffered[-2].reason_code == "manual_safe_hold"
        assert buffered[-1].kind == EventKind.EXECUTION_STATUS
        assert buffered[-1].details["backend_status"] == "SAFE_HOLD"
