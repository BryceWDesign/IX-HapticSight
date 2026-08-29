from ohip_hil import HILAcceptanceCriteria, HILHarness, HILSample, HILStatus, HardwareCapability


def test_hil_refuses_to_fake_pass_without_hardware():
    harness = HILHarness()
    out = harness.run(
        probe=lambda: [HardwareCapability("force_torque", False)],
        executor=lambda: [],
    )
    assert out.status == HILStatus.NOT_RUN_NO_HARDWARE


def test_hil_can_pass_only_with_declared_hardware_and_measured_samples():
    criteria = HILAcceptanceCriteria(max_force_N=3.5, max_latency_ms=25, min_samples=3)
    harness = HILHarness(criteria)
    out = harness.run(
        probe=lambda: [
            HardwareCapability("robot_motion", True, "robot-1"),
            HardwareCapability("force_torque", True, "ft-1"),
        ],
        executor=lambda: [
            HILSample(1.0, 1.0, 3.0),
            HILSample(1.1, 2.0, 4.0),
            HILSample(1.2, 3.0, 5.0),
        ],
    )
    assert out.status == HILStatus.PASSED
