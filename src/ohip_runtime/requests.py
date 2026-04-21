"""
Runtime request and decision models for IX-HapticSight.

This module defines the minimal coordination-facing contracts that sit between
the protocol core and the future runtime coordinator.

These models are intentionally backend-agnostic:
- no ROS 2 imports
- no transport assumptions
- no hardware-specific payloads

They exist so the runtime can reason explicitly about:
- what was requested
- what consent decision was returned
- what safety decision was returned
- whether a plan was approved, denied, or downgraded
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Optional

from ohip.schemas import ConsentMode, ContactPlan, SafetyLevel


class InteractionKind(str, Enum):
    """
    High-level interaction intent classes.

    These are deliberately narrow. They represent runtime intent categories,
    not broad social behavior claims.
    """

    OBSERVE_ONLY = "OBSERVE_ONLY"
    APPROACH_ONLY = "APPROACH_ONLY"
    PRECONTACT_VERIFY = "PRECONTACT_VERIFY"
    SUPPORT_CONTACT = "SUPPORT_CONTACT"
    OBJECT_INTERACTION = "OBJECT_INTERACTION"
    RETREAT = "RETREAT"
    SAFE_HOLD = "SAFE_HOLD"


class RequestSource(str, Enum):
    """
    Origin of an interaction request.

    This will matter later for trust boundaries, replay separation,
    and benchmark provenance.
    """

    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    POLICY_AUTOMATION = "POLICY_AUTOMATION"
    BENCHMARK = "BENCHMARK"
    REPLAY = "REPLAY"


class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
    DEGRADED_APPROVAL = "DEGRADED_APPROVAL"


@dataclass(frozen=True)
class InteractionRequest:
    """
    Runtime-facing request for a bounded interaction behavior.

    This object does not replace the protocol-level data structures.
    It gives the runtime coordinator a stable input contract.
    """

    request_id: str
    session_id: str
    subject_id: Optional[str]
    interaction_kind: InteractionKind
    source: RequestSource
    target_name: str = ""
    requested_scope: str = ""
    requires_contact: bool = False
    requires_consent_freshness: bool = True
    requested_at_utc_s: float = field(default_factory=time)
    notes: str = ""


@dataclass(frozen=True)
class ConsentAssessment:
    """
    Result of consent/policy evaluation for one runtime request.
    """

    request_id: str
    status: DecisionStatus
    consent_mode: ConsentMode
    consent_valid: bool
    consent_fresh: bool
    scope_allowed: bool
    reason_code: str
    evaluated_at_utc_s: float = field(default_factory=time)

    @property
    def approved(self) -> bool:
        return self.status in {
            DecisionStatus.APPROVED,
            DecisionStatus.DEGRADED_APPROVAL,
        }


@dataclass(frozen=True)
class SafetyAssessment:
    """
    Result of safety evaluation for one runtime request.
    """

    request_id: str
    status: DecisionStatus
    safety_level: SafetyLevel
    may_approach: bool
    may_contact: bool
    requires_retreat: bool
    requires_safe_hold: bool
    reason_code: str
    evaluated_at_utc_s: float = field(default_factory=time)

    @property
    def approved(self) -> bool:
        return self.status in {
            DecisionStatus.APPROVED,
            DecisionStatus.DEGRADED_APPROVAL,
        }


@dataclass(frozen=True)
class PlanningOutcome:
    """
    Planner result associated with a runtime request.

    A request may be denied before planning, may require additional
    verification, or may produce an actual ContactPlan.
    """

    request_id: str
    status: DecisionStatus
    reason_code: str
    plan: Optional[ContactPlan] = None
    degraded: bool = False
    created_at_utc_s: float = field(default_factory=time)

    @property
    def has_plan(self) -> bool:
        return self.plan is not None and self.status in {
            DecisionStatus.APPROVED,
            DecisionStatus.DEGRADED_APPROVAL,
        }


@dataclass(frozen=True)
class CoordinationDecision:
    """
    Final coordinator-facing summary for a runtime request.

    This is the compact artifact that can be passed to a future execution
    adapter, logger, replay system, or benchmark harness.
    """

    request_id: str
    status: DecisionStatus
    reason_code: str
    consent: ConsentAssessment
    safety: SafetyAssessment
    planning: Optional[PlanningOutcome] = None
    created_at_utc_s: float = field(default_factory=time)

    @property
    def executable(self) -> bool:
        if self.status not in {
            DecisionStatus.APPROVED,
            DecisionStatus.DEGRADED_APPROVAL,
        }:
            return False
        if not self.consent.approved:
            return False
        if not self.safety.approved:
            return False
        if self.planning is None:
            return False
        return self.planning.has_plan


__all__ = [
    "InteractionKind",
    "RequestSource",
    "DecisionStatus",
    "InteractionRequest",
    "ConsentAssessment",
    "SafetyAssessment",
    "PlanningOutcome",
    "CoordinationDecision",
]
