"""
IX-HapticSight — Tests for structured event replay helpers.

These tests verify that the replay layer can:
- iterate deterministically through event streams
- slice by session, request, and event kind
- reload from JSONL artifacts
- merge multiple event streams with stable ordering
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
    InteractionRequest,
    InteractionKind,
    PlanningOutcome,
    RequestSource,
    SafetyAssessment,
)
from ohip_runtime.state import (  # noqa: E402
    ExecutionState,
    InteractionSession,
    InteractionState,
    RuntimeHealth,
)
from ohip_logging.events import (  # noqa: E402
    EventKind,
    event_from_consent_assessment,
    event_from_coordination_decision,
    event_from_planning_outcome,
    event_from_request,
    event_from_safety_assessment,
    execution_status_event,
    state_transition_event,
)
from ohip_logging.jsonl import write_event_log  # noqa: E402
from ohip_logging.replay import (  # noqa: E402
    EventReplay,
    ReplayCursor,
    merge_replay_streams,
)


POSE_TARGET = Pose(
    frame="W",
    xyz=Vector3(0.42, -0.18, 1.36),
    rpy=RPY(0.0, 0.0, 1.57),
)


def make_session(session_id: str = "sess-1") -> InteractionSession:
    return InteractionSession(
        session_id=session_id,
        subject_id=f"{session_id}-person",
        interaction_state=InteractionState.VERIFY,
        execution_state=ExecutionState.READY,
        runtime_health=RuntimeHealth.NOMINAL,
        safety_level=SafetyLevel.GREEN,
        consent_valid=True,
        consent_fresh=True,
    )


def make_request(request_id: str = "req-1", session_id: str = "sess-1") -> InteractionRequest:
    return InteractionRequest(
        request_id=request_id,
        session_id=session_id,
        subject_id=f"{session_id}-person",
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


def make_decision(request_id: str = "req-1") -> CoordinationDecision:
    consent = ConsentAssessment(
        request_id=request_id,
        status=DecisionStatus.APPROVED,
        consent_mode=ConsentMode.EXPLICIT,
        consent_valid=True,
        consent_fresh=True,
        scope_allowed=True,
        reason_code="consent_ok",
    )
    safety = SafetyAssessment(
        request_id=request_id,
        status=DecisionStatus.APPROVED,
        safety_level=SafetyLevel.GREEN,
        may_approach=True,
        may_contact=True,
        requires_retreat=False,
        requires_safe_hold=False,
        reason_code="safety_ok",
    )
    planning = PlanningOutcome(
        request_id=request_id,
        status=DecisionStatus.APPROVED,
        reason_code="plan_ready",
        plan=make_plan(),
        degraded=False,
    )
    return CoordinationDecision(
        request_id=request_id,
        status=DecisionStatus.APPROVED,
        reason_code="consent_ok | safety_ok | plan_ready",
        consent=consent,
        safety=safety,
        planning=planning,
    )


def make_event_sequence(session_id: str = "sess-1", request_id: str = "req-1"):
    session = make_session(session_id=session_id)
    request = make_request(request_id=request_id, session_id=session_id)
    decision = make_decision(request_id=request_id)

    return [
        event_from_request(request),
        event_from_consent_assessment(session, decision.consent),
        event_from_safety_assessment(session, decision.safety),
        event_from_planning_outcome(session, decision.planning),
        state_transition_event(
            event_id=f"{request_id}:transition:verify_to_approach",
            session_id=session_id,
            from_interaction_state=InteractionState.VERIFY,
            to_interaction_state=InteractionState.APPROACH,
            from_execution_state=ExecutionState.READY,
            to_execution_state=ExecutionState.READY,
            runtime_health=RuntimeHealth.NOMINAL,
            reason_code="planner_ready",
        ),
        event_from_coordination_decision(session, decision),
        execution_status_event(
            event_id=f"{request_id}:execution:start",
            session_id=session_id,
            request_id=request_id,
            interaction_state=InteractionState.APPROACH,
            execution_state=ExecutionState.EXECUTING,
            runtime_health=RuntimeHealth.NOMINAL,
            reason_code="execution_started",
            safety_level=SafetyLevel.GREEN,
            accepted=True,
            backend_status="running",
            progress=0.25,
        ),
    ]


def test_replay_basic_iteration_and_summary():
    events = make_event_sequence()
    replay = EventReplay(events, source_label="unit-test")

    assert len(replay) == 7
    assert replay.first().kind == EventKind.REQUEST_RECEIVED
    assert replay.last().kind == EventKind.EXECUTION_STATUS

    summary = replay.summary()
    assert summary["source_label"] == "unit-test"
    assert summary["event_count"] == 7
    assert summary["session_ids"] == ["sess-1"]
    assert summary["request_ids"] == ["req-1"]
    assert summary["kind_counts"]["REQUEST_RECEIVED"] == 1
    assert summary["kind_counts"]["COORDINATION_DECIDED"] == 1


def test_replay_cursor_advances_deterministically():
    replay = EventReplay(make_event_sequence())
    cursor = ReplayCursor(index=0)

    kinds = []
    while True:
        event, cursor = replay.next_from(cursor)
        if event is None:
            break
        kinds.append(event.kind.value)

    assert kinds == [
        "REQUEST_RECEIVED",
        "CONSENT_EVALUATED",
        "SAFETY_EVALUATED",
        "PLAN_CREATED",
        "STATE_TRANSITION",
        "COORDINATION_DECIDED",
        "EXECUTION_STATUS",
    ]

    event, same_cursor = replay.next_from(cursor)
    assert event is None
    assert same_cursor.index == cursor.index


def test_replay_filters_by_session_request_and_kind():
    events_a = make_event_sequence(session_id="sess-1", request_id="req-1")
    events_b = make_event_sequence(session_id="sess-2", request_id="req-2")
    replay = EventReplay(events_a + events_b)

    session_slice = replay.by_session("sess-2")
    assert len(session_slice) == 7
    assert session_slice.session_ids() == ["sess-2"]
    assert session_slice.request_ids() == ["req-2"]

    request_slice = replay.by_request("req-1")
    assert len(request_slice) == 7
    assert request_slice.session_ids() == ["sess-1"]

    kinds_slice = replay.by_kind(EventKind.REQUEST_RECEIVED, EventKind.COORDINATION_DECIDED)
    assert len(kinds_slice) == 4
    assert kinds_slice.kinds() == ["REQUEST_RECEIVED", "COORDINATION_DECIDED"]


def test_replay_between_event_ids_returns_contiguous_slice():
    replay = EventReplay(make_event_sequence())
    slice_ = replay.between_event_ids(
        "req-1:consent",
        "req-1:decision",
    )

    assert len(slice_) == 5
    assert slice_.first().kind == EventKind.CONSENT_EVALUATED
    assert slice_.last().kind == EventKind.COORDINATION_DECIDED

    slice_without_end = replay.between_event_ids(
        "req-1:consent",
        "req-1:decision",
        include_end=False,
        name="consent_to_predecision",
    )
    assert len(slice_without_end) == 4
    assert slice_without_end.name == "consent_to_predecision"
    assert slice_without_end.last().kind == EventKind.STATE_TRANSITION


def test_replay_loads_from_jsonl_artifact():
    events = make_event_sequence()

    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "events.jsonl"
        written = write_event_log(log_path, events)
        assert written == 7

        replay = EventReplay.from_jsonl(log_path)
        assert len(replay) == 7
        assert replay.source_label.endswith("events.jsonl")
        assert replay.first().event_id == "req-1:request"
        assert replay.last().event_id == "req-1:execution:start"


def test_merge_replay_streams_orders_by_time_then_event_id():
    stream1 = make_event_sequence(session_id="sess-a", request_id="req-a")
    stream2 = make_event_sequence(session_id="sess-b", request_id="req-b")

    # Force deterministic overlap ordering by timestamp
    e1 = stream1[0]
    e2 = stream2[0]

    event_a = type(e1)(
        event_id="a-event",
        kind=e1.kind,
        session_id=e1.session_id,
        request_id=e1.request_id,
        interaction_state=e1.interaction_state,
        execution_state=e1.execution_state,
        runtime_health=e1.runtime_health,
        reason_code=e1.reason_code,
        created_at_utc_s=1000.0,
        details=e1.details,
    )
    event_b = type(e2)(
        event_id="b-event",
        kind=e2.kind,
        session_id=e2.session_id,
        request_id=e2.request_id,
        interaction_state=e2.interaction_state,
        execution_state=e2.execution_state,
        runtime_health=e2.runtime_health,
        reason_code=e2.reason_code,
        created_at_utc_s=1000.0,
        details=e2.details,
    )

    merged = merge_replay_streams([[event_b], [event_a]], source_label="merged-test")

    assert len(merged) == 2
    assert merged.source_label == "merged-test"
    assert merged.at(0).event_id == "a-event"
    assert merged.at(1).event_id == "b-event"
