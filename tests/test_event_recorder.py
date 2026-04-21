"""
IX-HapticSight — Tests for the high-level event recorder.

These tests verify that EventRecorder can:
- buffer structured events in memory
- persist them to JSONL logs
- record canonical decision cycles in order
- capture fault, transition, and execution status events
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import (  # noqa: E402
    ContactPlan,
    ConsentMode,
    Pose,
    RPY,
    SafetyLevel,
    Vector3,
)
from ohip_runtime.requests import (  # noqa: E402
    ConsentAssessment,
    CoordinationDecision,
    DecisionStatus,
    InteractionKind,
    InteractionRequest,
    PlanningOutcome,
    RequestSource,
    SafetyAssessment,
)
from ohip_runtime.state import (  # noqa: E402
    ExecutionState,
    FaultDisposition,
    FaultSeverity,
    InteractionSession,
    InteractionState,
    RuntimeFault,
    RuntimeHealth,
)
from ohip_logging.events import EventKind  # noqa: E402
from ohip_logging.jsonl import load_event_log  # noqa: E402
from ohip_logging.recorder import EventRecorder  # noqa: E402


POSE_TARGET = Pose(
    frame="W",
    xyz=Vector3(0.42, -0.18, 1.36),
    rpy=RPY(0.0, 0.0, 1.57),
)


def make_session() -> InteractionSession:
    return InteractionSession(
        session_id="sess-1",
        subject_id="person-1",
        interaction_state=InteractionState.VERIFY,
        execution_state=ExecutionState.READY,
        runtime_health=RuntimeHealth.NOMINAL,
        safety_level=SafetyLevel.GREEN,
        consent_valid=True,
        consent_fresh=True,
    )


def make_request() -> InteractionRequest:
    return InteractionRequest(
        request_id="req-1",
        session_id="sess-1",
        subject_id="person-1",
        interaction_kind=InteractionKind.SUPPORT_CONTACT,
        source=RequestSource.OPERATOR,
        target_name="shoulder",
        requested_scope="shoulder_contact",
        requires_contact=True,
    )


def make_plan() -> ContactPlan:
    return ContactPlan(
        contact_zone="shoulder_contact",
        target=POSE_TARGET,
        normal=Vector3(0.0, 0.8, 0.6),
        peak_force_N=1.2,
        dwell_ms=1500,
        approach_speed_mps=0.15,
        release_speed_mps=0.20,
        impedance={
            "normal_N_per_mm": [0.3, 0.6],
            "tangential_N_per_mm": [0.1, 0.3],
        },
        rationale="test support contact",
        consent_mode=ConsentMode.EXPLICIT,
    )


def make_decision() -> CoordinationDecision:
    consent = ConsentAssessment(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        consent_mode=ConsentMode.EXPLICIT,
        consent_valid=True,
        consent_fresh=True,
        scope_allowed=True,
        reason_code="consent_ok",
    )
    safety = SafetyAssessment(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        safety_level=SafetyLevel.GREEN,
        may_approach=True,
        may_contact=True,
        requires_retreat=False,
        requires_safe_hold=False,
        reason_code="safety_ok",
    )
    planning = PlanningOutcome(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        reason_code="plan_ready",
        plan=make_plan(),
        degraded=False,
    )
    return CoordinationDecision(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        reason_code="consent_ok | safety_ok | plan_ready",
        consent=consent,
        safety=safety,
        planning=planning,
    )


def test_event_recorder_buffers_single_request_event():
    recorder = EventRecorder()
    request = make_request()

    event = recorder.record_request(request, persist=False)

    assert event.kind == EventKind.REQUEST_RECEIVED
    assert len(recorder.buffer()) == 1
    assert recorder.buffer()[0].event_id == "req-1:request"


def test_event_recorder_records_decision_cycle_in_order():
    recorder = EventRecorder()
    session = make_session()
    request = make_request()
    decision = make_decision()

    events = recorder.record_decision_cycle(
        session=session,
        request=request,
        decision=decision,
        persist=False,
    )

    assert len(events) == 5
    assert [event.kind for event in events] == [
        EventKind.REQUEST_RECEIVED,
        EventKind.CONSENT_EVALUATED,
        EventKind.SAFETY_EVALUATED,
        EventKind.PLAN_CREATED,
        EventKind.COORDINATION_DECIDED,
    ]

    buffered = recorder.buffer()
    assert len(buffered) == 5
    assert buffered[-1].reason_code == "consent_ok | safety_ok | plan_ready"


def test_event_recorder_records_fault_transition_and_execution_status():
    recorder = EventRecorder()
    session = make_session()
    session.active_plan_id = "req-1"

    fault = RuntimeFault(
        fault_id="fault-1",
        reason_code="overforce",
        severity=FaultSeverity.ABORT,
        disposition=FaultDisposition.RETREAT,
        source="safety",
        requires_retreat=True,
    )
    session.apply_fault(fault)

    fault_event = recorder.record_fault(session=session, fault=fault, persist=False)
    assert fault_event.kind == EventKind.RETREAT_STATUS

    transition_event = recorder.record_state_transition(
        event_id="evt-transition-1",
        session_id=session.session_id,
        from_interaction_state=InteractionState.VERIFY,
        to_interaction_state=InteractionState.RETREAT,
        from_execution_state=ExecutionState.READY,
        to_execution_state=ExecutionState.RETREATING,
        runtime_health=RuntimeHealth.FAULTED,
        reason_code="overforce",
        persist=False,
    )
    assert transition_event.kind == EventKind.STATE_TRANSITION

    execution_event = recorder.record_execution_status(
        event_id="evt-exec-1",
        session=session,
        request_id="req-1",
        reason_code="retreat_started",
        accepted=True,
        backend_status="running",
        progress=0.4,
        persist=False,
    )
    assert execution_event.kind == EventKind.EXECUTION_STATUS
    assert execution_event.details["progress"] == 0.4

    assert len(recorder.buffer()) == 3


def test_event_recorder_persists_to_jsonl_log():
    session = make_session()
    request = make_request()
    decision = make_decision()

    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "runtime_events.jsonl"
        recorder = EventRecorder.from_path(log_path)

        recorder.record_decision_cycle(
            session=session,
            request=request,
            decision=decision,
            persist=True,
        )

        assert log_path.exists() is True

        loaded = load_event_log(log_path)
        assert len(loaded) == 5
        assert loaded[0].kind == EventKind.REQUEST_RECEIVED
        assert loaded[-1].kind == EventKind.COORDINATION_DECIDED


def test_persist_buffer_writes_buffered_events_without_clearing():
    session = make_session()
    request = make_request()
    decision = make_decision()

    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "buffered_runtime_events.jsonl"
        recorder = EventRecorder.from_path(log_path)

        recorder.record_decision_cycle(
            session=session,
            request=request,
            decision=decision,
            persist=False,
        )

        assert len(recorder.buffer()) == 5
        assert log_path.exists() is False

        written = recorder.persist_buffer()
        assert written == 5

        loaded = load_event_log(log_path)
        assert len(loaded) == 5
        assert len(recorder.buffer()) == 5

        recorder.clear_buffer()
        assert recorder.buffer() == []
