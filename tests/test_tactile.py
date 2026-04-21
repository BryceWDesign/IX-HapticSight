"""
IX-HapticSight — Tests for normalized tactile interface models.

These tests verify that the backend-agnostic tactile layer can:
- normalize tactile patches safely
- compute patch, area, pressure, and shear summaries
- expose freshness/health usability checks
- derive compact tactile contact assessments
"""

import math
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
from ohip_interfaces.tactile import (  # noqa: E402
    TactileFrame,
    assess_tactile_contact,
    make_tactile_patch,
)


def make_quality(*, sample_t: float = 100.0, received_t: float = 100.01) -> SignalQuality:
    return SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=sample_t,
        received_timestamp_utc_s=received_t,
        sequence_id=21,
        source_name="forearm_tactile",
        frame="forearm_link",
    )


def test_make_tactile_patch_normalizes_values():
    patch = make_tactile_patch(
        patch_id="p1",
        location_xyz=[0.01, 0.02, 0.03],
        normal_xyz=[0.0, 0.0, 1.0],
        area_mm2=15.5,
        pressure_kpa=2.2,
        shear_xy_kpa=[0.5, 0.25],
    )

    assert patch.patch_id == "p1"
    assert patch.location_xyz.x == 0.01
    assert patch.location_xyz.y == 0.02
    assert patch.location_xyz.z == 0.03
    assert patch.normal_xyz.z == 1.0
    assert patch.area_mm2 == 15.5
    assert patch.pressure_kpa == 2.2
    assert patch.shear_xy_kpa == (0.5, 0.25)


def test_tactile_patch_shear_magnitude_is_computed_correctly():
    patch = make_tactile_patch(
        patch_id="p2",
        location_xyz=[0.0, 0.0, 0.0],
        normal_xyz=[0.0, 1.0, 0.0],
        area_mm2=10.0,
        pressure_kpa=1.0,
        shear_xy_kpa=[3.0, 4.0],
    )

    assert math.isclose(patch.shear_magnitude_kpa(), 5.0, rel_tol=0.0, abs_tol=1e-12)


def test_tactile_frame_summaries_work_for_multiple_patches():
    patch_a = make_tactile_patch(
        patch_id="a",
        location_xyz=[0.01, 0.01, 0.00],
        normal_xyz=[0.0, 0.0, 1.0],
        area_mm2=12.0,
        pressure_kpa=2.0,
        shear_xy_kpa=[0.3, 0.4],
    )
    patch_b = make_tactile_patch(
        patch_id="b",
        location_xyz=[0.02, 0.02, 0.00],
        normal_xyz=[0.0, 0.0, 1.0],
        area_mm2=18.0,
        pressure_kpa=4.5,
        shear_xy_kpa=[0.0, 1.2],
    )

    frame = TactileFrame(
        surface_name="forearm_pad",
        frame="forearm_link",
        quality=make_quality(),
        patches=(patch_a, patch_b),
    )

    assert frame.patch_count() == 2
    assert frame.has_contact() is True
    assert frame.total_area_mm2() == 30.0
    assert frame.max_pressure_kpa() == 4.5
    assert frame.max_shear_kpa() == 1.2


def test_tactile_frame_respects_freshness_and_usability():
    policy = FreshnessPolicy(max_age_ms=250, required=True)

    frame = TactileFrame(
        surface_name="palm_pad",
        frame="palm_link",
        quality=make_quality(sample_t=50.0, received_t=50.002),
        patches=(),
    )

    assert frame.is_fresh(policy, now_utc_s=50.20) is True
    assert frame.is_usable(policy, now_utc_s=50.20) is True
    assert frame.is_fresh(policy, now_utc_s=50.30) is False
    assert frame.is_usable(policy, now_utc_s=50.30) is False


def test_assess_tactile_contact_detects_contact_and_excessive_values():
    patch_a = make_tactile_patch(
        patch_id="a",
        location_xyz=[0.0, 0.0, 0.0],
        normal_xyz=[0.0, 0.0, 1.0],
        area_mm2=20.0,
        pressure_kpa=6.0,
        shear_xy_kpa=[1.0, 1.0],
    )
    patch_b = make_tactile_patch(
        patch_id="b",
        location_xyz=[0.0, 0.0, 0.0],
        normal_xyz=[0.0, 0.0, 1.0],
        area_mm2=10.0,
        pressure_kpa=12.0,
        shear_xy_kpa=[4.0, 4.0],
    )

    frame = TactileFrame(
        surface_name="forearm_pad",
        frame="forearm_link",
        quality=make_quality(),
        patches=(patch_a, patch_b),
    )

    assessment = assess_tactile_contact(
        frame,
        pressure_threshold_kpa=0.5,
        excessive_pressure_threshold_kpa=10.0,
        excessive_shear_threshold_kpa=5.0,
    )

    assert assessment.contact_detected is True
    assert assessment.multi_patch_contact is True
    assert assessment.patch_count == 2
    assert assessment.total_area_mm2 == 30.0
    assert assessment.max_pressure_kpa == 12.0
    assert math.isclose(assessment.max_shear_kpa, math.sqrt(32.0), rel_tol=0.0, abs_tol=1e-12)
    assert assessment.excessive_pressure is True
    assert assessment.excessive_shear is True


