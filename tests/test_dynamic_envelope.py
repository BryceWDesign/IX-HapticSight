from ohip.schemas import SafetyLevel
from ohip_control import DynamicEnvelopeInput, DynamicSafetyEnvelope


def test_red_hazard_denies_all_authority():
    out = DynamicSafetyEnvelope().evaluate(
        DynamicEnvelopeInput(2.0, .1, 3.0, .2, safety_level=SafetyLevel.RED)
    )
    assert not out.allowed
    assert out.force_command_N == 0.0


def test_human_proximity_derates_authority():
    out = DynamicSafetyEnvelope().evaluate(
        DynamicEnvelopeInput(
            requested_force_N=3.0,
            requested_speed_mps=.2,
            base_force_cap_N=3.0,
            base_speed_cap_mps=.2,
            safety_level=SafetyLevel.GREEN,
            human_present=True,
            proximity_m=.4,
        )
    )
    assert out.allowed
    assert 0.0 < out.authority_scale < 1.0
    assert out.force_command_N < 3.0
