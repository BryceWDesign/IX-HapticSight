import pytest

from ohip_ros2 import Ros2ContactBridge, Ros2Unavailable


def test_ros2_bridge_does_not_fake_runtime_when_rclpy_missing():
    bridge = Ros2ContactBridge()
    with pytest.raises(Ros2Unavailable):
        bridge.start()
