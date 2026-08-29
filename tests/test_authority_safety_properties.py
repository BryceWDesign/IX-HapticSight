import random

from ohip.schemas import SafetyLevel
from ohip_control import ActionProposal, AuthorityDisposition, IndependentSafetyAuthority


def test_authority_never_expands_randomized_action_authority():
    rng = random.Random(20260829)
    authority = IndependentSafetyAuthority()
    levels = [SafetyLevel.GREEN, SafetyLevel.YELLOW, SafetyLevel.RED]
    for i in range(2000):
        base_force = rng.uniform(0.0, 20.0)
        base_speed = rng.uniform(0.0, 2.0)
        requested_force = rng.uniform(0.0, 50.0)
        requested_speed = rng.uniform(0.0, 5.0)
        p = ActionProposal(
            action_id=str(i),
            requested_force_N=requested_force,
            requested_speed_mps=requested_speed,
            base_force_cap_N=base_force,
            base_speed_cap_mps=base_speed,
            safety_level=rng.choice(levels),
            perception_uncertainty=rng.random(),
            perception_quorum_ok=rng.choice([True, True, True, False]),
            consent_required=rng.choice([True, False]),
            consent_active=rng.choice([True, False]),
            human_present=rng.choice([True, False]),
            proximity_m=rng.uniform(0.0, 2.0),
        )
        out = authority.decide(p)
        assert 0.0 <= out.granted_force_N <= base_force + 1e-9
        assert 0.0 <= out.granted_speed_mps <= base_speed + 1e-9
        assert out.granted_force_N <= requested_force + 1e-9
        assert out.granted_speed_mps <= requested_speed + 1e-9
        if out.disposition == AuthorityDisposition.DENY:
            assert out.granted_force_N == 0.0
            assert out.granted_speed_mps == 0.0
