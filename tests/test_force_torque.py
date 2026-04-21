"""
IX-HapticSight — Tests for normalized force/torque interface models.

These tests verify that the backend-agnostic force/torque layer can:
- normalize 3-axis force and torque payloads
- compute magnitudes correctly
- expose freshness/health usability checks
- derive compact contact-force assessments
"""

import math
import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_interfaces.force_torque import (  # noqa: E402
    ForceTorqueSample,
    assess_contact_force,
    make_force_torque_sample,
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
        sequence_id=7,
        source_name="wrist_ft",
        frame="tool0",
    )


def test_make_force_torque_sample_normalizes_vectors():
    sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.3, 0.4, 0.0],
        torque_xyz=[0.0, 0.0, 0.2],
        quality=make_quality(),
    )

    assert isinstance(sample, ForceTorqueSample)
    assert sample.frame == "tool0"
    assert sample.force.x == 0.3
    assert sample.force.y == 0.4
    assert sample.force.z == 0.0
    assert sample.torque.z == 0.2


def test_force_and_torque_magnitudes_are_computed_correctly():
    sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.3, 0.4, 0.0],
        torque_xyz=[0.0, 0.0, 0.5],
        quality=make_quality(),
    )

    assert math.isclose(sample.force_magnitude_N(), 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(sample.torque_magnitude_Nm(), 0.5, rel_tol=0.0, abs_tol=1e-12)


def test_force_torque_sample_respects_freshness_and_usability():
    policy = FreshnessPolicy(max_age_ms=250, required=True)

    fresh_sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.1, 0.1, 0.1],
        torque_xyz=[0.0, 0.0, 0.0],
        quality=make_quality(sample_t=50.0, received_t=50.002),
    )
    assert fresh_sample.is_fresh(policy, now_utc_s=50.20) is True
    assert fresh_sample.is_usable(policy, now_utc_s=50.20) is True

    stale_sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.1, 0.1, 0.1],
        torque_xyz=[0.0, 0.0, 0.0],
        quality=make_quality(sample_t=50.0, received_t=50.002),
    )
    assert stale_sample.is_fresh(policy, now_utc_s=50.30) is False
    assert stale_sample.is_usable(policy, now_utc_s=50.30) is False


def test_assess_contact_force_detects_contact_and_excessive_force():
    sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.0, 0.0, 1.25],
        torque_xyz=[0.0, 0.1, 0.0],
        quality=make_quality(),
    )

    assessment = assess_contact_force(
        sample,
        contact_threshold_N=0.25,
        excessive_threshold_N=1.0,
    )

    assert assessment.contact_detected is True
    assert assessment.excessive_force is True
    assert math.isclose(assessment.force_magnitude_N, 1.25, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(assessment.torque_magnitude_Nm, 0.1, rel_tol=0.0, abs_tol=1e-12)
    assert assessment.threshold_contact_N == 0.25
    assert assessment.threshold_excessive_N == 1.0


def test_assess_contact_force_can_report_no_contact():
    sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.05, 0.05, 0.05],
        torque_xyz=[0.0, 0.0, 0.0],
        quality=make_quality(),
    )

    assessment = assess_contact_force(
        sample,
        contact_threshold_N=0.25,
        excessive_threshold_N=1.0,
    )

    assert assessment.contact_detected is False
    assert assessment.excessive_force is False
    assert assessment.force_magnitude_N < 0.25


def test_make_force_torque_sample_rejects_bad_vector_lengths():
    try:
        make_force_torque_sample(
            frame="tool0",
            force_xyz=[1.0, 2.0],
            torque_xyz=[0.0, 0.0, 0.0],
            quality=make_quality(),
        )
        raised_force = False
    except ValueError:
        raised_force = True

    try:
        make_force_torque_sample(
            frame="tool0",
            force_xyz=[0.0, 0.0, 0.0],
            torque_xyz=[1.0, 2.0],
            quality=make_quality(),
        )
        raised_torque = False
    except ValueError:
        raised_torque = True

    assert raised_force is True
    assert raised_torque is True


def test_assess_contact_force_rejects_invalid_thresholds():
    sample = make_force_torque_sample(
        frame="tool0",
        force_xyz=[0.0, 0.0, 0.5],
        torque_xyz=[0.0, 0.0, 0.0],
        quality=make_quality(),
    )

    try:
        assess_contact_force(sample, contact_threshold_N=-0.1, excessive_threshold_N=1.0)
        raised_negative = False
    except ValueError:
        raised_negative = True

    try:
        assess_contact_force(sample, contact_threshold_N=1.0, excessive_threshold_N=0.5)
        raised_order = False
    except ValueError:
        raised_order = True

    assert raised_negative is True
    assert raised_order is True
