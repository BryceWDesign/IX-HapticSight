"""
High-level event recording helpers for IX-HapticSight.

This module provides a small orchestration layer over the lower-level event
builders and JSONL writer so runtime code can record a coherent event trail
without duplicating event-construction boilerplate everywhere.

The recorder is intentionally narrow:
- it does not own runtime state
- it does not own execution logic
- it does not replace replay or benchmark tooling

Its job is to turn already-known runtime decisions into a structured, durable,
append-oriented event stream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

from ohip_runtime.requests import CoordinationDecision, InteractionRequest
from ohip_runtime.state import (
    ExecutionState,
    InteractionSession,
    InteractionState,
    RuntimeFault,
    RuntimeHealth,
)
from .events import (
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
from .jsonl import EventLogWriter


@dataclass
class EventRecorder:
    """
    Append-oriented structured event recorder.

    The recorder can be used either:
    - with a live JSONL writer for durable artifacts
    - in memory only for tests and benchmark harnesses

    It preserves the exact event order that the caller chooses.
    """

    writer: Optional[EventLogWriter] = None
    _buffer: List[EventRecord] = field(default_factory=list)

    @classmethod
    def from_path(cls, path: str | Path) -> "EventRecorder":
        return cls(writer=EventLogWriter(path))

    def append(self, event: EventRecord, *, persist: bool = True) -> EventRecord:
        """
        Append one event to the in-memory buffer and optionally persist it.
        """
        self._buffer.append(event)
        if persist and self.writer is not None:
            self.writer.append(event)
        return event

    def append_many(
        self,
        events: Iterable[EventRecord],
        *,
        persist: bool = True,
    ) -> list[EventRecord]:
        """
        Append multiple events, preserving caller order.
        """
        appended: list[EventRecord] = []
        for event in events:
            appended.append(self.append(event, persist=persist))
        return appended

    def buffer(self) -> list[EventRecord]:
        """
        Return a shallow copy of the buffered events.
        """
        return list(self._buffer)

    def clear_buffer(self) -> None:
        self._buffer.clear()

    def persist_buffer(self) -> int:
        """
        Persist the current in-memory buffer to the writer without clearing it.

        Returns the number of events written.
        """
        if self.writer is None:
            return 0
        return self.writer.append_many(self._buffer)

    def record_request(self, request: InteractionRequest, *, persist: bool = True) -> EventRecord:
        return self.append(event_from_request(request), persist=persist)

    def record_decision_cycle(
        self,
        *,
        session: InteractionSession,
        request: InteractionRequest,
        decision: CoordinationDecision,
        persist: bool = True,
    ) -> list[EventRecord]:
        """
        Record the canonical event sequence for one decision cycle.

        Sequence:
        1. request received
        2. consent evaluated
        3. safety evaluated
        4. planning outcome, if present
        5. final coordination decision
        """
        events: list[EventRecord] = [
            event_from_request(request),
            event_from_consent_assessment(session, decision.consent),
            event_from_safety_assessment(session, decision.safety),
        ]
        if decision.planning is not None:
            events.append(event_from_planning_outcome(session, decision.planning))
        events.append(event_from_coordination_decision(session, decision))
        return self.append_many(events, persist=persist)

    def record_fault(
        self,
        *,
        session: InteractionSession,
        fault: RuntimeFault,
        persist: bool = True,
    ) -> EventRecord:
        return self.append(event_from_fault(session, fault), persist=persist)

    def record_state_transition(
        self,
        *,
        event_id: str,
        session_id: str,
        from_interaction_state: InteractionState,
        to_interaction_state: InteractionState,
        from_execution_state: ExecutionState,
        to_execution_state: ExecutionState,
        runtime_health: RuntimeHealth,
        reason_code: str,
        persist: bool = True,
    ) -> EventRecord:
        event = state_transition_event(
            event_id=event_id,
            session_id=session_id,
            from_interaction_state=from_interaction_state,
            to_interaction_state=to_interaction_state,
            from_execution_state=from_execution_state,
            to_execution_state=to_execution_state,
            runtime_health=runtime_health,
            reason_code=reason_code,
        )
        return self.append(event, persist=persist)

    def record_execution_status(
        self,
        *,
        event_id: str,
        session: InteractionSession,
        request_id: Optional[str],
        reason_code: str,
        accepted: bool,
        backend_status: str = "",
        progress: float = 0.0,
        persist: bool = True,
    ) -> EventRecord:
        event = execution_status_event(
            event_id=event_id,
            session_id=session.session_id,
            request_id=request_id,
            interaction_state=session.interaction_state,
            execution_state=session.execution_state,
            runtime_health=session.runtime_health,
            reason_code=reason_code,
            safety_level=session.safety_level,
            accepted=accepted,
            backend_status=backend_status,
            progress=progress,
        )
        return self.append(event, persist=persist)


__all__ = [
    "EventRecorder",
]
