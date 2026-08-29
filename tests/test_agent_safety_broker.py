import pytest

from ohip.schemas import SafetyLevel
from ohip_agent import AgentPhysicalProposal, AgentSafetyBroker
from ohip_control import AuthorityDisposition, MultimodalSafetyInput


def proposal(**updates):
    d = dict(
        proposal_id="p-1",
        agent_id="vla:test",
        action_kind="contact",
        requested_force_N=8.0,
        requested_speed_mps=.5,
        base_force_cap_N=3.0,
        base_speed_cap_mps=.1,
        consent_required=True,
        consent_active=True,
        created_at_s=10.0,
        rationale="agent says contact is useful",
    )
    d.update(updates)
    return AgentPhysicalProposal(**d)


def test_agent_broker_never_grants_more_than_deterministic_caps():
    out = AgentSafetyBroker().decide(proposal(), MultimodalSafetyInput())
    assert out.disposition == AuthorityDisposition.MODIFY
    assert out.granted_force_N <= 3.0
    assert out.granted_speed_mps <= .1
    assert len(out.proposal_sha256) == 64


def test_agent_broker_denies_red_sensor_fusion_even_if_agent_requests_contact():
    out = AgentSafetyBroker().decide(
        proposal(),
        MultimodalSafetyInput(vision_level=SafetyLevel.RED),
    )
    assert out.disposition == AuthorityDisposition.DENY
    assert out.granted_force_N == 0.0


def test_agent_broker_denies_missing_consent():
    out = AgentSafetyBroker().decide(proposal(consent_active=False), MultimodalSafetyInput())
    assert out.disposition == AuthorityDisposition.DENY
    assert "consent_missing" in out.reasons


def test_agent_proposal_rejects_nan_instead_of_forwarding_it():
    with pytest.raises(ValueError):
        AgentSafetyBroker().decide(proposal(requested_force_N=float("nan")), MultimodalSafetyInput())
