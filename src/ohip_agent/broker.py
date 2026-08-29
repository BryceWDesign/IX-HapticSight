"""Model-agnostic broker for LLM/VLA-proposed physical actions.

The broker exists so an agent can be arbitrarily capable without becoming the
final physical authority. Agent output is treated as an untrusted proposal.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from time import time

from ohip.schemas import SafetyLevel
from ohip_control import (
    ActionProposal,
    AuthorityDisposition,
    IndependentSafetyAuthority,
    MultimodalSafetyDecision,
    MultimodalSafetyFusion,
    MultimodalSafetyInput,
)


@dataclass(frozen=True)
class AgentPhysicalProposal:
    proposal_id: str
    agent_id: str
    action_kind: str
    requested_force_N: float
    requested_speed_mps: float
    base_force_cap_N: float
    base_speed_cap_mps: float
    consent_required: bool
    consent_active: bool
    human_present: bool = False
    proximity_m: float | None = None
    created_at_s: float = 0.0
    rationale: str = ""

    def validate(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("proposal_id is required")
        if not self.agent_id.strip():
            raise ValueError("agent_id is required")
        if not self.action_kind.strip():
            raise ValueError("action_kind is required")
        for name in ("requested_force_N", "requested_speed_mps", "base_force_cap_N", "base_speed_cap_mps"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.proximity_m is not None and (not math.isfinite(float(self.proximity_m)) or float(self.proximity_m) < 0.0):
            raise ValueError("proximity_m must be finite and non-negative")

    def canonical_dict(self) -> dict:
        doc = asdict(self)
        # Timestamp is provenance, but keeping it in the digest makes each proposal unique.
        return doc

    def sha256(self) -> str:
        body = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class BrokerDecisionReceipt:
    proposal_id: str
    proposal_sha256: str
    agent_id: str
    disposition: AuthorityDisposition
    granted_force_N: float
    granted_speed_mps: float
    fused_safety_level: SafetyLevel
    reasons: tuple[str, ...]
    counterfactual: str
    decided_at_s: float

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "proposal_sha256": self.proposal_sha256,
            "agent_id": self.agent_id,
            "disposition": self.disposition.value,
            "granted_force_N": self.granted_force_N,
            "granted_speed_mps": self.granted_speed_mps,
            "fused_safety_level": self.fused_safety_level.value,
            "reasons": list(self.reasons),
            "counterfactual": self.counterfactual,
            "decided_at_s": self.decided_at_s,
        }


class AgentSafetyBroker:
    """Combine multimodal safety state with an untrusted agent proposal."""

    def __init__(
        self,
        *,
        fusion: MultimodalSafetyFusion | None = None,
        authority: IndependentSafetyAuthority | None = None,
    ) -> None:
        self.fusion = fusion or MultimodalSafetyFusion()
        self.authority = authority or IndependentSafetyAuthority()

    def decide(self, proposal: AgentPhysicalProposal, sensor_state: MultimodalSafetyInput) -> BrokerDecisionReceipt:
        proposal.validate()
        fused = self.fusion.evaluate(sensor_state)
        decision = self.authority.decide(
            ActionProposal(
                action_id=proposal.proposal_id,
                requested_force_N=proposal.requested_force_N,
                requested_speed_mps=proposal.requested_speed_mps,
                base_force_cap_N=proposal.base_force_cap_N,
                base_speed_cap_mps=proposal.base_speed_cap_mps,
                safety_level=fused.level,
                perception_uncertainty=sensor_state.perception_uncertainty,
                perception_quorum_ok=sensor_state.perception_quorum_ok,
                consent_required=proposal.consent_required,
                consent_active=proposal.consent_active,
                human_present=proposal.human_present,
                proximity_m=proposal.proximity_m,
            )
        )
        reasons = tuple(fused.reasons) + (decision.reason,)
        return BrokerDecisionReceipt(
            proposal_id=proposal.proposal_id,
            proposal_sha256=proposal.sha256(),
            agent_id=proposal.agent_id,
            disposition=decision.disposition,
            granted_force_N=decision.granted_force_N,
            granted_speed_mps=decision.granted_speed_mps,
            fused_safety_level=fused.level,
            reasons=reasons,
            counterfactual=decision.counterfactual,
            decided_at_s=time(),
        )
