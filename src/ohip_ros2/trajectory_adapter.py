"""Optional ROS 2 FollowJointTrajectory adapter for real-robot integration.

This module intentionally separates *capability implementation* from *measured
hardware evidence*. It can submit bounded joint trajectories to a standard ROS
2 controller, but the repository does not claim that a physical robot has been
run unless an external HIL evidence bundle is supplied.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class Ros2TrajectoryUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class JointTrajectoryPointSpec:
    positions: tuple[float, ...]
    velocities: tuple[float, ...] = ()
    time_from_start_s: float = 1.0


@dataclass(frozen=True)
class JointTrajectorySpec:
    joint_names: tuple[str, ...]
    points: tuple[JointTrajectoryPointSpec, ...]

    def validate(self) -> None:
        if not self.joint_names:
            raise ValueError("joint_names must not be empty")
        if not self.points:
            raise ValueError("trajectory must contain at least one point")
        n = len(self.joint_names)
        previous = -1.0
        for point in self.points:
            if len(point.positions) != n:
                raise ValueError("each positions vector must match joint_names")
            if point.velocities and len(point.velocities) != n:
                raise ValueError("each velocities vector must match joint_names")
            if point.time_from_start_s <= previous:
                raise ValueError("time_from_start_s must be strictly increasing")
            previous = point.time_from_start_s


class FollowJointTrajectoryClient:
    """Thin action client around ``control_msgs/FollowJointTrajectory``."""

    def __init__(self, *, action_name: str = "/joint_trajectory_controller/follow_joint_trajectory") -> None:
        self.action_name = action_name
        self._node = None
        self._client = None
        self._rclpy = None

    def start(self, node_name: str = "ix_hapticsight_trajectory_client") -> None:
        try:
            import rclpy
            from rclpy.action import ActionClient
            from control_msgs.action import FollowJointTrajectory
        except Exception as exc:  # pragma: no cover
            raise Ros2TrajectoryUnavailable("ROS2 control_msgs/rclpy not installed") from exc
        if not rclpy.ok():
            rclpy.init(args=None)
        self._rclpy = rclpy
        self._FollowJointTrajectory = FollowJointTrajectory
        self._node = rclpy.create_node(node_name)
        self._client = ActionClient(self._node, FollowJointTrajectory, self.action_name)

    def submit(self, spec: JointTrajectorySpec, *, timeout_sec: float = 5.0):
        spec.validate()
        if self._client is None or self._node is None:
            raise Ros2TrajectoryUnavailable("client has not been started")
        if not self._client.wait_for_server(timeout_sec=float(timeout_sec)):  # pragma: no cover
            raise Ros2TrajectoryUnavailable(f"trajectory action server unavailable: {self.action_name}")
        from trajectory_msgs.msg import JointTrajectoryPoint  # pragma: no cover
        goal = self._FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = list(spec.joint_names)
        for point in spec.points:
            ros_point = JointTrajectoryPoint()
            ros_point.positions = list(point.positions)
            ros_point.velocities = list(point.velocities)
            sec = int(point.time_from_start_s)
            nanosec = int((point.time_from_start_s - sec) * 1_000_000_000)
            ros_point.time_from_start.sec = sec
            ros_point.time_from_start.nanosec = nanosec
            goal.trajectory.points.append(ros_point)
        return self._client.send_goal_async(goal)  # pragma: no cover
