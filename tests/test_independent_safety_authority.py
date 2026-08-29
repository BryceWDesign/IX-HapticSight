from ohip.schemas import SafetyLevel
from ohip_control import ActionProposal, AuthorityDisposition, IndependentSafetyAuthority


def proposal(**kw):
    base = dict(
        action_id="a",
        requested_force_N=2.0,
        requested_speed_mps=.1,
        base_force_cap_N=3.0,
        base_speed_cap_mps=.2,
        safety_level=SafetyLevel.GREEN,
        perception_uncertainty=.05,
        perception_quorum_ok=True,
        consent_required=True,
        consent_active=True,
        human_present=False,
        proximity_m=None,
    )
    base.update(kw)
    return ActionProposal(**base)


def test_authority_denies_without_consent():
    out = IndependentSafetyAuthority().decide(proposal(consent_active=False))
    assert out.disposition == AuthorityDisposition.DENY
    assert out.granted_force_N == 0.0
    assert "consent" in out.reason


def test_authority_denies_model_disagreement():
    out = IndependentSafetyAuthority().decide(proposal(perception_quorum_ok=False))
    assert out.disposition == AuthorityDisposition.DENY
    assert out.reason == "perception_quorum_failed"


def test_authority_modifies_excessive_request():
    out = IndependentSafetyAuthority().decide(proposal(requested_force_N=9.0, requested_speed_mps=1.0))
    assert out.disposition == AuthorityDisposition.MODIFY
    assert out.granted_force_N <= 3.0
    assert out.granted_speed_mps <= .2
