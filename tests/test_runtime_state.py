"""
IX-HapticSight — Tests for runtime state models.

These tests cover the new backend-agnostic runtime session layer introduced
under `src/ohip_runtime/`. The goal is to verify that conservative runtime
state transitions behave predictably before any ROS 2 or execution backend
integration is added.
"""

import os
import sys

# Make both `ohip` and `ohip_runtime` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

from ohip.schemas import SafetyLevel  # noqa: E402
from ohip_runtime.state import (  # noqa: E402
    ExecutionState,
    FaultDisposition,
    FaultSeverity,
    InteractionSession,
    InteractionState,
    RuntimeFault,
    RuntimeHealth,
    SignalFreshness,
)


def test_signal_freshness_all_required_fresh():
    freshness = SignalFreshness(
        force_torque_fresh=True,
        tactile_fresh=False,
        proximity_fresh=True,
        thermal_fresh=True,
        scene_fresh=True,
    )

    assert freshness.all_required_fresh(
        require_force_torque=True,
        require_proximity=True,
        require_thermal=True,
        require_scene=True,
    ) is True

    assert freshness.all_required_fresh(
        require_force_torque=True,
        require_tactile=True,
    ) is False


def test_runtime_fault_health_mapping():
    degraded = RuntimeFault(
        fault_id="f1",
        reason_code="sensor_degraded",
        severity=FaultSeverity.DEGRADED,
        disposition=FaultDisposition.NARROW_BEHAVIOR,
        source="test",
    )
    blocking = RuntimeFault(
        fault_id="f2",
        reason_code="consent_missing",
        severity=FaultSeverity.BLOCKING,
        disposition=FaultDisposition.REJECT_ACTION,
        source="test",
    )
    critical = RuntimeFault(
        fault_id="f3",
        reason_code="e_stop",
        severity=FaultSeverity.CRITICAL,
        disposition=FaultDisposition.LATCH,
        source="test",
        latched=True,
    )

    assert degraded.runtime_health() == RuntimeHealth.DEGRADED
    assert blocking.runtime_health() == RuntimeHealth.BLOCKED
    assert critical.runtime_health() == RuntimeHealth.FAULTED


def test_session_can_begin_approach_only_when_conditions_are_good():
    session = InteractionSession(session_id="s-1")
    session.interaction_state = InteractionState.IDLE
    session.safety_level = SafetyLevel.GREEN
    session.consent_valid = True
    session.consent_fresh = True

    assert session.can_begin_approach() is True

    session.interaction_state = InteractionState.CONTACT
    assert session.can_begin_approach() is False

    session.interaction_state = InteractionState.VERIFY
    assert session.can_begin_approach() is True

    session.safety_level = SafetyLevel.RED
    assert session.can_begin_approach() is False


def test_non_latched_blocking_fault_blocks_new_actions_and_can_clear():
    session = InteractionSession(
        session_id="s-2",
        interaction_state=InteractionState.IDLE,
        execution_state=ExecutionState.READY,
        safety_level=SafetyLevel.GREEN,
        consent_valid=True,
        consent_fresh=True,
    )

    fault = RuntimeFault(
        fault_id="f-block",
        reason_code="consent_denied",
        severity=FaultSeverity.BLOCKING,
        disposition=FaultDisposition.REJECT_ACTION,
        source="runtime_coordinator",
    )
    session.apply_fault(fault)

    assert session.active_fault is not None
    assert session.runtime_health == RuntimeHealth.BLOCKED
    assert session.can_begin_approach() is False

    cleared = session.clear_non_latched_fault()
    assert cleared is True
    assert session.active_fault is None
    assert session.runtime_health == RuntimeHealth.NOMINAL


def test_retreat_fault_moves_session_to_retreating():
    session = InteractionSession(
        session_id="s-3",
        interaction_state=InteractionState.CONTACT,
        execution_state=ExecutionState.EXECUTING,
        safety_level=SafetyLevel.GREEN,
        consent_valid=True,
        consent_fresh=True,
    )

    fault = RuntimeFault(
        fault_id="f-retreat",
        reason_code="overforce",
        severity=FaultSeverity.ABORT,
        disposition=FaultDisposition.RETREAT,
        source="safety",
        requires_retreat=True,
    )
    session.apply_fault(fault)

    assert session.interaction_state == InteractionState.RETREAT
    assert session.execution_state == ExecutionState.RETREATING
    assert session.runtime_health == RuntimeHealth.FAULTED


def test_safe_hold_fault_moves_session_to_safe_hold():
    session = InteractionSession(
        session_id="s-4",
        interaction_state=InteractionState.APPROACH,
        execution_state=ExecutionState.EXECUTING,
        safety_level=SafetyLevel.YELLOW,
    )

    fault = RuntimeFault(
        fault_id="f-hold",
        reason_code="backend_unavailable",
        severity=FaultSeverity.ABORT,
        disposition=FaultDisposition.SAFE_HOLD,
        source="execution",
        requires_safe_hold=True,
    )
    session.apply_fault(fault)

    assert session.interaction_state == InteractionState.SAFE_HOLD
    assert session.execution_state == ExecutionState.SAFE_HOLD
    assert session.runtime_health == RuntimeHealth.FAULTED


def test_latched_fault_cannot_be_cleared_and_enters_fault_latched():
    session = InteractionSession(
        session_id="s-5",
        interaction_state=InteractionState.PRECONTACT,
        execution_state=ExecutionState.EXECUTING,
        safety_level=SafetyLevel.YELLOW,
    )

    fault = RuntimeFault(
        fault_id="f-latched",
        reason_code="policy_integrity_failure",
        severity=FaultSeverity.CRITICAL,
        disposition=FaultDisposition.LATCH,
        source="integrity",
        latched=True,
    )
    session.apply_fault(fault)

    assert session.interaction_state == InteractionState.FAULT_LATCHED
    assert session.execution_state == ExecutionState.FAULTED
    assert session.runtime_health == RuntimeHealth.FAULTED

    cleared = session.clear_non_latched_fault()
    assert cleared is False
    assert session.active_fault is not None
