from ohip_control import BoundedRealtimeController, ControllerInput, ControllerState


def inp(**kw):
    base = dict(
        requested_speed_mps=.05,
        requested_force_N=1.0,
        measured_force_N=.2,
        force_cap_N=2.0,
        speed_cap_mps=.1,
        sensor_age_ms=2.0,
        consent_active=True,
        contact_requested=True,
        perception_quorum_ok=True,
        e_stop=False,
        contact_detected=False,
    )
    base.update(kw)
    return ControllerInput(**base)


def test_controller_clamps_request_inside_envelope():
    c = BoundedRealtimeController(target_period_ms=50)
    out = c.step(inp(requested_force_N=5.0, requested_speed_mps=.5))
    assert out.command_force_N == 2.0
    assert out.command_speed_mps == .1
    assert not out.stop


def test_controller_latches_on_measured_overforce():
    c = BoundedRealtimeController(target_period_ms=50)
    out = c.step(inp(measured_force_N=2.5, force_cap_N=2.0, contact_detected=True))
    assert out.stop
    assert out.latched
    assert out.state == ControllerState.FAULTED
    assert out.command_force_N == 0.0


def test_controller_latches_when_consent_disappears_during_contact_request():
    c = BoundedRealtimeController(target_period_ms=50)
    out = c.step(inp(consent_active=False))
    assert out.latched
    assert out.reason == "consent_lost"


def test_controller_stops_on_perception_disagreement():
    c = BoundedRealtimeController(target_period_ms=50)
    out = c.step(inp(perception_quorum_ok=False))
    assert out.stop
    assert out.reason == "perception_quorum_failed"
