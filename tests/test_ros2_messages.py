from types import SimpleNamespace

from ohip_ros2 import wrench_stamped_to_sample


def test_wrench_stamped_converter_without_ros_runtime():
    msg = SimpleNamespace(
        header=SimpleNamespace(
            frame_id="tool0",
            stamp=SimpleNamespace(sec=10, nanosec=500_000_000),
        ),
        wrench=SimpleNamespace(
            force=SimpleNamespace(x=1.0, y=2.0, z=2.0),
            torque=SimpleNamespace(x=.1, y=.2, z=.2),
        ),
    )
    sample = wrench_stamped_to_sample(msg)
    assert sample.frame == "tool0"
    assert sample.force_magnitude_N() == 3.0
    assert sample.quality.source_name == "ros2_wrench"
