"""
IX-HapticSight — Tests for structured event creation and JSONL logging.

These tests verify that the new logging layer can:
- build structured event records from runtime objects
- serialize and deserialize event logs safely
- preserve event ordering and core fields for replay/audit use
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Make both `ohip`, `ohip_runtime`, and `ohip_logging` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import (  # noqa: E402
    ContactPlan,
    ConsentMode,
    Nudge,
    NudgeLevel,
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
from ohip_logging.events import (  # noqa: E402
    EventKind,
    EventRecord,
    event_from_consent_assessment,
    event_from_coordination_decision,
    event_from_fault,
    event_from_planning_outcome,
    event_from_request,
    event_from_safety_assessment,
    execution_status_event,
    state_transition_event,
)
from ohip_logging.jsonl import (  # noqa: E402
    EventLogWriter,
    last_event,
    load_event_log,
    tail_event_log,
    write_event_log,
)


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
        max_force_N=1.2,
        dwell_ms=(1000, 3000),
        impedance={
            "normal_N_per_mm": [0.3, 0.6],
            "tangential_N_per_mm": [0.1, 0.3],
        },
        consent_mode=ConsentMode.EXPLICIT,
    )


def make_planning_outcome() -> PlanningOutcome:
    return PlanningOutcome(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        reason_code="plan_ready",
        plan=make_plan(),
        degraded=False,
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
    planning = make_planning_outcome()
    return CoordinationDecision(
        request_id="req-1",
        status=DecisionStatus.APPROVED,
        reason_code="consent_ok | safety_ok | plan_ready",
        consent=consent,
        safety=safety,
        planning=planning,
    )


def test_event_record_roundtrip_dict():
    event = EventRecord(
        event_id="evt-1",
        kind=EventKind.REQUEST_RECEIVED,
        session_id="sess-1",
        request_id="req-1",
        interaction_state="VERIFY",
        execution_state="READY",
        runtime_health="NOMINAL",
        reason_code="request_received",
        details={"foo": "bar", "count": 2},
    )

    data = event.to_dict()
    restored = EventRecord.from_dict(data)

    assert restored.event_id == "evt-1"
    assert restored.kind == EventKind.REQUEST_RECEIVED
    assert restored.session_id == "sess-1"
    assert restored.details["foo"] == "bar"
    assert restored.details["count"] == 2


def test_request_and_decision_events_capture_expected_fields():
    session = make_session()
    request = make_request()
    decision = make_decision()

    req_event = event_from_request(request)
    assert req_event.kind == EventKind.REQUEST_RECEIVED
    assert req_event.details["interaction_kind"] == "SUPPORT_CONTACT"
    assert req_event.details["requires_contact"] is True

    decision_event = event_from_coordination_decision(session, decision)
    assert decision_event.kind == EventKind.COORDINATION_DECIDED
    assert decision_event.reason_code == "consent_ok | safety_ok | plan_ready"
    assert decision_event.details["status"] == "APPROVED"
    assert decision_event.details["executable"] is True
    assert decision_event.details["has_plan"] is True


def test_consent_safety_and_planning_events_capture_status():
    session = make_session()

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
        status=DecisionStatus.REQUIRES_VERIFICATION,
        safety_level=SafetyLevel.YELLOW,
        may_approach=True,
        may_contact=False,
        requires_retreat=False,
        requires_safe_hold=False,
        reason_code="plan_required_before_contact",
    )
    planning = make_planning_outcome()

    consent_event = event_from_consent_assessment(session, consent)
    safety_event = event_from_safety_assessment(session, safety)
    planning_event = event_from_planning_outcome(session, planning)

    assert consent_event.kind == EventKind.CONSENT_EVALUATED
    assert consent_event.details["consent_mode"] == "explicit"

    assert safety_event.kind == EventKind.SAFETY_EVALUATED
    assert safety_event.details["status"] == "REQUIRES_VERIFICATION"
    assert safety_event.details["safety_level"] == "YELLOW"

    assert planning_event.kind == EventKind.PLAN_CREATED
    assert planning_event.details["has_plan"] is True
    assert planning_event.details["plan"]["contact_zone"] == "shoulder_contact"


def test_fault_transition_and_execution_events_capture_runtime_context():
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

    fault_event = event_from_fault(session, fault)
    assert fault_event.kind == EventKind.RETREAT_STATUS
    assert fault_event.reason_code == "overforce"
    assert fault_event.details["severity"] == "ABORT"
    assert fault_event.details["requires_retreat"] is True

    transition_event = state_transition_event(
        event_id="evt-transition-1",
        session_id="sess-1",
        from_interaction_state=InteractionState.VERIFY,
        to_interaction_state=InteractionState.RETREAT,
        from_execution_state=ExecutionState.READY,
        to_execution_state=ExecutionState.RETREATING,
        runtime_health=RuntimeHealth.FAULTED,
        reason_code="overforce",
    )
    assert transition_event.kind == EventKind.STATE_TRANSITION
    assert transition_event.details["from_interaction_state"] == "VERIFY"
    assert transition_event.details["to_execution_state"] == "RETREATING"

    exec_event = execution_status_event(
        event_id="evt-exec-1",
        session_id="sess-1",
        request_id="req-1",
        interaction_state=InteractionState.RETREAT,
        execution_state=ExecutionState.RETREATING,
        runtime_health=RuntimeHealth.FAULTED,
        reason_code="retreat_started",
        safety_level=SafetyLevel.RED,
        accepted=True,
        backend_status="moving",
        progress=0.5,
    )
    assert exec_event.kind == EventKind.EXECUTION_STATUS
    assert exec_event.details["backend_status"] == "moving"
    assert exec_event.details["progress"] == 0.5


def test_jsonl_writer_roundtrip_and_tail():
    session = make_session()
    request = make_request()
    decision = make_decision()

    events = [
        event_from_request(request),
        event_from_consent_assessment(session, decision.consent),
        event_from_safety_assessment(session, decision.safety),
        event_from_planning_outcome(session, decision.planning),
        event_from_coordination_decision(session, decision),
    ]

    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "events.jsonl"
        writer = EventLogWriter(log_path)

        written = writer.append_many(events)
        assert written == 5
        assert writer.exists() is True

        loaded = writer.read_all()
        assert len(loaded) == 5
        assert loaded[0].kind == EventKind.REQUEST_RECEIVED
        assert loaded[-1].kind == EventKind.COORDINATION_DECIDED

        tail = tail_event_log(log_path, limit=2)
        assert len(tail) == 2
        assert tail[0].kind == EventKind.PLAN_CREATED
        assert tail[1].kind == EventKind.COORDINATION_DECIDED

        last = last_event(log_path)
        assert last is not None
        assert last.kind == EventKind.COORDINATION_DECIDED

        writer.clear()
        assert writer.read_all() == []


def test_write_event_log_overwrites_existing_content():
    session = make_session()
    request = make_request()

    initial_events = [event_from_request(request)]
    replacement_events = [
        state_transition_event(
            event_id="evt-transition-2",
            session_id=session.session_id,
            from_interaction_state=InteractionState.IDLE,
            to_interaction_state=InteractionState.VERIFY,
            from_execution_state=ExecutionState.IDLE,
            to_execution_state=ExecutionState.READY,
            runtime_health=RuntimeHealth.NOMINAL,
            reason_code="entered_verify",
        )
    ]

    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "events.jsonl"

        count1 = write_event_log(log_path, initial_events)
        assert count1 == 1
        assert len(load_event_log(log_path)) == 1

        count2 = write_event_log(log_path, replacement_events)
        assert count2 == 1

        loaded = load_event_log(log_path)
        assert len(loaded) == 1
        assert loaded[0].kind == EventKind.STATE_TRANSITION
        assert loaded[0].reason_code == "entered_verify"
