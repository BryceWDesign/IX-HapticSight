"""ROS 2 message conversion helpers.

These converters are deliberately duck-typed so their numeric behavior can be
tested without ROS 2 being installed. At runtime they accept standard
``geometry_msgs/WrenchStamped``-like and proximity message objects.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

from ohip.schemas import Vector3
from ohip_interfaces.force_torque import ForceTorqueSample
from ohip_interfaces.signal_health import SignalHealth, SignalQuality, SignalSourceMode
from ohip_interfaces.tactile import TactileFrame, make_tactile_patch


@dataclass(frozen=True)
class Ros2Command:
    session_id: str
    request_id: str
    linear_xyz_mps: tuple[float, float, float]
    angular_xyz_rps: tuple[float, float, float]
    force_cap_N: float
    reason_code: str


def _stamp_to_seconds(stamp: Any) -> float:
    sec = float(getattr(stamp, "sec", 0.0))
    nanosec = float(getattr(stamp, "nanosec", 0.0))
    value = sec + nanosec / 1_000_000_000.0
    return value if value > 0.0 else time()


def wrench_stamped_to_sample(msg: Any, *, source_id: str = "ros2_wrench") -> ForceTorqueSample:
    header = getattr(msg, "header", None)
    stamp = getattr(header, "stamp", None)
    frame_id = str(getattr(header, "frame_id", "tool"))
    wrench = getattr(msg, "wrench")
    force = getattr(wrench, "force")
    torque = getattr(wrench, "torque")
    ts = _stamp_to_seconds(stamp) if stamp is not None else time()
    quality = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=ts,
        received_timestamp_utc_s=time(),
        sequence_id=None,
        source_name=source_id,
        frame=frame_id,
        note="ROS2 WrenchStamped",
    )
    return ForceTorqueSample(
        frame=frame_id,
        force=Vector3(float(force.x), float(force.y), float(force.z)),
        torque=Vector3(float(torque.x), float(torque.y), float(torque.z)),
        quality=quality,
    )


def tactile_multiarray_to_frame(
    msg: Any,
    *,
    surface_name: str = "tool_tactile",
    frame: str = "tool",
    source_id: str = "ros2_tactile",
) -> TactileFrame:
    """Convert a ``std_msgs/Float32MultiArray``-like payload to tactile patches.

    The wire contract is ten floats per patch:
    ``x,y,z,nx,ny,nz,area_mm2,pressure_kpa,shear_x_kpa,shear_y_kpa``.
    A hardware driver or vendor bridge can publish this normalized topic without
    HapticSight depending on one proprietary tactile SDK.
    """
    values = [float(v) for v in getattr(msg, "data", ())]
    stride = 10
    if len(values) % stride != 0:
        raise ValueError("tactile Float32MultiArray length must be a multiple of 10")
    now = time()
    quality = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=now,
        received_timestamp_utc_s=now,
        source_name=source_id,
        frame=frame,
        note="ROS2 Float32MultiArray normalized tactile patches",
    )
    patches = []
    for index in range(0, len(values), stride):
        chunk = values[index:index + stride]
        patches.append(make_tactile_patch(
            patch_id=f"patch-{index // stride}",
            location_xyz=chunk[0:3],
            normal_xyz=chunk[3:6],
            area_mm2=chunk[6],
            pressure_kpa=chunk[7],
            shear_xy_kpa=chunk[8:10],
        ))
    return TactileFrame(surface_name=surface_name, frame=frame, quality=quality, patches=tuple(patches))
