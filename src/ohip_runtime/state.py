"""
Runtime state models for IX-HapticSight.

This module introduces explicit runtime/session ownership structures without
changing the existing protocol core in ``src/ohip``. The goal is to make
interaction flow, fault latching, and runtime health visible before adding
coordinator or backend code.

This module is intentionally backend-agnostic and ROS-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Optional

from ohip.schemas import SafetyLevel


class InteractionState(str, Enum):
    """
    High-level runtime interaction states.

    These states are intentionally conservative and align with the repository's
    documented approach / verify / contact / retreat / safe-hold semantics.
    """

    IDLE = "IDLE"
    VERIFY = "VERIFY"
    APPROACH = "APPROACH"
    PRECONTACT = "PRECONTACT"
    CONTACT = "CONTACT"
    RETREAT = "RETREAT"
    SAFE_HOLD = "SAFE_HOLD"
    FAULT_LATCHED = "FAULT_LATCHED"


class ExecutionState(str, Enum):
    """
    Backend-facing execution states.

    These are kept separate from interaction states so a reviewer can see
    whether the system is waiting on policy, executing motion, retreating,
    or faulted at the runtime layer.
    """

    IDLE = "IDLE"
    READY = "READY"
    EXECUTING = "EXECUTING"
    ABORTING = "ABORTING"
    RETREATING = "RETREATING"
    SAFE_HOLD = "SAFE_HOLD"
    FAULTED = "FAULTED"
    UNAVAILABLE = "UNAVAILABLE"


class FaultSeverity(str, Enum):
    INFO = "INFO"
    DEGRADED = "DEGRADED"
    BLOCKING = "BLOCKING"
    ABORT = "ABORT"
    CRITICAL = "CRITICAL"


class FaultDisposition(str, Enum):
    """
    What the runtime is expected to do in response to a fault.
    """

    LOG_ONLY = "LOG_ONLY"
    NARROW_BEHAVIOR = "NARROW_BEHAVIOR"
    REJECT_ACTION = "REJECT_ACTION"
    ABORT = "ABORT"
    RETREAT = "RETREAT"
    SAFE_HOLD = "SAFE_HOLD"
    LATCH = "LATCH"


class RuntimeHealth(str, Enum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    FAULTED = "FAULTED"


@dataclass(frozen=True)
class RuntimeFault:
    """
    Structured runtime fault record.

    This is not yet a full event-log object; it is a lightweight runtime model
    suitable for coordinators, tests, and future event serialization.
    """

    fault_id: str
    reason_code: str
    severity: FaultSeverity
    disposition: FaultDisposition
    source: str
    latched: bool = False
    requires_abort: bool = False
    requires_retreat: bool = False
    requires_safe_hold: bool = False
    created_at_utc_s: float = field(default_factory=time)
    details: str = ""

    def blocks_new_actions(self) -> bool:
        return self.severity in {
            FaultSeverity.BLOCKING,
            FaultSeverity.ABORT,
            FaultSeverity.CRITICAL,
        } or self.latched

    def runtime_health(self) -> RuntimeHealth:
        if self.latched or self.severity == FaultSeverity.CRITICAL:
            return RuntimeHealth.FAULTED
        if self.severity == FaultSeverity.ABORT:
            return RuntimeHealth.FAULTED
        if self.severity == FaultSeverity.BLOCKING:
            return RuntimeHealth.BLOCKED
        if self.severity == FaultSeverity.DEGRADED:
            return RuntimeHealth.DEGRADED
        return RuntimeHealth.NOMINAL


@dataclass
class SignalFreshness:
    """
    Snapshot of whether safety-relevant signal classes are currently fresh.

    The runtime will eventually derive this from actual sensing interfaces.
    For now, it provides a clean contract for coordinator logic and tests.
    """

    force_torque_fresh: bool = False
    tactile_fresh: bool = False
    proximity_fresh: bool = False
    thermal_fresh: bool = False
    scene_fresh: bool = False

    def all_required_fresh(
        self,
        *,
        require_force_torque: bool = False,
        require_tactile: bool = False,
        require_proximity: bool = False,
        require_thermal: bool = False,
        require_scene: bool = False,
    ) -> bool:
        checks = [
            (require_force_torque, self.force_torque_fresh),
            (require_tactile, self.tactile_fresh),
            (require_proximity, self.proximity_fresh),
            (require_thermal, self.thermal_fresh),
            (require_scene, self.scene_fresh),
        ]
        return all(actual for required, actual in checks if required)


@dataclass
class InteractionSession:
    """
    Runtime-owned interaction session snapshot.

    This object is intentionally small and explicit. It does not replace the
    canonical OHIP schemas; it tracks the runtime's current authority, state,
    and safety posture for one interaction session.
    """

    session_id: str
    subject_id: Optional[str] = None
    interaction_state: InteractionState = InteractionState.IDLE
    execution_state: ExecutionState = ExecutionState.IDLE
    runtime_health: RuntimeHealth = RuntimeHealth.NOMINAL
    safety_level: SafetyLevel = SafetyLevel.YELLOW
    active_plan_id: Optional[str] = None
    active_fault: Optional[RuntimeFault] = None
    signal_freshness: SignalFreshness = field(default_factory=SignalFreshness)
    consent_valid: bool = False
    consent_fresh: bool = False
    last_transition_utc_s: float = field(default_factory=time)
    last_update_utc_s: float = field(default_factory=time)

    def set_interaction_state(self, state: InteractionState) -> None:
        self.interaction_state = state
        now = time()
        self.last_transition_utc_s = now
        self.last_update_utc_s = now

    def set_execution_state(self, state: ExecutionState) -> None:
        self.execution_state = state
        self.last_update_utc_s = time()

    def apply_fault(self, fault: RuntimeFault) -> None:
        """
        Apply a fault conservatively to the session snapshot.

        This method updates runtime health and pushes the interaction /
        execution state toward safer, more explicit outcomes.
        """
        self.active_fault = fault
        self.runtime_health = fault.runtime_health()
        self.last_update_utc_s = time()

        if fault.latched or fault.disposition == FaultDisposition.LATCH:
            self.interaction_state = InteractionState.FAULT_LATCHED
            self.execution_state = ExecutionState.FAULTED
            self.last_transition_utc_s = self.last_update_utc_s
            return

        if fault.requires_safe_hold or fault.disposition == FaultDisposition.SAFE_HOLD:
            self.interaction_state = InteractionState.SAFE_HOLD
            self.execution_state = ExecutionState.SAFE_HOLD
            self.last_transition_utc_s = self.last_update_utc_s
            return

        if fault.requires_retreat or fault.disposition == FaultDisposition.RETREAT:
            self.interaction_state = InteractionState.RETREAT
            self.execution_state = ExecutionState.RETREATING
            self.last_transition_utc_s = self.last_update_utc_s
            return

        if fault.requires_abort or fault.disposition == FaultDisposition.ABORT:
            self.execution_state = ExecutionState.ABORTING
            self.last_transition_utc_s = self.last_update_utc_s
            return

    def clear_non_latched_fault(self) -> bool:
        """
        Clear the active fault only when it is not latched.

        Returns True if a fault was cleared.
        """
        if self.active_fault is None:
            return False
        if self.active_fault.latched:
            return False
        self.active_fault = None
        self.runtime_health = RuntimeHealth.NOMINAL
        self.last_update_utc_s = time()
        return True

    def can_begin_approach(self) -> bool:
        """
        Conservative gate for beginning an approach action.

        This does not replace the consent manager or safety gate. It provides
        a runtime-side summary check that higher-level coordinators can use.
        """
        if self.active_fault and self.active_fault.blocks_new_actions():
            return False
        if not self.consent_valid or not self.consent_fresh:
            return False
        if self.safety_level == SafetyLevel.RED:
            return False
        if self.runtime_health in {RuntimeHealth.BLOCKED, RuntimeHealth.FAULTED}:
            return False
        return self.interaction_state in {
            InteractionState.IDLE,
            InteractionState.VERIFY,
        }

    def mark_updated(self) -> None:
        self.last_update_utc_s = time()


__all__ = [
    "InteractionState",
    "ExecutionState",
    "FaultSeverity",
    "FaultDisposition",
    "RuntimeHealth",
    "RuntimeFault",
    "SignalFreshness",
    "InteractionSession",
]
