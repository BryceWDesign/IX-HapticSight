"""
IX-HapticSight — Tests for interface signal health and freshness models.

These tests verify the backend-agnostic signal metadata layer that sits between
raw sensing and runtime safety/coordination logic.
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_interfaces.signal_health import (  # noqa: E402
    FreshnessPolicy,
    MultiSignalFreshness,
    SignalHealth,
    SignalQuality,
    SignalSourceMode,
)


def test_freshness_policy_respects_age_threshold():
    policy = FreshnessPolicy(max_age_ms=250, required=True)

    assert policy.is_fresh(sample_timestamp_utc_s=100.0, now_utc_s=100.20) is True
    assert policy.is_fresh(sample_timestamp_utc_s=100.0, now_utc_s=100.251) is False


def test_signal_quality_age_and_transport_latency_are_non_negative():
    quality = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=100.0,
        received_timestamp_utc_s=100.015,
        sequence_id=12,
        source_name="wrist_ft",
        frame="tool0",
    )

    assert quality.age_ms(now_utc_s=100.100) == 100.0
    assert quality.transport_latency_ms() == 15.0


def test_signal_quality_is_usable_requires_health_and_freshness_when_required():
    policy = FreshnessPolicy(max_age_ms=200, required=True)

    nominal_fresh = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=50.0,
        received_timestamp_utc_s=50.005,
    )
    assert nominal_fresh.is_fresh(policy, now_utc_s=50.150) is True
    assert nominal_fresh.is_usable(policy, now_utc_s=50.150) is True

    nominal_stale = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=50.0,
        received_timestamp_utc_s=50.005,
    )
    assert nominal_stale.is_fresh(policy, now_utc_s=50.2501) is False
    assert nominal_stale.is_usable(policy, now_utc_s=50.2501) is False

    degraded_fresh = SignalQuality(
        source_mode=SignalSourceMode.SIMULATION,
        health=SignalHealth.DEGRADED,
        sample_timestamp_utc_s=10.0,
        received_timestamp_utc_s=10.001,
    )
    assert degraded_fresh.is_usable(policy, now_utc_s=10.050) is True

    invalid_signal = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.INVALID,
        sample_timestamp_utc_s=10.0,
        received_timestamp_utc_s=10.001,
    )
    assert invalid_signal.is_usable(policy, now_utc_s=10.050) is False

    unavailable_signal = SignalQuality(
        source_mode=SignalSourceMode.LIVE,
        health=SignalHealth.UNAVAILABLE,
        sample_timestamp_utc_s=10.0,
        received_timestamp_utc_s=10.001,
    )
    assert unavailable_signal.is_usable(policy, now_utc_s=10.050) is False


def test_signal_quality_optional_policy_allows_stale_but_not_invalid():
    optional_policy = FreshnessPolicy(max_age_ms=100, required=False)

    stale_but_nominal = SignalQuality(
        source_mode=SignalSourceMode.REPLAY,
        health=SignalHealth.NOMINAL,
        sample_timestamp_utc_s=20.0,
        received_timestamp_utc_s=20.002,
    )
    assert stale_but_nominal.is_fresh(optional_policy, now_utc_s=20.250) is False
    assert stale_but_nominal.is_usable(optional_policy, now_utc_s=20.250) is True

    stale_and_invalid = SignalQuality(
        source_mode=SignalSourceMode.REPLAY,
        health=SignalHealth.INVALID,
        sample_timestamp_utc_s=20.0,
        received_timestamp_utc_s=20.002,
    )
    assert stale_and_invalid.is_usable(optional_policy, now_utc_s=20.250) is False


def test_signal_quality_freshness_summary_contains_expected_fields():
    policy = FreshnessPolicy(max_age_ms=150, required=True)
    quality = SignalQuality(
        source_mode=SignalSourceMode.BENCHMARK,
        health=SignalHealth.DEGRADED,
        sample_timestamp_utc_s=75.0,
        received_timestamp_utc_s=75.010,
        sequence_id=88,
        source_name="sim_proximity",
        frame="W",
        note="test run",
    )

    summary = quality.freshness_summary(policy, now_utc_s=75.100)

    assert summary["source_mode"] == "BENCHMARK"
    assert summary["health"] == "DEGRADED"
    assert summary["age_ms"] == 100.0
    assert summary["max_age_ms"] == 150
    assert summary["required"] is True
    assert summary["fresh"] is True
    assert summary["usable"] is True
    assert summary["sequence_id"] == 88
    assert summary["source_name"] == "sim_proximity"
    assert summary["frame"] == "W"
    assert summary["note"] == "test run"


def test_multi_signal_freshness_all_required_and_any_available():
    freshness = MultiSignalFreshness(
        force_torque=True,
        tactile=False,
        proximity=True,
        thermal=True,
        scene=False,
    )

    assert freshness.any_available() is True

    assert freshness.all_required(
        require_force_torque=True,
        require_proximity=True,
        require_thermal=True,
    ) is True

    assert freshness.all_required(
        require_force_torque=True,
        require_tactile=True,
    ) is False

    none_available = MultiSignalFreshness()
    assert none_available.any_available() is False
