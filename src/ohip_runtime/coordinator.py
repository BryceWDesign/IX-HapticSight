"""
Runtime coordinator for IX-HapticSight.

This module provides the first real orchestration layer that sits above the
protocol core in ``src/ohip`` and below any future ROS 2 or backend-specific
transport layer.

The coordinator is intentionally conservative:
- it does not command motion directly
- it does not bypass consent or safety checks
- it does not assume one specific middleware stack
- it does not claim to be a full production runtime

Its job is to turn a runtime request into an explicit coordination decision
using the existing protocol-core components:
- ConsentManager
- ContactPlanner
- SafetyGate
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from ohip.consent_manager import ConsentManager
from ohip.contact_planner import ContactPlanner, PlannerHints
from ohip.safety_gate import SafetyGate
from ohip.schemas import (
    ConsentMode,
    ConsentRecord,
    Nudge,
    SafetyLevel,
)

from .requests import (
    ConsentAssessment,
    CoordinationDecision,
    DecisionStatus,
    InteractionKind,
    InteractionRequest,
    PlanningOutcome,
    SafetyAssessment,
)
from .state import (
    FaultDisposition,
    FaultSeverity,
    InteractionSession,
    RuntimeFault,
)


RiskQuery = Callable[[object], SafetyLevel]


@dataclass(frozen=True)
class CoordinatorConfig:
    """
    Minimal coordinator behavior knobs.

    These are intentionally small at this stage. The coordinator should remain
    understandable and should avoid becoming a hidden policy engine.
    """

    default_contact_scope: str = "shoulder_contact"
    allow_approach_without_contact: bool = True
    allow_verify_without_fresh_consent: bool = True


class RuntimeCoordinator:
    """
    Conservative runtime coordinator.

    This class translates an InteractionRequest into:
    - consent assessment
    - safety assessment
    - optional planning outcome
    - final coordination decision

    The coordinator is intentionally explicit so it can later feed:
    - an execution adapter
    - a structured event logger
    - replay tooling
    - benchmark harnesses
    """

    def __init__(
        self,
        *,
        consent_manager: ConsentManager,
        contact_planner: ContactPlanner,
        safety_gate: SafetyGate,
        risk_query: RiskQuery,
        config: Optional[CoordinatorConfig] = None,
    ) -> None:
        self._consent = consent_manager
        self._planner = contact_planner
        self._safety = safety_gate
        self._risk_query = risk_query
        self._config = config or CoordinatorConfig()

    def assess_consent(
        self,
        *,
        session: InteractionSession,
        request: InteractionRequest,
    ) -> ConsentAssessment:
        """
        Evaluate whether the requested behavior is consent-authorized.

        This method does not mutate the session.
        """
        requested_scopes = self._requested_scopes(request)
        record = self._consent.query(
            subject_id=request.subject_id or "",
            requested_scopes=requested_scopes,
        )

        consent_valid = record.mode != ConsentMode.NONE and bool(record.is_active())
        consent_fresh = bool(record.is_active())
        scope_allowed = consent_valid

        if request.requires_contact:
            if consent_valid and scope_allowed:
                return ConsentAssessment(
                    request_id=request.request_id,
                    status=DecisionStatus.APPROVED,
                    consent_mode=record.mode,
                    consent_valid=True,
                    consent_fresh=consent_fresh,
                    scope_allowed=True,
                    reason_code="consent_ok",
                )

            return ConsentAssessment(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                consent_mode=record.mode,
                consent_valid=consent_valid,
                consent_fresh=consent_fresh,
                scope_allowed=scope_allowed,
                reason_code="consent_missing_or_invalid",
            )

        if request.interaction_kind == InteractionKind.PRECONTACT_VERIFY:
            if consent_valid:
                return ConsentAssessment(
                    request_id=request.request_id,
                    status=DecisionStatus.APPROVED,
                    consent_mode=record.mode,
                    consent_valid=True,
                    consent_fresh=consent_fresh,
                    scope_allowed=scope_allowed,
                    reason_code="consent_ok_for_verify",
                )

            if self._config.allow_verify_without_fresh_consent:
                return ConsentAssessment(
                    request_id=request.request_id,
                    status=DecisionStatus.REQUIRES_VERIFICATION,
                    consent_mode=record.mode,
                    consent_valid=False,
                    consent_fresh=False,
                    scope_allowed=False,
                    reason_code="verify_requires_runtime_confirmation",
                )

        if request.interaction_kind in {
            InteractionKind.OBSERVE_ONLY,
            InteractionKind.APPROACH_ONLY,
        } and self._config.allow_approach_without_contact:
            return ConsentAssessment(
                request_id=request.request_id,
                status=DecisionStatus.APPROVED,
                consent_mode=record.mode,
                consent_valid=consent_valid,
                consent_fresh=consent_fresh,
                scope_allowed=scope_allowed,
                reason_code="no_contact_consent_not_required",
            )

        return ConsentAssessment(
            request_id=request.request_id,
            status=DecisionStatus.DENIED,
            consent_mode=record.mode,
            consent_valid=consent_valid,
            consent_fresh=consent_fresh,
            scope_allowed=scope_allowed,
            reason_code="consent_denied",
        )

    def assess_safety(
        self,
        *,
        session: InteractionSession,
        request: InteractionRequest,
        candidate_plan,
        start_pose=None,
    ) -> SafetyAssessment:
        """
        Evaluate software + hardware safety for the request or candidate plan.

        The runtime remains conservative:
        - a latched safety gate means denial
        - RED means denial
        - hardware faults mean denial
        - retreat / safe-hold requests take priority
        """
        if self._safety.is_latched():
            return SafetyAssessment(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                safety_level=SafetyLevel.RED,
                may_approach=False,
                may_contact=False,
                requires_retreat=False,
                requires_safe_hold=True,
                reason_code=f"safety_latched:{self._safety.last_reason()}",
            )

        if candidate_plan is not None:
            ok_sw, why_sw = self._safety.software_ok(candidate_plan, self._risk_query, start_pose)
            ok_hw, why_hw = self._safety.hardware_ok()

            if not ok_sw:
                return SafetyAssessment(
                    request_id=request.request_id,
                    status=DecisionStatus.DENIED,
                    safety_level=SafetyLevel.RED,
                    may_approach=False,
                    may_contact=False,
                    requires_retreat=False,
                    requires_safe_hold=False,
                    reason_code=why_sw,
                )

            if not ok_hw:
                return SafetyAssessment(
                    request_id=request.request_id,
                    status=DecisionStatus.DENIED,
                    safety_level=SafetyLevel.RED,
                    may_approach=False,
                    may_contact=False,
                    requires_retreat=False,
                    requires_safe_hold=True,
                    reason_code=why_hw,
                )

            return SafetyAssessment(
                request_id=request.request_id,
                status=DecisionStatus.APPROVED,
                safety_level=SafetyLevel.GREEN,
                may_approach=True,
                may_contact=request.requires_contact,
                requires_retreat=False,
                requires_safe_hold=False,
                reason_code="safety_ok",
            )

        # No plan yet: evaluate session-side summary posture conservatively.
        if session.safety_level == SafetyLevel.RED:
            return SafetyAssessment(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                safety_level=SafetyLevel.RED,
                may_approach=False,
                may_contact=False,
                requires_retreat=False,
                requires_safe_hold=False,
                reason_code="session_safety_red",
            )

        if request.requires_contact:
            return SafetyAssessment(
                request_id=request.request_id,
                status=DecisionStatus.REQUIRES_VERIFICATION,
                safety_level=session.safety_level,
                may_approach=session.safety_level != SafetyLevel.RED,
                may_contact=False,
                requires_retreat=False,
                requires_safe_hold=False,
                reason_code="plan_required_before_contact",
            )

        return SafetyAssessment(
            request_id=request.request_id,
            status=DecisionStatus.APPROVED,
            safety_level=session.safety_level,
            may_approach=session.safety_level != SafetyLevel.RED,
            may_contact=False,
            requires_retreat=False,
            requires_safe_hold=False,
            reason_code="session_safety_ok",
        )

    def build_planning_outcome(
        self,
        *,
        request: InteractionRequest,
        nudge: Optional[Nudge],
        consent_record: ConsentRecord,
        profile_name: Optional[str] = None,
        hints: Optional[PlannerHints] = None,
    ) -> PlanningOutcome:
        """
        Build a planning outcome from a nudge and consent record.

        For non-contact requests, planning may not produce a ContactPlan and that
        is acceptable. This method is primarily for contact-oriented behaviors.
        """
        if request.interaction_kind in {
            InteractionKind.OBSERVE_ONLY,
            InteractionKind.SAFE_HOLD,
        }:
            return PlanningOutcome(
                request_id=request.request_id,
                status=DecisionStatus.APPROVED,
                reason_code="no_contact_plan_required",
                plan=None,
                degraded=False,
            )

        if request.interaction_kind == InteractionKind.RETREAT:
            return PlanningOutcome(
                request_id=request.request_id,
                status=DecisionStatus.REQUIRES_VERIFICATION,
                reason_code="retreat_planner_not_yet_implemented",
                plan=None,
                degraded=False,
            )

        if nudge is None:
            return PlanningOutcome(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                reason_code="missing_nudge",
                plan=None,
                degraded=False,
            )

        plan = self._planner.plan(
            nudge=nudge,
            consent=consent_record,
            profile_name=profile_name,
            hints=hints,
        )
        if plan is None:
            return PlanningOutcome(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                reason_code="planner_returned_none",
                plan=None,
                degraded=False,
            )

        return PlanningOutcome(
            request_id=request.request_id,
            status=DecisionStatus.APPROVED,
            reason_code="plan_ready",
            plan=plan,
            degraded=False,
        )

    def decide(
        self,
        *,
        session: InteractionSession,
        request: InteractionRequest,
        nudge: Optional[Nudge] = None,
        profile_name: Optional[str] = None,
        hints: Optional[PlannerHints] = None,
        start_pose=None,
    ) -> CoordinationDecision:
        """
        Produce a final coordination decision for one runtime request.

        This method does not command execution. It produces an explicit decision
        object that a future execution adapter or logger can consume.
        """
        consent = self.assess_consent(session=session, request=request)

        if consent.status == DecisionStatus.DENIED:
            safety = SafetyAssessment(
                request_id=request.request_id,
                status=DecisionStatus.REQUIRES_VERIFICATION,
                safety_level=session.safety_level,
                may_approach=False,
                may_contact=False,
                requires_retreat=False,
                requires_safe_hold=False,
                reason_code="consent_denied_before_planning",
            )
            return CoordinationDecision(
                request_id=request.request_id,
                status=DecisionStatus.DENIED,
                reason_code=consent.reason_code,
                consent=consent,
                safety=safety,
                planning=None,
            )

        consent_record = self._consent.query(
            subject_id=request.subject_id or "",
            requested_scopes=self._requested_scopes(request),
        )

        planning = self.build_planning_outcome(
            request=request,
            nudge=nudge,
            consent_record=consent_record,
            profile_name=profile_name,
            hints=hints,
        )

        safety = self.assess_safety(
            session=session,
            request=request,
            candidate_plan=planning.plan,
            start_pose=start_pose,
        )

        final_status = self._merge_status(consent.status, safety.status, planning.status)
        final_reason = self._merge_reason(consent.reason_code, safety.reason_code, planning.reason_code)

        return CoordinationDecision(
            request_id=request.request_id,
            status=final_status,
            reason_code=final_reason,
            consent=consent,
            safety=safety,
            planning=planning,
        )

    def apply_decision_to_session(
        self,
        *,
        session: InteractionSession,
        decision: CoordinationDecision,
    ) -> None:
        """
        Apply the coordination decision conservatively to the runtime session.

        This gives the runtime package a visible state/update path before a
        future execution adapter exists.
        """
        session.consent_valid = decision.consent.consent_valid
        session.consent_fresh = decision.consent.consent_fresh
        session.safety_level = decision.safety.safety_level

        if decision.status == DecisionStatus.DENIED:
            if decision.safety.requires_safe_hold:
                fault = RuntimeFault(
                    fault_id=f"{decision.request_id}:safe_hold",
                    reason_code=decision.reason_code,
                    severity=FaultSeverity.ABORT,
                    disposition=FaultDisposition.SAFE_HOLD,
                    source="runtime_coordinator",
                    requires_safe_hold=True,
                )
                session.apply_fault(fault)
            elif decision.safety.requires_retreat:
                fault = RuntimeFault(
                    fault_id=f"{decision.request_id}:retreat",
                    reason_code=decision.reason_code,
                    severity=FaultSeverity.ABORT,
                    disposition=FaultDisposition.RETREAT,
                    source="runtime_coordinator",
                    requires_retreat=True,
                )
                session.apply_fault(fault)
            else:
                fault = RuntimeFault(
                    fault_id=f"{decision.request_id}:blocked",
                    reason_code=decision.reason_code,
                    severity=FaultSeverity.BLOCKING,
                    disposition=FaultDisposition.REJECT_ACTION,
                    source="runtime_coordinator",
                )
                session.apply_fault(fault)
            return

        if decision.planning and decision.planning.plan is not None:
            session.active_plan_id = decision.request_id

        session.clear_non_latched_fault()
        session.mark_updated()

    def _requested_scopes(self, request: InteractionRequest) -> list[str]:
        if request.requires_contact:
            if request.requested_scope:
                return [request.requested_scope]
            return [self._config.default_contact_scope]
        if request.requested_scope:
            return [request.requested_scope]
        return []

    @staticmethod
    def _merge_status(
        consent_status: DecisionStatus,
        safety_status: DecisionStatus,
        planning_status: DecisionStatus,
    ) -> DecisionStatus:
        statuses = {consent_status, safety_status, planning_status}
        if DecisionStatus.DENIED in statuses:
            return DecisionStatus.DENIED
        if DecisionStatus.REQUIRES_VERIFICATION in statuses:
            return DecisionStatus.REQUIRES_VERIFICATION
        if DecisionStatus.DEGRADED_APPROVAL in statuses:
            return DecisionStatus.DEGRADED_APPROVAL
        return DecisionStatus.APPROVED

    @staticmethod
    def _merge_reason(*reasons: str) -> str:
        clean = [r for r in reasons if r]
        return " | ".join(clean[:3])


__all__ = [
    "CoordinatorConfig",
    "RuntimeCoordinator",
]
