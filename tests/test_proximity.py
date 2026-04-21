"""
IX-HapticSight — Tests for normalized proximity interface models.

These tests verify that the backend-agnostic proximity layer can:
- normalize proximity returns safely
- compute nearest and range summaries
- expose freshness/health usability checks
- derive compact proximity assessments for near-contact and corridor checks
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_interfaces.proximity import (  # noqa: E402
    ProximityFrame,
    assess_proximity,
    make_proximity_return,
)
from ohip_interfaces.signal_health import (  # noqa: E402
    FreshnessPolicy,
    SignalHealth,
    SignalQuality,
    SignalSourceMode,
)


def make_quality(*, sample_t: float = 100.0, received_t: float = 100.01) -> SignalQuality:
    return SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=sample_t,
        received_timestamp_utc_s=received_t,
        sequence_id=31,
        source_name="forearm_proximity",
        frame="forearm_link",
    )


def test_make_proximity_return_normalizes_values():
    prox = make_proximity_return(
        zone_id="z1",
        distance_mm=85.0,
        direction_xyz=[0.0, 0.0, 1.0],
        point_xyz=[0.01, 0.02, 0.03],
        confidence=0.9,
    )

    assert prox.zone_id == "z1"
    assert prox.distance_mm == 85.0
    assert prox.direction_xyz.z == 1.0
    assert prox.point_xyz is not None
    assert prox.point_xyz.x == 0.01
    assert prox.point_xyz.y == 0.02
    assert prox.point_xyz.z == 0.03
    assert prox.confidence == 0.9


def test_proximity_frame_summaries_work_for_multiple_returns():
    ret_a = make_proximity_return(
        zone_id="a",
        distance_mm=120.0,
        direction_xyz=[1.0, 0.0, 0.0],
        confidence=0.8,
    )
    ret_b = make_proximity_return(
        zone_id="b",
        distance_mm=55.0,
        direction_xyz=[0.0, 1.0, 0.0],
        confidence=1.0,
    )
    ret_c = make_proximity_return(
        zone_id="c",
        distance_mm=200.0,
        direction_xyz=[0.0, 0.0, 1.0],
        confidence=0.7,
    )

    frame = ProximityFrame(
        sensor_name="forearm_ring",
        frame="forearm_link",
        quality=make_quality(),
        returns=(ret_a, ret_b, ret_c),
    )

    assert frame.return_count() == 3
    assert frame.has_returns() is True
    assert frame.min_distance_mm() == 55.0
    assert frame.max_distance_mm() == 200.0
    nearest = frame.nearest_return()
    assert nearest is not None
    assert nearest.zone_id == "b"
    assert nearest.distance_mm == 55.0


def test_proximity_frame_handles_empty_returns():
    frame = ProximityFrame(
        sensor_name="forearm_ring",
        frame="forearm_link",
        quality=make_quality(),
        returns=(),
    )

    assert frame.return_count() == 0
    assert frame.has_returns() is False
    assert frame.min_distance_mm() is None
    assert frame.max_distance_mm() is None
    assert frame.nearest_return() is None


def test_proximity_frame_respects_freshness_and_usability():
    policy = FreshnessPolicy(max_age_ms=250, required=True)

    frame = ProximityFrame(
        sensor_name="palm_ring",
        frame="palm_link",
        quality=make_quality(sample_t=50.0, received_t=50.002),
        returns=(),
    )

    assert frame.is_fresh(policy, now_utc_s=50.20) is True
    assert frame.is_usable(policy, now_utc_s=50.20) is True
    assert frame.is_fresh(policy, now_utc_s=50.30) is False
    assert frame.is_usable(policy, now_utc_s=50.30) is False


def test_assess_proximity_detects_near_contact_and_stop_zone():
    ret_a = make_proximity_return(
        zone_id="a",
        distance_mm=35.0,
        direction_xyz=[1.0, 0.0, 0.0],
        confidence=1.0,
    )
    ret_b = make_proximity_return(
        zone_id="b",
        distance_mm=90.0,
        direction_xyz=[0.0, 1.0, 0.0],
        confidence=1.0,
    )

    frame = ProximityFrame(
        sensor_name="wrist_ring",
        frame="tool0",
        quality=make_quality(),
        returns=(ret_a, ret_b),
    )

    assessment = assess_proximity(
        frame,
        caution_distance_mm=120.0,
        stop_distance_mm=40.0,
    )

    assert assessment.object_detected is True
    assert assessment.near_contact is True
    assert assessment.corridor_clear is False
    assert assessment.return_count == 2
    assert assessment.nearest_distance_mm == 35.0
    assert assessment.caution_distance_mm == 120.0
    assert assessment.stop_distance_mm == 40.0


def test_assess_proximity_can_report_caution_without_stop_violation():
    ret = make_proximity_return(
        zone_id="only",
        distance_mm=75.0,
        direction_xyz=[0.0, 0.0, 1.0],
        confidence=0.95,
    )

    frame = ProximityFrame(
        sensor_name="wrist_ring",
        frame="tool0",
        quality=make_quality(),
        returns=(ret,),
    )

    assessment = assess_proximity(
        frame,
        caution_distance_mm=120.0,
        stop_distance_mm=40.0,
    )

    assert assessment.object_detected is True
    assert assessment.near_contact is True
    assert assessment.corridor_clear is True
    assert assessment.nearest_distance_mm == 75.0


def test_assess_proximity_can_report_clear_corridor_when_no_returns():
    frame = ProximityFrame(
        sensor_name="wrist_ring",
        frame="tool0",
        quality=make_quality(),
        returns=(),
    )

    assessment = assess_proximity(
        frame,
        caution_distance_mm=120.0,
        stop_distance_mm=40.0,
    )

    assert assessment.object_detected is False
    assert assessment.near_contact is False
    assert assessment.corridor_clear is True
    assert assessment.return_count == 0
    assert assessment.nearest_distance_mm is None


def test_make_proximity_return_rejects_invalid_inputs():
    try:
        make_proximity_return(
            zone_id="bad-dir",
            distance_mm=50.0,
            direction_xyz=[1.0, 0.0],
        )
        bad_dir = False
    except ValueError:
        bad_dir = True

    try:
        make_proximity_return(
            zone_id="bad-point",
            distance_mm=50.0,
            direction_xyz=[1.0, 0.0, 0.0],
            point_xyz=[0.0, 1.0],
        )
        bad_point = False
    except ValueError:
        bad_point = True

    try:
        make_proximity_return(
            zone_id="bad-distance",
            distance_mm=-1.0,
            direction_xyz=[1.0, 0.0, 0.0],
        )
        bad_distance = False
    except ValueError:
        bad_distance = True

    try:
        make_proximity_return(
            zone_id="bad-confidence-low",
            distance_mm=10.0,
            direction_xyz=[1.0, 0.0, 0.0],
            confidence=-0.1,
        )
        bad_conf_low = False
    except ValueError:
        bad_conf_low = True

    try:
        make_proximity_return(
            zone_id="bad-confidence-high",
            distance_mm=10.0,
            direction_xyz=[1.0, 0.0, 0.0],
            confidence=1.1,
        )
        bad_conf_high = False
    except ValueError:
        bad_conf_high = True

    assert bad_dir is True
    assert bad_point is True
    assert bad_distance is True
    assert bad_conf_low is True
    assert bad_conf_high is True


def test_assess_proximity_rejects_invalid_thresholds():
    frame = ProximityFrame(
        sensor_name="ring",
        frame="tool0",
        quality=make_quality(),
        returns=(),
    )

    try:
        assess_proximity(
            frame,
            caution_distance_mm=-1.0,
            stop_distance_mm=40.0,
        )
        bad_caution = False
    except ValueError:
        bad_caution = True

    try:
        assess_proximity(
            frame,
            caution_distance_mm=120.0,
            stop_distance_mm=-1.0,
        )
        bad_stop = False
    except ValueError:
        bad_stop = True

    try:
        assess_proximity(
            frame,
            caution_distance_mm=40.0,
            stop_distance_mm=120.0,
        )
        bad_order = False
    except ValueError:
        bad_order = True

    assert bad_caution is True
    assert bad_stop is True
    assert bad_order is True
