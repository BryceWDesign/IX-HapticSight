"""
IX-HapticSight — Tests for execution adapter contracts.

These tests verify the backend-agnostic execution request/response models that
sit between runtime coordination and a future concrete backend adapter.
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
    ExecutionBackendCapabilities,
    ExecutionCommandKind,
    ExecutionResponse,
    ExecutionResultStatus,
    ExecutionUpdate,
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


def test_execution_backend_capabilities_to_dict():
    caps = ExecutionBackendCapabilities(
        backend_name="sim-backend",
        supports_plan_execution=True,
        supports_pose_targets=True,
        supports_abort=True,
        supports_retreat=True,
        supports_safe_hold=True,
        supports_progress_updates=True,
        supports_collision_aware_execution=True,
        supports_velocity_scaling=True,
        supports_force_limited_execution=False,
    )

    data = caps.to_dict()

    assert data["backend_name"] == "sim-backend"
    assert data["supports_plan_execution"] is True
    assert data["supports_pose_targets"] is True
    assert data["supports_progress_updates"] is True
    assert data["supports_collision_aware_execution"] is True
    assert data["supports_force_limited_execution"] is False


def test_bounded_execution_request_with_plan_validates_and_serializes():
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

    request.validate()
    data = request.to_dict()

    assert data["request_id"] == "exec-req-1"
    assert data["command_kind"] == "PLAN"
    assert data["safety_level"] == "GREEN"
    assert data["plan"] is not None
    assert data["target_pose"] is None
    assert data["max_speed_scale"] == 0.75
    assert data["timeout_s"] == 3.0
    assert data["reason_code"] == "runtime_approved_plan"


def test_bounded_execution_request_with_pose_target_validates_and_serializes():
    request = BoundedExecutionRequest(
        request_id="exec-req-2",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.POSE_TARGET,
        safety_level=SafetyLevel.YELLOW,
        target_pose=POSE_TARGET,
        max_speed_scale=0.5,
        timeout_s=2.5,
        reason_code="move_to_rest_pose",
    )

    request.validate()
    data = request.to_dict()

    assert data["command_kind"] == "POSE_TARGET"
    assert data["plan"] is None
    assert data["target_pose"] is not None
    assert data["target_pose"]["frame"] == "W"
    assert data["max_speed_scale"] == 0.5


def test_abort_and_safe_hold_requests_can_omit_plan_and_pose():
    abort_request = BoundedExecutionRequest(
        request_id="exec-abort-1",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.ABORT,
        safety_level=SafetyLevel.RED,
        reason_code="hazard_abort",
    )
    safe_hold_request = BoundedExecutionRequest(
        request_id="exec-hold-1",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.SAFE_HOLD,
        safety_level=SafetyLevel.RED,
        reason_code="backend_unavailable",
    )

    abort_request.validate()
    safe_hold_request.validate()

    assert abort_request.to_dict()["plan"] is None
    assert safe_hold_request.to_dict()["target_pose"] is None


def test_retreat_request_requires_plan_or_target_pose():
    bad_request = BoundedExecutionRequest(
        request_id="exec-retreat-bad",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.RETREAT,
        safety_level=SafetyLevel.RED,
        reason_code="retreat_required",
    )

    try:
        bad_request.validate()
        raised = False
    except ValueError:
        raised = True

    assert raised is True


def test_pose_target_request_requires_target_pose():
    bad_request = BoundedExecutionRequest(
        request_id="exec-pose-bad",
        session_id="sess-1",
        command_kind=ExecutionCommandKind.POSE_TARGET,
        safety_level=SafetyLevel.YELLOW,
        reason_code="missing_pose",
    )

    try:
        bad_request.validate()
        raised = False
    except ValueError:
        raised = True

    assert raised is True


def test_request_rejects_both_plan_and_pose_and_invalid_scalars():
    try:
        BoundedExecutionRequest(
            request_id="exec-bad-both",
            session_id="sess-1",
            command_kind=ExecutionCommandKind.PLAN,
            safety_level=SafetyLevel.GREEN,
            plan=make_plan(),
            target_pose=POSE_TARGET,
            reason_code="bad_both",
        ).validate()
        raised_both = False
    except ValueError:
        raised_both = True

    try:
        BoundedExecutionRequest(
            request_id="exec-bad-speed",
            session_id="sess-1",
            command_kind=ExecutionCommandKind.PLAN,
            safety_level=SafetyLevel.GREEN,
            plan=make_plan(),
            max_speed_scale=0.0,
            reason_code="bad_speed",
        ).validate()
        raised_speed = False
    except ValueError:
        raised_speed = True

    try:
        BoundedExecutionRequest(
            request_id="exec-bad-timeout",
            session_id="sess-1",
            command_kind=ExecutionCommandKind.PLAN,
            safety_level=SafetyLevel.GREEN,
            plan=make_plan(),
            timeout_s=0.0,
            reason_code="bad_timeout",
        ).validate()
        raised_timeout = False
    except ValueError:
        raised_timeout = True

    assert raised_both is True
    assert raised_speed is True
    assert raised_timeout is True


def test_execution_response_to_dict():
    response = ExecutionResponse(
        request_id="exec-req-1",
        session_id="sess-1",
        status=ExecutionResultStatus.ACCEPTED,
        accepted=True,
        backend_name="sim-backend",
        reason_code="accepted_for_execution",
        backend_execution_id="sim-123",
    )

    data = response.to_dict()

    assert data["status"] == "ACCEPTED"
    assert data["accepted"] is True
    assert data["backend_name"] == "sim-backend"
    assert data["backend_execution_id"] == "sim-123"


def test_execution_update_validate_and_to_dict():
    update = ExecutionUpdate(
        request_id="exec-req-1",
        session_id="sess-1",
        status=ExecutionResultStatus.RUNNING,
        backend_name="sim-backend",
        progress=0.4,
        reason_code="moving",
        backend_execution_id="sim-123",
    )

    update.validate()
    data = update.to_dict()

    assert data["status"] == "RUNNING"
    assert data["progress"] == 0.4
    assert data["reason_code"] == "moving"
    assert data["backend_execution_id"] == "sim-123"

    try:
        ExecutionUpdate(
            request_id="exec-req-1",
            session_id="sess-1",
            status=ExecutionResultStatus.RUNNING,
            backend_name="sim-backend",
            progress=1.5,
        ).validate()
        raised = False
    except ValueError:
        raised = True

    assert raised is True
