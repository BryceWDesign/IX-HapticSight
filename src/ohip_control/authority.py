"""Independent action authority between AI/planning and physical execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ohip.schemas import SafetyLevel

from .envelope import DynamicEnvelopeInput, DynamicSafetyEnvelope


class AuthorityDisposition(str, Enum):
    ALLOW = "ALLOW"
    MODIFY = "MODIFY"
    DENY = "DENY"


@dataclass(frozen=True)
class ActionProposal:
    action_id: str
    requested_force_N: float
    requested_speed_mps: float
    base_force_cap_N: float
    base_speed_cap_mps: float
    safety_level: SafetyLevel
    perception_uncertainty: float
    perception_quorum_ok: bool
    consent_required: bool
    consent_active: bool
    human_present: bool = False
    proximity_m: float | None = None


@dataclass(frozen=True)
class AuthorityDecision:
    action_id: str
    disposition: AuthorityDisposition
    granted_force_N: float
    granted_speed_mps: float
    reason: str
    counterfactual: str


class IndependentSafetyAuthority:
    """Fail-closed safety authority that no learned policy may bypass."""

    def __init__(self, envelope: DynamicSafetyEnvelope | None = None) -> None:
        self.envelope = envelope or DynamicSafetyEnvelope()

    def decide(self, proposal: ActionProposal) -> AuthorityDecision:
        if proposal.consent_required and not proposal.consent_active:
            return AuthorityDecision(
                proposal.action_id,
                AuthorityDisposition.DENY,
                0.0,
                0.0,
                "consent_missing",
                "Obtain active consent in the requested contact scope before contact authority can be granted.",
            )
        if not proposal.perception_quorum_ok:
            return AuthorityDecision(
                proposal.action_id,
                AuthorityDisposition.DENY,
                0.0,
                0.0,
                "perception_quorum_failed",
                "Restore agreement between independent perception channels or require human verification.",
            )
        env = self.envelope.evaluate(
            DynamicEnvelopeInput(
                requested_force_N=proposal.requested_force_N,
                requested_speed_mps=proposal.requested_speed_mps,
                base_force_cap_N=proposal.base_force_cap_N,
                base_speed_cap_mps=proposal.base_speed_cap_mps,
                proximity_m=proposal.proximity_m,
                perception_uncertainty=proposal.perception_uncertainty,
                safety_level=proposal.safety_level,
                human_present=proposal.human_present,
            )
        )
        if not env.allowed:
            counterfactual = {
                "red_hazard": "Move the target/corridor out of RED or clear the hazard before retrying.",
                "perception_uncertainty_stop": "Reduce perception uncertainty below the stop threshold or require human verification.",
                "human_proximity_stop": "Increase separation beyond the configured human stop distance.",
            }.get(env.reason, "Resolve the safety veto before retrying.")
            return AuthorityDecision(proposal.action_id, AuthorityDisposition.DENY, 0.0, 0.0, env.reason, counterfactual)
        modified = (
            env.force_command_N + 1e-9 < max(0.0, proposal.requested_force_N)
            or env.speed_command_mps + 1e-9 < max(0.0, proposal.requested_speed_mps)
        )
        disposition = AuthorityDisposition.MODIFY if modified else AuthorityDisposition.ALLOW
        if modified:
            counterfactual = (
                f"Requested action can proceed only inside the granted envelope: force <= {env.force_command_N:.3f} N, "
                f"speed <= {env.speed_command_mps:.3f} m/s."
            )
        else:
            counterfactual = "No modification required under current measured safety state."
        return AuthorityDecision(
            proposal.action_id,
            disposition,
            env.force_command_N,
            env.speed_command_mps,
            env.reason,
            counterfactual,
        )
