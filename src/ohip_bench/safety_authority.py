"""Adversarial benchmark scenarios for the independent safety authority."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from ohip.schemas import SafetyLevel
from ohip_control import ActionProposal, AuthorityDisposition, IndependentSafetyAuthority


@dataclass(frozen=True)
class AuthorityScenarioResult:
    scenario: str
    expected: AuthorityDisposition
    observed: AuthorityDisposition
    passed: bool
    reason: str
    granted_force_N: float
    granted_speed_mps: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d["expected"] = self.expected.value
        d["observed"] = self.observed.value
        return d


def _base(**updates) -> ActionProposal:
    d = dict(
        action_id="benchmark",
        requested_force_N=2.0,
        requested_speed_mps=0.08,
        base_force_cap_N=3.0,
        base_speed_cap_mps=0.10,
        safety_level=SafetyLevel.GREEN,
        perception_uncertainty=0.05,
        perception_quorum_ok=True,
        consent_required=True,
        consent_active=True,
        human_present=False,
        proximity_m=None,
    )
    d.update(updates)
    return ActionProposal(**d)


def run_authority_benchmark(authority: IndependentSafetyAuthority | None = None) -> list[AuthorityScenarioResult]:
    authority = authority or IndependentSafetyAuthority()
    scenarios = [
        ("nominal", _base(), AuthorityDisposition.ALLOW),
        ("over_request", _base(requested_force_N=8.0, requested_speed_mps=0.5), AuthorityDisposition.MODIFY),
        ("red_hazard", _base(safety_level=SafetyLevel.RED), AuthorityDisposition.DENY),
        ("consent_loss", _base(consent_active=False), AuthorityDisposition.DENY),
        ("model_disagreement", _base(perception_quorum_ok=False), AuthorityDisposition.DENY),
        ("high_uncertainty", _base(perception_uncertainty=0.85), AuthorityDisposition.DENY),
        ("human_too_close", _base(human_present=True, proximity_m=0.10), AuthorityDisposition.DENY),
        ("human_near_derate", _base(human_present=True, proximity_m=0.40), AuthorityDisposition.MODIFY),
    ]
    results: list[AuthorityScenarioResult] = []
    for name, proposal, expected in scenarios:
        decision = authority.decide(proposal)
        results.append(
            AuthorityScenarioResult(
                scenario=name,
                expected=expected,
                observed=decision.disposition,
                passed=decision.disposition == expected,
                reason=decision.reason,
                granted_force_N=decision.granted_force_N,
                granted_speed_mps=decision.granted_speed_mps,
            )
        )
    return results
