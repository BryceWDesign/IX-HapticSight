"""
High-level runtime service for IX-HapticSight.

This module connects the major backend-agnostic runtime pieces introduced in
the upgrade so far:

- SessionStore
- RuntimeCoordinator
- EventRecorder
- ExecutionAdapter

The goal is to provide one explicit service layer that:
- loads and updates session state
- evaluates a runtime request
- records the full decision trail
- submits bounded execution requests when allowed
- records execution status in the same structured event stream

This is still not a ROS 2 runtime and not a hardware runtime.
It is a disciplined orchestration layer for local execution, replay, and tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ohip.contact_planner import PlannerHints
from ohip.schemas import Nudge, Pose

from ohip_interfaces.execution_adapter import (
    BoundedExecutionRequest,
    ExecutionAdapter,
    ExecutionCommandKind,
    ExecutionResponse,
    ExecutionResultStatus,
)
from ohip_logging.recorder import EventRecorder

from .coordinator import RuntimeCoordinator
from .requests import CoordinationDecision, InteractionRequest
from .session_store import SessionStore
from .state import ExecutionState, InteractionSession, InteractionState


@dataclass(frozen=True)
class RuntimeServiceResult:
    """
    Result bundle for one handled runtime request.
    """

    session: InteractionSession
    decision: CoordinationDecision
    execution_response: Optional[ExecutionResponse] = None

    @property
    def executed(self) -> bool:
        return self.execution_response is not None and bool(self.execution_response.accepted)


class RuntimeService:
    """
    High-level runtime orchestration service.

    The service is intentionally conservative:
    - session state is stored explicitly
    - the coordinator remains the source of decision logic
    - the execution adapter may reject requests it cannot honor
    - event recording happens in the same request flow
    """

    def __init__(
        self,
        *,
        session_store: SessionStore,
        coordinator: RuntimeCoordinator,
        recorder: EventRecorder,
        execution_adapter: Optional[ExecutionAdapter] = None,
    ) -> None:
        self._sessions = session_store
        self._coordinator = coordinator
        self._recorder = recorder
        self._execution = execution_adapter

    def upsert_session(self, session: InteractionSession) -> InteractionSession:
        return self._sessions.upsert(session)

    def get_session(self, session_id: str) -> Optional[InteractionSession]:
        return self._sessions.get(session_id)

    def require_session(self, session_id: str) -> InteractionSession:
        return self._sessions.require(session_id)

    def handle_request(
        self,
        *,
        request: InteractionRequest,
        nudge: Optional[Nudge] = None,
        profile_name: Optional[str] = None,
        hints: Optional[PlannerHints] = None,
        start_pose: Optional[Pose] = None,
    ) -> RuntimeServiceResult:
        """
        Evaluate and optionally execute one runtime request.

        Flow:
        1. load session
        2. coordinator decides
        3. recorder logs request / decision cycle
        4. coordinator mutates session conservatively
        5. optional execution submission when executable
        6. recorder logs fault and/or execution state
        7. updated session is persisted
        """
        session = self._sessions.require(request.session_id)

        decision = self._coordinator.decide(
            session=session,
            request=request,
            nudge=nudge,
            profile_name=profile_name,
            hints=hints,
            start_pose=start_pose,
        )

        self._recorder.record_decision_cycle(
            session=session,
            request=request,
            decision=decision,
            persist=True,
        )

        before_interaction = session.interaction_state
        before_execution = session.execution_state

        self._coordinator.apply_decision_to_session(
            session=session,
            decision=decision,
        )

        self._record_session_side_effects(
            session=session,
            request_id=request.request_id,
            previous_interaction_state=before_interaction,
            previous_execution_state=before_execution,
            reason_code=decision.reason_code,
        )

        execution_response: Optional[ExecutionResponse] = None

        if decision.executable and self._execution is not None and decision.planning is not None:
            exec_request = BoundedExecutionRequest(
                request_id=request.request_id,
                session_id=session.session_id,
                command_kind=ExecutionCommandKind.PLAN,
                safety_level=decision.safety.safety_level,
                plan=decision.planning.plan,
                max_speed_scale=1.0,
                timeout_s=3.0,
                reason_code=decision.reason_code,
            )
            execution_response = self._execution.submit(exec_request)

            prev_interaction = session.interaction_state
            prev_execution = session.execution_state

            self._apply_execution_response_to_session(
                session=session,
                response=execution_response,
            )

            if (
                session.interaction_state != prev_interaction
                or session.execution_state != prev_execution
            ):
                self._recorder.record_state_transition(
                    event_id=f"{request.request_id}:post_submit_transition",
                    session_id=session.session_id,
                    from_interaction_state=prev_interaction,
                    to_interaction_state=session.interaction_state,
                    from_execution_state=prev_execution,
                    to_execution_state=session.execution_state,
                    runtime_health=session.runtime_health,
                    reason_code=execution_response.reason_code or "execution_submitted",
                    persist=True,
                )

            self._recorder.record_execution_status(
                event_id=f"{request.request_id}:execution_submit",
                session=session,
                request_id=request.request_id,
                reason_code=execution_response.reason_code or execution_response.status.value.lower(),
                accepted=execution_response.accepted,
                backend_status=execution_response.status.value,
                progress=1.0 if execution_response.status in {
                    ExecutionResultStatus.ABORTED,
                    ExecutionResultStatus.SAFE_HOLD,
                    ExecutionResultStatus.COMPLETED,
                } else 0.0,
                persist=True,
            )

        persisted = self._sessions.update(session)
        return RuntimeServiceResult(
            session=persisted,
            decision=decision,
            execution_response=execution_response,
        )

    def abort_session(self, *, session_id: str, reason_code: str = "") -> Optional[ExecutionResponse]:
        if self._execution is None:
            return None

        session = self._sessions.require(session_id)
        previous_interaction = session.interaction_state
        previous_execution = session.execution_state

        response = self._execution.abort(session_id=session_id, reason_code=reason_code)
        self._apply_execution_response_to_session(session=session, response=response)

        if (
            session.interaction_state != previous_interaction
            or session.execution_state != previous_execution
        ):
            self._recorder.record_state_transition(
                event_id=f"{session_id}:abort_transition",
                session_id=session_id,
                from_interaction_state=previous_interaction,
                to_interaction_state=session.interaction_state,
                from_execution_state=previous_execution,
                to_execution_state=session.execution_state,
                runtime_health=session.runtime_health,
                reason_code=response.reason_code or "abort",
                persist=True,
            )

        self._recorder.record_execution_status(
            event_id=f"{session_id}:abort_execution_status",
            session=session,
            request_id=response.request_id or None,
            reason_code=response.reason_code or "abort",
            accepted=response.accepted,
            backend_status=response.status.value,
            progress=1.0 if response.accepted else 0.0,
            persist=True,
        )
        self._sessions.update(session)
        return response

    def safe_hold_session(self, *, session_id: str, reason_code: str = "") -> Optional[ExecutionResponse]:
        if self._execution is None:
            return None

        session = self._sessions.require(session_id)
        previous_interaction = session.interaction_state
        previous_execution = session.execution_state

        response = self._execution.safe_hold(session_id=session_id, reason_code=reason_code)
        self._apply_execution_response_to_session(session=session, response=response)

        if (
            session.interaction_state != previous_interaction
            or session.execution_state != previous_execution
        ):
            self._recorder.record_state_transition(
                event_id=f"{session_id}:safe_hold_transition",
                session_id=session_id,
                from_interaction_state=previous_interaction,
                to_interaction_state=session.interaction_state,
                from_execution_state=previous_execution,
                to_execution_state=session.execution_state,
                runtime_health=session.runtime_health,
                reason_code=response.reason_code or "safe_hold",
                persist=True,
            )

        self._recorder.record_execution_status(
            event_id=f"{session_id}:safe_hold_execution_status",
            session=session,
            request_id=response.request_id or None,
            reason_code=response.reason_code or "safe_hold",
            accepted=response.accepted,
            backend_status=response.status.value,
            progress=1.0 if response.accepted else 0.0,
            persist=True,
        )
        self._sessions.update(session)
        return response

    def _record_session_side_effects(
        self,
        *,
        session: InteractionSession,
        request_id: str,
        previous_interaction_state: InteractionState,
        previous_execution_state: ExecutionState,
        reason_code: str,
    ) -> None:
        if (
            session.interaction_state != previous_interaction_state
            or session.execution_state != previous_execution_state
        ):
            self._recorder.record_state_transition(
                event_id=f"{request_id}:session_transition",
                session_id=session.session_id,
                from_interaction_state=previous_interaction_state,
                to_interaction_state=session.interaction_state,
                from_execution_state=previous_execution_state,
                to_execution_state=session.execution_state,
                runtime_health=session.runtime_health,
                reason_code=reason_code,
                persist=True,
            )

        if session.active_fault is not None:
            self._recorder.record_fault(
                session=session,
                fault=session.active_fault,
                persist=True,
            )

    @staticmethod
    def _apply_execution_response_to_session(
        *,
        session: InteractionSession,
        response: ExecutionResponse,
    ) -> None:
        """
        Reflect immediate execution-adapter response into the runtime session.
        """
        if response.status == ExecutionResultStatus.ACCEPTED:
            session.execution_state = ExecutionState.READY
            session.runtime_health = session.runtime_health
        elif response.status == ExecutionResultStatus.RUNNING:
            session.execution_state = ExecutionState.EXECUTING
        elif response.status == ExecutionResultStatus.RETREATING:
            session.interaction_state = InteractionState.RETREAT
            session.execution_state = ExecutionState.RETREATING
        elif response.status == ExecutionResultStatus.SAFE_HOLD:
            session.interaction_state = InteractionState.SAFE_HOLD
            session.execution_state = ExecutionState.SAFE_HOLD
        elif response.status == ExecutionResultStatus.ABORTED:
            session.execution_state = ExecutionState.ABORTING
        elif response.status == ExecutionResultStatus.FAULTED:
            session.interaction_state = InteractionState.FAULT_LATCHED
            session.execution_state = ExecutionState.FAULTED
        elif response.status == ExecutionResultStatus.UNAVAILABLE:
            session.execution_state = ExecutionState.UNAVAILABLE

        session.mark_updated()


__all__ = [
    "RuntimeServiceResult",
    "RuntimeService",
]
