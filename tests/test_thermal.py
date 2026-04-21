"""
IX-HapticSight — Tests for normalized thermal interface models.

These tests verify that the backend-agnostic thermal layer can:
- normalize thermal samples safely
- compute hottest and range summaries
- expose freshness/health usability checks
- derive compact thermal assessments for caution and stop thresholds
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_interfaces.signal_health import (  # noqa: E402
    FreshnessPolicy,
    SignalHealth,
    SignalQuality,
    SignalSourceMode,
)
from ohip_interfaces.thermal import (  # noqa: E402
    ThermalFrame,
    assess_thermal,
    make_thermal_sample,
)


def make_quality(*, sample_t: float = 100.0, received_t: float = 100.01) -> SignalQuality:
    return SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=sample_t,
        received_timestamp_utc_s=received_t,
        sequence_id=41,
        source_name="surface_thermal",
        frame="forearm_link",
    )


def test_make_thermal_sample_normalizes_values():
    sample = make_thermal_sample(
        zone_id="z1",
        temperature_c=36.5,
        location_xyz=[0.01, 0.02, 0.03],
        confidence=0.95,
    )

    assert sample.zone_id == "z1"
    assert sample.temperature_c == 36.5
    assert sample.location_xyz is not None
    assert sample.location_xyz.x == 0.01
    assert sample.location_xyz.y == 0.02
    assert sample.location_xyz.z == 0.03
    assert sample.confidence == 0.95


def test_thermal_frame_summaries_work_for_multiple_samples():
    sample_a = make_thermal_sample(
        zone_id="a",
        temperature_c=34.0,
        location_xyz=[0.0, 0.0, 0.0],
        confidence=1.0,
    )
    sample_b = make_thermal_sample(
        zone_id="b",
        temperature_c=41.2,
        location_xyz=[0.1, 0.0, 0.0],
        confidence=0.9,
    )
    sample_c = make_thermal_sample(
        zone_id="c",
        temperature_c=37.8,
        location_xyz=[0.2, 0.0, 0.0],
        confidence=0.8,
    )

    frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(sample_a, sample_b, sample_c),
    )

    assert frame.sample_count() == 3
    assert frame.has_samples() is True
    assert frame.min_temperature_c() == 34.0
    assert frame.max_temperature_c() == 41.2

    hottest = frame.hottest_sample()
    assert hottest is not None
    assert hottest.zone_id == "b"
    assert hottest.temperature_c == 41.2


def test_thermal_frame_handles_empty_samples():
    frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(),
    )

    assert frame.sample_count() == 0
    assert frame.has_samples() is False
    assert frame.min_temperature_c() is None
    assert frame.max_temperature_c() is None
    assert frame.hottest_sample() is None


def test_thermal_frame_respects_freshness_and_usability():
    policy = FreshnessPolicy(max_age_ms=250, required=True)

    frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(sample_t=50.0, received_t=50.002),
        samples=(),
    )

    assert frame.is_fresh(policy, now_utc_s=50.20) is True
    assert frame.is_usable(policy, now_utc_s=50.20) is True
    assert frame.is_fresh(policy, now_utc_s=50.30) is False
    assert frame.is_usable(policy, now_utc_s=50.30) is False


def test_assess_thermal_detects_caution_and_stop_thresholds():
    sample_a = make_thermal_sample(
        zone_id="a",
        temperature_c=37.9,
        confidence=1.0,
    )
    sample_b = make_thermal_sample(
        zone_id="b",
        temperature_c=46.2,
        confidence=1.0,
    )

    frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(sample_a, sample_b),
    )

    assessment = assess_thermal(
        frame,
        caution_temperature_c=38.0,
        stop_temperature_c=45.0,
    )

    assert assessment.heat_detected is True
    assert assessment.over_limit is True
    assert assessment.sample_count == 2
    assert assessment.hottest_temperature_c == 46.2
    assert assessment.caution_temperature_c == 38.0
    assert assessment.stop_temperature_c == 45.0


def test_assess_thermal_can_report_below_threshold_or_empty():
    below_frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(
            make_thermal_sample(zone_id="a", temperature_c=35.0),
            make_thermal_sample(zone_id="b", temperature_c=37.5),
        ),
    )

    below_assessment = assess_thermal(
        below_frame,
        caution_temperature_c=38.0,
        stop_temperature_c=45.0,
    )

    assert below_assessment.heat_detected is False
    assert below_assessment.over_limit is False
    assert below_assessment.hottest_temperature_c == 37.5

    empty_frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(),
    )

    empty_assessment = assess_thermal(
        empty_frame,
        caution_temperature_c=38.0,
        stop_temperature_c=45.0,
    )

    assert empty_assessment.heat_detected is False
    assert empty_assessment.over_limit is False
    assert empty_assessment.sample_count == 0
    assert empty_assessment.hottest_temperature_c is None


def test_make_thermal_sample_rejects_invalid_inputs():
    try:
        make_thermal_sample(
            zone_id="bad-location",
            temperature_c=36.0,
            location_xyz=[0.0, 1.0],
        )
        bad_location = False
    except ValueError:
        bad_location = True

    try:
        make_thermal_sample(
            zone_id="bad-confidence-low",
            temperature_c=36.0,
            confidence=-0.1,
        )
        bad_conf_low = False
    except ValueError:
        bad_conf_low = True

    try:
        make_thermal_sample(
            zone_id="bad-confidence-high",
            temperature_c=36.0,
            confidence=1.1,
        )
        bad_conf_high = False
    except ValueError:
        bad_conf_high = True

    assert bad_location is True
    assert bad_conf_low is True
    assert bad_conf_high is True


def test_assess_thermal_rejects_invalid_threshold_order():
    frame = ThermalFrame(
        sensor_name="surface_array",
        frame="forearm_link",
        quality=make_quality(),
        samples=(),
    )

    try:
        assess_thermal(
            frame,
            caution_temperature_c=45.0,
            stop_temperature_c=38.0,
        )
        raised = False
    except ValueError:
        raised = True

    assert raised is True