def test_assess_tactile_contact_can_report_no_contact():
    frame = TactileFrame(
        surface_name="palm_pad",
        frame="palm_link",
        quality=make_quality(),
        patches=(),
    )

    assessment = assess_tactile_contact(
        frame,
        pressure_threshold_kpa=0.5,
        excessive_pressure_threshold_kpa=10.0,
        excessive_shear_threshold_kpa=5.0,
    )

    assert assessment.contact_detected is False
    assert assessment.multi_patch_contact is False
    assert assessment.patch_count == 0
    assert assessment.total_area_mm2 == 0.0
    assert assessment.max_pressure_kpa == 0.0
    assert assessment.max_shear_kpa == 0.0
    assert assessment.excessive_pressure is False
    assert assessment.excessive_shear is False


def test_make_tactile_patch_rejects_invalid_inputs():
    try:
        make_tactile_patch(
            patch_id="bad-loc",
            location_xyz=[0.0, 0.0],
            normal_xyz=[0.0, 0.0, 1.0],
            area_mm2=1.0,
            pressure_kpa=1.0,
        )
        bad_loc = False
    except ValueError:
        bad_loc = True

    try:
        make_tactile_patch(
            patch_id="bad-normal",
            location_xyz=[0.0, 0.0, 0.0],
            normal_xyz=[0.0, 1.0],
            area_mm2=1.0,
            pressure_kpa=1.0,
        )
        bad_normal = False
    except ValueError:
        bad_normal = True

    try:
        make_tactile_patch(
            patch_id="bad-shear",
            location_xyz=[0.0, 0.0, 0.0],
            normal_xyz=[0.0, 0.0, 1.0],
            area_mm2=1.0,
            pressure_kpa=1.0,
            shear_xy_kpa=[1.0],
        )
        bad_shear = False
    except ValueError:
        bad_shear = True

    try:
        make_tactile_patch(
            patch_id="bad-area",
            location_xyz=[0.0, 0.0, 0.0],
            normal_xyz=[0.0, 0.0, 1.0],
            area_mm2=-1.0,
            pressure_kpa=1.0,
        )
        bad_area = False
    except ValueError:
        bad_area = True

    try:
        make_tactile_patch(
            patch_id="bad-pressure",
            location_xyz=[0.0, 0.0, 0.0],
            normal_xyz=[0.0, 0.0, 1.0],
            area_mm2=1.0,
            pressure_kpa=-0.1,
        )
        bad_pressure = False
    except ValueError:
        bad_pressure = True

    assert bad_loc is True
    assert bad_normal is True
    assert bad_shear is True
    assert bad_area is True
    assert bad_pressure is True


def test_assess_tactile_contact_rejects_invalid_thresholds():
    frame = TactileFrame(
        surface_name="pad",
        frame="pad_link",
        quality=make_quality(),
        patches=(),
    )

    try:
        assess_tactile_contact(
            frame,
            pressure_threshold_kpa=-0.1,
            excessive_pressure_threshold_kpa=10.0,
            excessive_shear_threshold_kpa=5.0,
        )
        bad_pressure_threshold = False
    except ValueError:
        bad_pressure_threshold = True

    try:
        assess_tactile_contact(
            frame,
            pressure_threshold_kpa=1.0,
            excessive_pressure_threshold_kpa=0.5,
            excessive_shear_threshold_kpa=5.0,
        )
        bad_excessive_pressure = False
    except ValueError:
        bad_excessive_pressure = True

    try:
        assess_tactile_contact(
            frame,
            pressure_threshold_kpa=0.5,
            excessive_pressure_threshold_kpa=10.0,
            excessive_shear_threshold_kpa=-1.0,
        )
        bad_shear_threshold = False
    except ValueError:
        bad_shear_threshold = True

    assert bad_pressure_threshold is True
    assert bad_excessive_pressure is True
    assert bad_shear_threshold is True
