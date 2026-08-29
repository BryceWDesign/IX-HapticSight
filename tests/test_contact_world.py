from ohip_sim import ContactWorld


def test_contact_world_generates_force_after_surface_contact():
    world = ContactWorld(surface_position_m=.01)
    state = None
    for _ in range(100):
        state = world.step(command_velocity_mps=.05, force_cap_N=10.0, dt_s=.005)
    assert state is not None
    assert state.measured_force_N > 0.0


def test_contact_world_low_level_limiter_stops_forward_motion_over_cap():
    world = ContactWorld(surface_position_m=.001, stiffness_N_per_m=5000)
    state = None
    for _ in range(50):
        state = world.step(command_velocity_mps=.2, force_cap_N=.5, dt_s=.005)
        if state.measured_force_N > .5:
            break
    assert state is not None
    assert state.measured_force_N > .5
    assert state.velocity_mps <= 0.0
