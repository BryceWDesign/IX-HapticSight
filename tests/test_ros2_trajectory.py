import pytest

from ohip_ros2 import JointTrajectoryPointSpec, JointTrajectorySpec


def test_joint_trajectory_spec_validation():
    spec = JointTrajectorySpec(
        joint_names=("j1", "j2"),
        points=(
            JointTrajectoryPointSpec((0.0, 0.0), time_from_start_s=.5),
            JointTrajectoryPointSpec((.1, -.1), (.2, -.2), time_from_start_s=1.0),
        ),
    )
    spec.validate()


def test_joint_trajectory_rejects_non_monotonic_time():
    spec = JointTrajectorySpec(
        joint_names=("j1",),
        points=(
            JointTrajectoryPointSpec((0.0,), time_from_start_s=1.0),
            JointTrajectoryPointSpec((.1,), time_from_start_s=.5),
        ),
    )
    with pytest.raises(ValueError):
        spec.validate()
