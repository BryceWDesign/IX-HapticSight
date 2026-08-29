from ohip.schemas import SafetyLevel
from ohip_control import MultimodalSafetyFusion, MultimodalSafetyInput
from ohip_interfaces.force_torque import ContactForceAssessment
from ohip_interfaces.proximity import ProximityAssessment
from ohip_interfaces.tactile import TactileContactAssessment
from ohip_interfaces.thermal import ThermalAssessment


def test_multimodal_nominal_stays_green():
    out = MultimodalSafetyFusion().evaluate(MultimodalSafetyInput())
    assert out.level == SafetyLevel.GREEN


def test_missing_required_sensor_fails_closed():
    out = MultimodalSafetyFusion().evaluate(MultimodalSafetyInput(require_force=True))
    assert out.level == SafetyLevel.RED
    assert out.missing_required_modalities == ("force",)


def test_excessive_force_overrides_green_vision():
    force = ContactForceAssessment(True, True, 4.0, .1, .25, 3.5)
    out = MultimodalSafetyFusion().evaluate(MultimodalSafetyInput(force=force))
    assert out.level == SafetyLevel.RED
    assert "force_excessive" in out.reasons


def test_multiple_caution_modalities_produce_yellow():
    prox = ProximityAssessment(True, True, True, 1, 80.0, 120.0, 40.0)
    thermal = ThermalAssessment(True, False, 1, 40.0, 38.0, 45.0)
    tactile = TactileContactAssessment(True, False, 1, 20.0, 2.0, .2, False, False)
    out = MultimodalSafetyFusion().evaluate(
        MultimodalSafetyInput(proximity=prox, thermal=thermal, tactile=tactile)
    )
    assert out.level == SafetyLevel.YELLOW
    assert len(out.available_modalities) == 3


def test_perception_quorum_failure_is_red_even_if_sensors_nominal():
    out = MultimodalSafetyFusion().evaluate(MultimodalSafetyInput(perception_quorum_ok=False))
    assert out.level == SafetyLevel.RED
