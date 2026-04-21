"""
IX-HapticSight — Tests for the in-memory simulated execution adapter.

These tests verify that the simulated adapter:
- exposes stable capabilities
- accepts supported bounded execution requests
- tracks per-session execution updates
- supports abort and safe-hold transitions
- rejects unsupported command kinds cleanly
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import (  # noqa: E402
    ConsentMode,
    ContactPlan,
    ImpedanceProfile,
    Pose,
    RPY,
    SafetyLevel,
    Vector3,
)
from ohip_interfaces.execution_adapter import (  # noqa: E402
    BoundedExecutionRequest,
    ExecutionCommandKind,
    ExecutionResultStatus,
)
from ohip_interfaces.simulated_execution_adapter import (  # noqa: E402
    SimulatedExecutionAdapter,
)


POSE_TARGET = Pose(
    frame="W",
    xyz=Vector3(0.42, -0.18, 1.36),
    rpy=RPY(0.0, 0.0, 1.57),
)


def make_plan() -> ContactPlan:
    return ContactPlan(
        target=POSE_TARGET,
        contact_normal=Vector3(0.0, 0.8, 0.6),
        peak_force_N=1.2,
        dwell_ms=1500,
        approach_speed_mps=0.15,
        release_speed_mps=0.20,
        impedance=ImpedanceProfile(
            normal_N_per_mm=(0.3, 0.6),
            tangential_N_per_mm=(0.1, 0.3),
        ),
        rationale="test support contact",
        consent_mode=ConsentMode.EXPLICIT,
    )


def test_simulated_adapter_reports_capabilities():
    adapter = SimulatedExecutionAdapter(
        backend_name="sim-backend",
        support_pose_targets=True,
        support_plan_execution=True,
        support_progress_updates=True,
    )

    caps = adapter.capabilities()

    assert caps.backend_name == "sim-backend"
    assert caps.supports_plan_execution is True
    assert caps.supports_pose_targets is True
    assert caps.supports_abort is True
    assert caps.supports_retreat is True
    assert caps.supports_safe_hold is True
    assert caps.supports_progress_updates is True


def test_submit_plan_request_and_advance_to_completion():
    adapter = SimulatedExecutionAdapter()

    request = BoundedExecutionRequest(
        request_id="exec-req-1",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.PLAN,
        safety_level=SafetyLevel.GREEN,
        plan=make_plan(),
        max_speed_scale=0.75,
        timeout_s=3.0,
        reason_code="runtime_approved_plan",
    )

    response = adapter.submit(request)
    assert response.status == ExecutionResultStatus.ACCEPTED
    assert response.accepted is True
    assert response.backend_execution_id is not None

    update = adapter.current_update(session_id="sess-1")
    assert update is not None
    assert update.status == ExecutionResultStatus.ACCEPTED
    assert update.progress == 0.0

    update = adapter.advance(
        session_id="sess-1",
        progress=0.4,
        reason_code="running",
    )
    assert update.status == ExecutionResultStatus.RUNNING
    assert update.progress == 0.4
    assert update.reason_code == "running"

    update = adapter.advance(
        session_id="sess-1",
        progress=1.0,
        complete=True,
        reason_code="completed",
    )
    assert update.status == ExecutionResultStatus.COMPLETED
    assert update.progress == 1.0
    assert update.reason_code == "completed"


def test_submit_pose_target_request():
    adapter = SimulatedExecutionAdapter()

    request = BoundedExecutionRequest(
        request_id="exec-req-2",
        session_id="sess-2",
        command_kind=ExecutionCommandKind.POSE_TARGET,
        safety_level=SafetyLevel.YELLOW,
        target_pose=POSE_TARGET,
        max_speed_scale=0.5,
        timeout_s=2.0,
        reason_code="move_to_rest_pose",
    )

    response = adapter.submit(request)
    assert response.status == ExecutionResultStatus.ACCEPTED
    assert response.accepted is True

    update = adapter.advance(
        session_id="sess-2",
        progress=0.25,
        reason_code="running",
    )
    assert update.status == ExecutionResultStatus.RUNNING
    assert update.progress == 0.25


def test_retreat_safe_hold_and_abort_requests_become_terminal_states():
    adapter = SimulatedExecutionAdapter()

    retreat_request = BoundedExecutionRequest(
        request_id="exec-retreat-1",
        session_id="sess-3",
        command_kind=ExecutionCommandKind.RETREAT,
        safety_level=SafetyLevel.RED,
        target_pose=POSE_TARGET,
        reason_code="retreat_required",
    )
    retreat_response = adapter.submit(retreat_request)
    assert retreat_response.status == ExecutionResultStatus.RETREATING
    assert retreat_response.accepted is True

    retreat_update = adapter.current_update(session_id="sess-3")
    assert retreat_update is not None
    assert retreat_update.status == ExecutionResultStatus.RETREATING

    hold_request = BoundedExecutionRequest(
        request_id="exec-hold-1",
        session_id="sess-4",
        command_kind=ExecutionCommandKind.SAFE_HOLD,
        safety_level=SafetyLevel.RED,
        reason_code="backend_unavailable",
    )
    hold_response = adapter.submit(hold_request)
    assert hold_response.status == ExecutionResultStatus.SAFE_HOLD
    assert hold_response.accepted is True

    hold_update = adapter.current_update(session_id="sess-4")
    assert hold_update is not None
    assert hold_update.status == ExecutionResultStatus.SAFE_HOLD
    assert hold_update.progress == 1.0

    abort_request = BoundedExecutionRequest(
        request_id="exec-abort-1",
        session_id="sess-5",
        command_kind=ExecutionCommandKind.ABORT,
        safety_level=SafetyLevel.RED,
        reason_code="hazard_abort",
    )
    abort_response = adapter.submit(abort_request)
    assert abort_response.status == ExecutionResultStatus.ABORTED
    assert abort_response.accepted is True

    abort_update = adapter.current_update(session_id="sess-5")
    assert abort_update is not None
    assert abort_update.status == ExecutionResultStatus.ABORTED
    assert abort_update.progress == 1.0


def test_abort_and_safe_hold_can_override_existing_session_state():
    adapter = SimulatedExecutionAdapter()

    request = BoundedExecutionRequest(
        request_id="exec-req-6",
        session_id="sess-6",
        command_kind=ExecutionCommandKind.PLAN,
        safety_level=SafetyLevel.GREEN,
        plan=make_plan(),
        reason_code="runtime_approved_plan",
    )
    adapter.submit(request)

    abort_response = adapter.abort(
        session_id="sess-6",
        reason_code="operator_abort",
    )
    assert abort_response.status == ExecutionResultStatus.ABORTED
    assert abort_response.accepted is True
    assert abort_response.reason_code == "operator_abort"

    update = adapter.current_update(session_id="sess-6")
    assert update is not None
    assert update.status == ExecutionResultStatus.ABORTED
    assert update.progress == 1.0

    # Re-submit to same session and then drive to safe hold.
    adapter.submit(request)
    hold_response = adapter.safe_hold(
        session_id="sess-6",
        reason_code="force_safe_hold",
    )
    assert hold_response.status == ExecutionResultStatus.SAFE_HOLD
    assert hold_response.accepted is True
    assert hold_response.reason_code == "force_safe_hold"

    update = adapter.current_update(session_id="sess-6")
    assert update is not None
    assert update.status == ExecutionResultStatus.SAFE_HOLD
    assert update.progress == 1.0


def test_abort_or_safe_hold_unknown_session_returns_unavailable():
    adapter = SimulatedExecutionAdapter()

    abort_response = adapter.abort(
        session_id="missing-session",
        reason_code="unknown_session_abort",
    )
    assert abort_response.status == ExecutionResultStatus.UNAVAILABLE
    assert abort_response.accepted is False

    hold_response = adapter.safe_hold(
        session_id="missing-session",
        reason_code="unknown_session_hold",
    )
    assert hold_response.status == ExecutionResultStatus.UNAVAILABLE
    assert hold_response.accepted is False


def test_unsupported_command_types_are_rejected():
    no_plan_adapter = SimulatedExecutionAdapter(
        support_plan_execution=False,
        support_pose_targets=True,
    )
    no_pose_adapter = SimulatedExecutionAdapter(
        support_plan_execution=True,
        support_pose_targets=False,
    )

    plan_request = BoundedExecutionRequest(
        request_id="exec-plan-reject",
        session_id="sess-7",
        command_kind=ExecutionCommandKind.PLAN,
        safety_level=SafetyLevel.GREEN,
        plan=make_plan(),
        reason_code="plan_request",
    )
    plan_response = no_plan_adapter.submit(plan_request)
    assert plan_response.status == ExecutionResultStatus.REJECTED
    assert plan_response.accepted is False
    assert plan_response.reason_code == "plan_execution_not_supported"

    pose_request = BoundedExecutionRequest(
        request_id="exec-pose-reject",
        session_id="sess-8",
        command_kind=ExecutionCommandKind.POSE_TARGET,
        safety_level=SafetyLevel.YELLOW,
        target_pose=POSE_TARGET,
        reason_code="pose_request",
    )
    pose_response = no_pose_adapter.submit(pose_request)
    assert pose_response.status == ExecutionResultStatus.REJECTED
    assert pose_response.accepted is False
    assert pose_response.reason_code == "pose_target_not_supported"


def test_advance_can_fault_and_terminal_states_do_not_change_afterward():
    adapter = SimulatedExecutionAdapter()

    request = BoundedExecutionRequest(
        request_id="exec-req-9",
        session_id="sess-9",
        command_kind=ExecutionCommandKind.PLAN,
        safety_level=SafetyLevel.GREEN,
        plan=make_plan(),
        reason_code="runtime_approved_plan",
    )
    adapter.submit(request)

    update = adapter.advance(
        session_id="sess-9",
        progress=0.5,
        fault=True,
        reason_code="backend_fault",
    )
    assert update.status == ExecutionResultStatus.FAULTED
    assert update.progress == 0.5
    assert update.reason_code == "backend_fault"

    later = adapter.advance(
        session_id="sess-9",
        progress=1.0,
        complete=True,
        reason_code="should_not_override_fault",
    )
    assert later.status == ExecutionResultStatus.FAULTED
    assert later.reason_code == "backend_fault"
