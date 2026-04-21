"""
Structured event models for IX-HapticSight.

This module provides replay-safe, backend-agnostic event records for important
runtime behavior such as:

- interaction request handling
- consent decisions
- safety decisions
- planning outcomes
- runtime faults
- state transitions
- execution milestones

The design goal is to preserve enough causal context for later audit and replay
without depending on ad hoc console logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any, Optional

from ohip.schemas import ContactPlan, SafetyLevel
from ohip_runtime.requests import (
    ConsentAssessment,
    CoordinationDecision,
    DecisionStatus,
    InteractionRequest,
    PlanningOutcome,
    SafetyAssessment,
)
from ohip_runtime.state import (
    ExecutionState,
    InteractionSession,
    InteractionState,
    RuntimeFault,
    RuntimeHealth,
)


class EventKind(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    CONSENT_EVALUATED = "CONSENT_EVALUATED"
    SAFETY_EVALUATED = "SAFETY_EVALUATED"
    PLAN_CREATED = "PLAN_CREATED"
    COORDINATION_DECIDED = "COORDINATION_DECIDED"
    STATE_TRANSITION = "STATE_TRANSITION"
    FAULT_APPLIED = "FAULT_APPLIED"
    EXECUTION_STATUS = "EXECUTION_STATUS"
    RETREAT_STATUS = "RETREAT_STATUS"
    SAFE_HOLD_STATUS = "SAFE_HOLD_STATUS"
    BENCHMARK_MARKER = "BENCHMARK_MARKER"
    REPLAY_MARKER = "REPLAY_MARKER"


def _safe_plan_dict(plan: Optional[ContactPlan]) -> Optional[dict[str, Any]]:
    if plan is None:
        return None
    return plan.to_dict()


@dataclass(frozen=True)
class EventRecord:
    """
    Canonical structured event record.

    Notes:
    - `event_id` should be unique within a log or evidence bundle.
    - `reason_code` is intentionally short and machine-friendly.
    - `details` is optional extra context, not a dumping ground for raw payloads.
    """

    event_id: str
    kind: EventKind
    session_id: Optional[str]
    request_id: Optional[str]
    interaction_state: Optional[str]
    execution_state: Optional[str]
    runtime_health: Optional[str]
    reason_code: str
    created_at_utc_s: float = field(default_factory=time)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind.value,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "interaction_state": self.interaction_state,
            "execution_state": self.execution_state,
            "runtime_health": self.runtime_health,
            "reason_code": self.reason_code,
            "created_at_utc_s": float(self.created_at_utc_s),
            "details": dict(self.details),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "EventRecord":
        return EventRecord(
            event_id=str(data["event_id"]),
            kind=EventKind(str(data["kind"])),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            interaction_state=data.get("interaction_state"),
            execution_state=data.get("execution_state"),
            runtime_health=data.get("runtime_health"),
            reason_code=str(data.get("reason_code", "")),
            created_at_utc_s=float(data.get("created_at_utc_s", time())),
            details=dict(data.get("details", {})),
        )


def event_from_request(request: InteractionRequest) -> EventRecord:
    return EventRecord(
        event_id=f"{request.request_id}:request",
        kind=EventKind.REQUEST_RECEIVED,
        session_id=request.session_id,
        request_id=request.request_id,
        interaction_state=None,
        execution_state=None,
        runtime_health=None,
        reason_code="request_received",
        details={
            "interaction_kind": request.interaction_kind.value,
            "source": request.source.value,
            "target_name": request.target_name,
            "requested_scope": request.requested_scope,
            "requires_contact": bool(request.requires_contact),
            "requires_consent_freshness": bool(request.requires_consent_freshness),
            "subject_id": request.subject_id,
            "requested_at_utc_s": float(request.requested_at_utc_s),
            "notes": request.notes,
        },
    )


def event_from_consent_assessment(
    session: InteractionSession,
    assessment: ConsentAssessment,
) -> EventRecord:
    return EventRecord(
        event_id=f"{assessment.request_id}:consent",
        kind=EventKind.CONSENT_EVALUATED,
        session_id=session.session_id,
        request_id=assessment.request_id,
        interaction_state=session.interaction_state.value,
        execution_state=session.execution_state.value,
        runtime_health=session.runtime_health.value,
        reason_code=assessment.reason_code,
        details={
            "status": assessment.status.value,
            "consent_mode": assessment.consent_mode.value,
            "consent_valid": bool(assessment.consent_valid),
            "consent_fresh": bool(assessment.consent_fresh),
            "scope_allowed": bool(assessment.scope_allowed),
            "evaluated_at_utc_s": float(assessment.evaluated_at_utc_s),
        },
    )


def event_from_safety_assessment(
    session: InteractionSession,
    assessment: SafetyAssessment,
) -> EventRecord:
    return EventRecord(
        event_id=f"{assessment.request_id}:safety",
        kind=EventKind.SAFETY_EVALUATED,
        session_id=session.session_id,
        request_id=assessment.request_id,
        interaction_state=session.interaction_state.value,
        execution_state=session.execution_state.value,
        runtime_health=session.runtime_health.value,
        reason_code=assessment.reason_code,
        details={
            "status": assessment.status.value,
            "safety_level": assessment.safety_level.value,
            "may_approach": bool(assessment.may_approach),
            "may_contact": bool(assessment.may_contact),
            "requires_retreat": bool(assessment.requires_retreat),
            "requires_safe_hold": bool(assessment.requires_safe_hold),
            "evaluated_at_utc_s": float(assessment.evaluated_at_utc_s),
        },
    )


def event_from_planning_outcome(
    session: InteractionSession,
    outcome: PlanningOutcome,
) -> EventRecord:
    return EventRecord(
        event_id=f"{outcome.request_id}:plan",
        kind=EventKind.PLAN_CREATED,
        session_id=session.session_id,
        request_id=outcome.request_id,
        interaction_state=session.interaction_state.value,
        execution_state=session.execution_state.value,
        runtime_health=session.runtime_health.value,
        reason_code=outcome.reason_code,
        details={
            "status": outcome.status.value,
            "degraded": bool(outcome.degraded),
            "created_at_utc_s": float(outcome.created_at_utc_s),
            "has_plan": bool(outcome.has_plan),
            "plan": _safe_plan_dict(outcome.plan),
        },
    )


def event_from_coordination_decision(
    session: InteractionSession,
    decision: CoordinationDecision,
) -> EventRecord:
    return EventRecord(
        event_id=f"{decision.request_id}:decision",
        kind=EventKind.COORDINATION_DECIDED,
        session_id=session.session_id,
        request_id=decision.request_id,
        interaction_state=session.interaction_state.value,
        execution_state=session.execution_state.value,
        runtime_health=session.runtime_health.value,
        reason_code=decision.reason_code,
        details={
            "status": decision.status.value,
            "executable": bool(decision.executable),
            "created_at_utc_s": float(decision.created_at_utc_s),
            "consent_status": decision.consent.status.value,
            "safety_status": decision.safety.status.value,
            "planning_status": decision.planning.status.value if decision.planning else None,
            "has_plan": bool(decision.planning.has_plan) if decision.planning else False,
        },
    )


def event_from_fault(
    session: InteractionSession,
    fault: RuntimeFault,
) -> EventRecord:
    kind = EventKind.FAULT_APPLIED
    if fault.requires_retreat:
        kind = EventKind.RETREAT_STATUS
    elif fault.requires_safe_hold:
        kind = EventKind.SAFE_HOLD_STATUS

    return EventRecord(
        event_id=f"{fault.fault_id}:fault",
        kind=kind,
        session_id=session.session_id,
        request_id=session.active_plan_id,
        interaction_state=session.interaction_state.value,
        execution_state=session.execution_state.value,
        runtime_health=session.runtime_health.value,
        reason_code=fault.reason_code,
        details={
            "source": fault.source,
            "severity": fault.severity.value,
            "disposition": fault.disposition.value,
            "latched": bool(fault.latched),
            "requires_abort": bool(fault.requires_abort),
            "requires_retreat": bool(fault.requires_retreat),
            "requires_safe_hold": bool(fault.requires_safe_hold),
            "created_at_utc_s": float(fault.created_at_utc_s),
            "details": fault.details,
        },
    )


def state_transition_event(
    *,
    event_id: str,
    session_id: str,
    from_interaction_state: InteractionState,
    to_interaction_state: InteractionState,
    from_execution_state: ExecutionState,
    to_execution_state: ExecutionState,
    runtime_health: RuntimeHealth,
    reason_code: str,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        kind=EventKind.STATE_TRANSITION,
        session_id=session_id,
        request_id=None,
        interaction_state=to_interaction_state.value,
        execution_state=to_execution_state.value,
        runtime_health=runtime_health.value,
        reason_code=reason_code,
        details={
            "from_interaction_state": from_interaction_state.value,
            "to_interaction_state": to_interaction_state.value,
            "from_execution_state": from_execution_state.value,
            "to_execution_state": to_execution_state.value,
        },
    )


def execution_status_event(
    *,
    event_id: str,
    session_id: str,
    request_id: Optional[str],
    interaction_state: InteractionState,
    execution_state: ExecutionState,
    runtime_health: RuntimeHealth,
    reason_code: str,
    safety_level: SafetyLevel,
    accepted: bool,
    backend_status: str = "",
    progress: float = 0.0,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        kind=EventKind.EXECUTION_STATUS,
        session_id=session_id,
        request_id=request_id,
        interaction_state=interaction_state.value,
        execution_state=execution_state.value,
        runtime_health=runtime_health.value,
        reason_code=reason_code,
        details={
            "safety_level": safety_level.value,
            "accepted": bool(accepted),
            "backend_status": backend_status,
            "progress": float(progress),
        },
    )


__all__ = [
    "EventKind",
    "EventRecord",
    "event_from_request",
    "event_from_consent_assessment",
    "event_from_safety_assessment",
    "event_from_planning_outcome",
    "event_from_coordination_decision",
    "event_from_fault",
    "state_transition_event",
    "execution_status_event",
]
