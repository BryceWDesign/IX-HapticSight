"""
Execution adapter contracts for IX-HapticSight.

This module defines backend-agnostic execution interfaces that sit between:
- runtime coordination / planning
and
- a concrete simulator, middleware bridge, or robot controller adapter

The goal is to keep execution transport replaceable without weakening the
authority of consent, safety, or bounded planning logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Optional

from ohip.schemas import ContactPlan, Pose, SafetyLevel


class ExecutionCommandKind(str, Enum):
    """
    High-level command classes that the runtime may ask an execution backend
    to honor.
    """

    PLAN = "PLAN"
    POSE_TARGET = "POSE_TARGET"
    ABORT = "ABORT"
    RETREAT = "RETREAT"
    SAFE_HOLD = "SAFE_HOLD"


class ExecutionResultStatus(str, Enum):
    """
    Normalized execution result / state values exposed by an adapter.
    """

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    RETREATING = "RETREATING"
    SAFE_HOLD = "SAFE_HOLD"
    FAULTED = "FAULTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ExecutionBackendCapabilities:
    """
    Small capability summary for one execution backend.

    This is intentionally conservative. It helps runtime code understand what
    the backend claims to support without embedding backend-specific logic in
    the protocol core.
    """

    backend_name: str
    supports_plan_execution: bool = False
    supports_pose_targets: bool = False
    supports_abort: bool = True
    supports_retreat: bool = True
    supports_safe_hold: bool = True
    supports_progress_updates: bool = False
    supports_collision_aware_execution: bool = False
    supports_velocity_scaling: bool = True
    supports_force_limited_execution: bool = False

    def to_dict(self) -> dict:
        return {
            "backend_name": self.backend_name,
            "supports_plan_execution": bool(self.supports_plan_execution),
            "supports_pose_targets": bool(self.supports_pose_targets),
            "supports_abort": bool(self.supports_abort),
            "supports_retreat": bool(self.supports_retreat),
            "supports_safe_hold": bool(self.supports_safe_hold),
            "supports_progress_updates": bool(self.supports_progress_updates),
            "supports_collision_aware_execution": bool(self.supports_collision_aware_execution),
            "supports_velocity_scaling": bool(self.supports_velocity_scaling),
            "supports_force_limited_execution": bool(self.supports_force_limited_execution),
        }


@dataclass(frozen=True)
class BoundedExecutionRequest:
    """
    A runtime-approved execution request.

    Exactly one of `plan` or `target_pose` may be present for motion-like
    commands. Abort / retreat / safe-hold commands may omit both and rely on
    reason codes and backend semantics.
    """

    request_id: str
    session_id: str
    command_kind: ExecutionCommandKind
    safety_level: SafetyLevel
    plan: Optional[ContactPlan] = None
    target_pose: Optional[Pose] = None
    max_speed_scale: float = 1.0
    timeout_s: Optional[float] = None
    reason_code: str = ""
    created_at_utc_s: float = field(default_factory=time)

    def validate(self) -> None:
        if self.max_speed_scale <= 0.0:
            raise ValueError("max_speed_scale must be > 0.0")

        if self.command_kind in {
            ExecutionCommandKind.PLAN,
            ExecutionCommandKind.RETREAT,
        } and self.plan is None and self.target_pose is None:
            raise ValueError(
                "PLAN or RETREAT requests require a plan or target_pose"
            )

        if self.command_kind == ExecutionCommandKind.POSE_TARGET and self.target_pose is None:
            raise ValueError("POSE_TARGET requests require target_pose")

        if self.plan is not None and self.target_pose is not None:
            raise ValueError("request may not include both plan and target_pose")

        if self.timeout_s is not None and self.timeout_s <= 0.0:
            raise ValueError("timeout_s must be > 0.0 when provided")

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "command_kind": self.command_kind.value,
            "safety_level": self.safety_level.value,
            "plan": None if self.plan is None else self.plan.to_dict(),
            "target_pose": None if self.target_pose is None else self.target_pose.to_dict(),
            "max_speed_scale": float(self.max_speed_scale),
            "timeout_s": None if self.timeout_s is None else float(self.timeout_s),
            "reason_code": self.reason_code,
            "created_at_utc_s": float(self.created_at_utc_s),
        }


@dataclass(frozen=True)
class ExecutionResponse:
    """
    Immediate adapter response to an execution request.
    """

    request_id: str
    session_id: str
    status: ExecutionResultStatus
    accepted: bool
    backend_name: str
    reason_code: str = ""
    backend_execution_id: Optional[str] = None
    created_at_utc_s: float = field(default_factory=time)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "accepted": bool(self.accepted),
            "backend_name": self.backend_name,
            "reason_code": self.reason_code,
            "backend_execution_id": self.backend_execution_id,
            "created_at_utc_s": float(self.created_at_utc_s),
        }


@dataclass(frozen=True)
class ExecutionUpdate:
    """
    Periodic or terminal execution status update from an adapter.
    """

    request_id: str
    session_id: str
    status: ExecutionResultStatus
    backend_name: str
    progress: float = 0.0
    reason_code: str = ""
    backend_execution_id: Optional[str] = None
    created_at_utc_s: float = field(default_factory=time)

    def validate(self) -> None:
        if self.progress < 0.0 or self.progress > 1.0:
            raise ValueError("progress must be between 0.0 and 1.0")

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "backend_name": self.backend_name,
            "progress": float(self.progress),
            "reason_code": self.reason_code,
            "backend_execution_id": self.backend_execution_id,
            "created_at_utc_s": float(self.created_at_utc_s),
        }


class ExecutionAdapter(ABC):
    """
    Abstract contract for runtime execution backends.

    Design rules:
    - execution may reject a request it cannot honor safely
    - execution may not expand the authority of the request
    - abort and safe-hold paths must remain explicit
    - status reporting should be structured and replay-friendly
    """

    @abstractmethod
    def capabilities(self) -> ExecutionBackendCapabilities:
        """
        Return a summary of backend capabilities.
        """
        raise NotImplementedError

    @abstractmethod
    def submit(self, request: BoundedExecutionRequest) -> ExecutionResponse:
        """
        Submit a bounded execution request to the backend.
        """
        raise NotImplementedError

    @abstractmethod
    def current_update(self, *, session_id: str) -> Optional[ExecutionUpdate]:
        """
        Return the most recent execution update for a session, if any.
        """
        raise NotImplementedError

    @abstractmethod
    def abort(self, *, session_id: str, reason_code: str = "") -> ExecutionResponse:
        """
        Ask the backend to abort execution for a session.
        """
        raise NotImplementedError

    @abstractmethod
    def safe_hold(self, *, session_id: str, reason_code: str = "") -> ExecutionResponse:
        """
        Ask the backend to enter safe hold for a session.
        """
        raise NotImplementedError


__all__ = [
    "ExecutionCommandKind",
    "ExecutionResultStatus",
    "ExecutionBackendCapabilities",
    "BoundedExecutionRequest",
    "ExecutionResponse",
    "ExecutionUpdate",
    "ExecutionAdapter",
]
