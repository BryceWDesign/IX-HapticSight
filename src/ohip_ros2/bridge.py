"""ROS 2 execution and sensor bridge for IX-HapticSight.

The bridge uses standard ROS 2 messages when ``rclpy`` is available. It does
not weaken HapticSight safety authority: only already-bounded velocity/force
commands should be published.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Any

from ohip_interfaces.force_torque import ForceTorqueSample
from ohip_interfaces.tactile import TactileFrame

from .messages import Ros2Command, tactile_multiarray_to_frame, wrench_stamped_to_sample


@dataclass(frozen=True)
class Ros2BridgeConfig:
    node_name: str = "ix_hapticsight_bridge"
    wrench_topic: str = "/hapticsight/force_torque"
    twist_topic: str = "/hapticsight/bounded_twist"
    safety_event_topic: str = "/hapticsight/safety_event"
    e_stop_topic: str = "/hapticsight/e_stop"
    tactile_topic: str = "/hapticsight/tactile_patches"
    qos_depth: int = 10


class Ros2Unavailable(RuntimeError):
    pass


class Ros2ContactBridge:
    """Runtime ROS 2 bridge using ``geometry_msgs`` and ``std_msgs``.

    ``start`` imports ROS lazily so the rest of the repository remains usable on
    systems without ROS 2. ``publish_bounded_command`` publishes a TwistStamped
    plus a structured safety side-channel containing force authority and audit
    identifiers.
    """

    def __init__(self, config: Ros2BridgeConfig | None = None) -> None:
        self.config = config or Ros2BridgeConfig()
        self._node: Any | None = None
        self._rclpy: Any | None = None
        self._twist_pub: Any | None = None
        self._event_pub: Any | None = None
        self._wrench_sub: Any | None = None
        self._estop_sub: Any | None = None
        self._last_wrench: ForceTorqueSample | None = None
        self._e_stop = False
        self._last_tactile: TactileFrame | None = None
        self._lock = Lock()

    @property
    def started(self) -> bool:
        return self._node is not None

    @property
    def e_stop(self) -> bool:
        with self._lock:
            return self._e_stop

    def latest_wrench(self) -> ForceTorqueSample | None:
        with self._lock:
            return self._last_wrench

    def latest_tactile(self) -> TactileFrame | None:
        with self._lock:
            return self._last_tactile

    def start(self) -> None:
        if self.started:
            return
        try:
            import rclpy
            from geometry_msgs.msg import TwistStamped, WrenchStamped
            from std_msgs.msg import Bool, Float32MultiArray, String
        except Exception as exc:  # pragma: no cover - requires ROS2 environment
            raise Ros2Unavailable(
                "ROS 2 runtime dependencies are not installed. Install this package inside a ROS 2 environment with rclpy, geometry_msgs and std_msgs."
            ) from exc

        if not rclpy.ok():
            rclpy.init(args=None)
        node = rclpy.create_node(self.config.node_name)
        self._rclpy = rclpy
        self._node = node
        self._TwistStamped = TwistStamped
        self._String = String
        self._twist_pub = node.create_publisher(TwistStamped, self.config.twist_topic, self.config.qos_depth)
        self._event_pub = node.create_publisher(String, self.config.safety_event_topic, self.config.qos_depth)
        self._wrench_sub = node.create_subscription(WrenchStamped, self.config.wrench_topic, self._on_wrench, self.config.qos_depth)
        self._estop_sub = node.create_subscription(Bool, self.config.e_stop_topic, self._on_estop, self.config.qos_depth)
        self._tactile_sub = node.create_subscription(Float32MultiArray, self.config.tactile_topic, self._on_tactile, self.config.qos_depth)

    def spin_once(self, timeout_sec: float = 0.0) -> None:
        if not self.started or self._rclpy is None:
            raise Ros2Unavailable("bridge has not been started")
        self._rclpy.spin_once(self._node, timeout_sec=float(timeout_sec))  # pragma: no cover

    def close(self) -> None:
        if self._node is not None:  # pragma: no cover - requires ROS2 environment
            self._node.destroy_node()
        self._node = None

    def publish_bounded_command(self, command: Ros2Command) -> None:
        if not self.started or self._node is None:
            raise Ros2Unavailable("bridge has not been started")
        if command.force_cap_N < 0.0:
            raise ValueError("force_cap_N must be non-negative")
        msg = self._TwistStamped()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z = command.linear_xyz_mps
        msg.twist.angular.x, msg.twist.angular.y, msg.twist.angular.z = command.angular_xyz_rps
        self._twist_pub.publish(msg)
        event = self._String()
        event.data = json.dumps(
            {
                "kind": "bounded_command",
                "session_id": command.session_id,
                "request_id": command.request_id,
                "force_cap_N": command.force_cap_N,
                "reason_code": command.reason_code,
                "timestamp_s": time(),
            },
            sort_keys=True,
        )
        self._event_pub.publish(event)

    def publish_stop(self, *, session_id: str, reason_code: str) -> None:
        self.publish_bounded_command(
            Ros2Command(
                session_id=session_id,
                request_id="safety-stop",
                linear_xyz_mps=(0.0, 0.0, 0.0),
                angular_xyz_rps=(0.0, 0.0, 0.0),
                force_cap_N=0.0,
                reason_code=reason_code,
            )
        )

    def _on_wrench(self, msg: Any) -> None:  # pragma: no cover - callback tested via converter
        sample = wrench_stamped_to_sample(msg)
        with self._lock:
            self._last_wrench = sample

    def _on_tactile(self, msg: Any) -> None:  # pragma: no cover
        frame = tactile_multiarray_to_frame(msg)
        with self._lock:
            self._last_tactile = frame

    def _on_estop(self, msg: Any) -> None:  # pragma: no cover
        with self._lock:
            self._e_stop = bool(msg.data)
