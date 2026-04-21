"""
In-memory simulated execution adapter for IX-HapticSight.

This adapter is intentionally simple and deterministic. Its purpose is to:
- exercise the execution adapter contract in tests
- provide a backend-agnostic placeholder for local runtime integration
- support replay and benchmark scaffolding before any ROS 2 or hardware bridge

It does not perform real motion planning or physics.
It simulates execution state transitions in a conservative, inspectable way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Dict, Optional

from .execution_adapter import (
    BoundedExecutionRequest,
    ExecutionAdapter,
    ExecutionBackendCapabilities,
    ExecutionCommandKind,
    ExecutionResponse,
    ExecutionResultStatus,
    ExecutionUpdate,
)


@dataclass
class _SessionExecutionState:
    session_id: str
    request_id: str
    backend_execution_id: str
    status: ExecutionResultStatus
    progress: float = 0.0
    reason_code: str = ""
    last_update_utc_s: float = field(default_factory=time)


class SimulatedExecutionAdapter(ExecutionAdapter):
    """
    Deterministic in-memory adapter that implements the ExecutionAdapter
    contract without talking to real hardware or middleware.
    """

    def __init__(
        self,
        *,
        backend_name: str = "simulated-execution",
        support_pose_targets: bool = True,
        support_plan_execution: bool = True,
        support_progress_updates: bool = True,
    ) -> None:
        self._caps = ExecutionBackendCapabilities(
            backend_name=backend_name,
            supports_plan_execution=support_plan_execution,
            supports_pose_targets=support_pose_targets,
            supports_abort=True,
            supports_retreat=True,
            supports_safe_hold=True,
            supports_progress_updates=support_progress_updates,
            supports_collision_aware_execution=False,
            supports_velocity_scaling=True,
            supports_force_limited_execution=False,
        )
        self._sessions: Dict[str, _SessionExecutionState] = {}
        self._counter = 0

    def capabilities(self) -> ExecutionBackendCapabilities:
        return self._caps

    def submit(self, request: BoundedExecutionRequest) -> ExecutionResponse:
        request.validate()

        if request.command_kind == ExecutionCommandKind.PLAN and not self._caps.supports_plan_execution:
            return self._reject(request, "plan_execution_not_supported")
        if request.command_kind == ExecutionCommandKind.POSE_TARGET and not self._caps.supports_pose_targets:
            return self._reject(request, "pose_target_not_supported")

        self._counter += 1
        backend_execution_id = f"{self._caps.backend_name}:{self._counter}"

        status = ExecutionResultStatus.ACCEPTED
        progress = 0.0

        if request.command_kind == ExecutionCommandKind.RETREAT:
            status = ExecutionResultStatus.RETREATING
        elif request.command_kind == ExecutionCommandKind.SAFE_HOLD:
            status = ExecutionResultStatus.SAFE_HOLD
            progress = 1.0
        elif request.command_kind == ExecutionCommandKind.ABORT:
            status = ExecutionResultStatus.ABORTED
            progress = 1.0

        self._sessions[request.session_id] = _SessionExecutionState(
            session_id=request.session_id,
            request_id=request.request_id,
            backend_execution_id=backend_execution_id,
            status=status,
            progress=progress,
            reason_code=request.reason_code,
        )

        return ExecutionResponse(
            request_id=request.request_id,
            session_id=request.session_id,
            status=status,
            accepted=True,
            backend_name=self._caps.backend_name,
            reason_code=request.reason_code or "accepted",
            backend_execution_id=backend_execution_id,
        )

    def current_update(self, *, session_id: str) -> Optional[ExecutionUpdate]:
        state = self._sessions.get(session_id)
        if state is None:
            return None
        return ExecutionUpdate(
            request_id=state.request_id,
            session_id=state.session_id,
            status=state.status,
            backend_name=self._caps.backend_name,
            progress=state.progress,
            reason_code=state.reason_code,
            backend_execution_id=state.backend_execution_id,
            created_at_utc_s=state.last_update_utc_s,
        )

    def abort(self, *, session_id: str, reason_code: str = "") -> ExecutionResponse:
        state = self._sessions.get(session_id)
        if state is None:
            return ExecutionResponse(
                request_id="",
                session_id=session_id,
                status=ExecutionResultStatus.UNAVAILABLE,
                accepted=False,
                backend_name=self._caps.backend_name,
                reason_code=reason_code or "unknown_session",
                backend_execution_id=None,
            )

        state.status = ExecutionResultStatus.ABORTED
        state.progress = 1.0
        state.reason_code = reason_code or "aborted"
        state.last_update_utc_s = time()

        return ExecutionResponse(
            request_id=state.request_id,
            session_id=session_id,
            status=ExecutionResultStatus.ABORTED,
            accepted=True,
            backend_name=self._caps.backend_name,
            reason_code=state.reason_code,
            backend_execution_id=state.backend_execution_id,
        )

    def safe_hold(self, *, session_id: str, reason_code: str = "") -> ExecutionResponse:
        state = self._sessions.get(session_id)
        if state is None:
            return ExecutionResponse(
                request_id="",
                session_id=session_id,
                status=ExecutionResultStatus.UNAVAILABLE,
                accepted=False,
                backend_name=self._caps.backend_name,
                reason_code=reason_code or "unknown_session",
                backend_execution_id=None,
            )

        state.status = ExecutionResultStatus.SAFE_HOLD
        state.progress = 1.0
        state.reason_code = reason_code or "safe_hold"
        state.last_update_utc_s = time()

        return ExecutionResponse(
            request_id=state.request_id,
            session_id=session_id,
            status=ExecutionResultStatus.SAFE_HOLD,
            accepted=True,
            backend_name=self._caps.backend_name,
            reason_code=state.reason_code,
            backend_execution_id=state.backend_execution_id,
        )

    def advance(
        self,
        *,
        session_id: str,
        progress: float,
        complete: bool = False,
        fault: bool = False,
        reason_code: str = "",
    ) -> ExecutionUpdate:
        """
        Advance one simulated session for tests or benchmark scaffolding.

        Rules:
        - progress is clamped to [0, 1]
        - fault=True forces FAULTED
        - complete=True forces COMPLETED
        - SAFE_HOLD and ABORTED remain terminal
        """
        state = self._sessions.get(session_id)
        if state is None:
            raise KeyError(f"unknown session_id: {session_id}")

        if state.status in {
            ExecutionResultStatus.ABORTED,
            ExecutionResultStatus.SAFE_HOLD,
            ExecutionResultStatus.FAULTED,
            ExecutionResultStatus.COMPLETED,
        }:
            return self.current_update(session_id=session_id)  # type: ignore[return-value]

        state.progress = max(0.0, min(1.0, float(progress)))
        state.last_update_utc_s = time()

        if fault:
            state.status = ExecutionResultStatus.FAULTED
            state.reason_code = reason_code or "faulted"
        elif complete or state.progress >= 1.0:
            state.status = ExecutionResultStatus.COMPLETED
            state.progress = 1.0
            state.reason_code = reason_code or "completed"
        elif state.status == ExecutionResultStatus.ACCEPTED:
            state.status = ExecutionResultStatus.RUNNING
            state.reason_code = reason_code or "running"
        else:
            state.reason_code = reason_code or state.reason_code or "running"

        return ExecutionUpdate(
            request_id=state.request_id,
            session_id=state.session_id,
            status=state.status,
            backend_name=self._caps.backend_name,
            progress=state.progress,
            reason_code=state.reason_code,
            backend_execution_id=state.backend_execution_id,
            created_at_utc_s=state.last_update_utc_s,
        )

    def _reject(self, request: BoundedExecutionRequest, reason_code: str) -> ExecutionResponse:
        return ExecutionResponse(
            request_id=request.request_id,
            session_id=request.session_id,
            status=ExecutionResultStatus.REJECTED,
            accepted=False,
            backend_name=self._caps.backend_name,
            reason_code=reason_code,
            backend_execution_id=None,
        )


__all__ = [
    "SimulatedExecutionAdapter",
]
