"""
IX-HapticSight — Tests for benchmark models.

These tests verify the backend-agnostic benchmark scenario, observation, and
result structures introduced under `src/ohip_bench/`.
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_bench.models import (  # noqa: E402
    BenchmarkDomain,
    BenchmarkExpectation,
    BenchmarkMetric,
    BenchmarkObservation,
    BenchmarkOutcome,
    BenchmarkResult,
    BenchmarkScenario,
    compare_expectation,
)


def test_benchmark_metric_to_dict():
    metric = BenchmarkMetric(
        name="event_count",
        value=5,
        unit="count",
        note="structured events emitted",
    )

    data = metric.to_dict()

    assert data["name"] == "event_count"
    assert data["value"] == 5.0
    assert data["unit"] == "count"
    assert data["note"] == "structured events emitted"


def test_benchmark_expectation_to_dict():
    expectation = BenchmarkExpectation(
        expected_status="APPROVED",
        expected_executable=True,
        expected_fault_reason="",
        expected_execution_status="ACCEPTED",
    )

    data = expectation.to_dict()

    assert data["expected_status"] == "APPROVED"
    assert data["expected_executable"] is True
    assert data["expected_fault_reason"] == ""
    assert data["expected_execution_status"] == "ACCEPTED"


def test_benchmark_scenario_to_dict():
    scenario = BenchmarkScenario(
        scenario_id="consent-approved-001",
        title="Explicit consent allows support contact",
        domain=BenchmarkDomain.CONSENT,
        description="Contact request with valid explicit consent should approve.",
        inputs={
            "request_kind": "SUPPORT_CONTACT",
            "consent_mode": "EXPLICIT",
            "scopes": ["shoulder_contact"],
        },
        expectation=BenchmarkExpectation(
            expected_status="APPROVED",
            expected_executable=True,
            expected_execution_status="ACCEPTED",
        ),
        tags=("consent", "contact", "happy_path"),
    )

    data = scenario.to_dict()

    assert data["scenario_id"] == "consent-approved-001"
    assert data["title"] == "Explicit consent allows support contact"
    assert data["domain"] == "CONSENT"
    assert data["inputs"]["request_kind"] == "SUPPORT_CONTACT"
    assert data["expectation"]["expected_status"] == "APPROVED"
    assert data["tags"] == ["consent", "contact", "happy_path"]


def test_benchmark_observation_to_dict():
    observation = BenchmarkObservation(
        observed_status="DENIED",
        observed_executable=False,
        observed_fault_reason="consent_missing_or_invalid",
        observed_execution_status="",
        event_count=5,
    )

    data = observation.to_dict()

    assert data["observed_status"] == "DENIED"
    assert data["observed_executable"] is False
    assert data["observed_fault_reason"] == "consent_missing_or_invalid"
    assert data["observed_execution_status"] == ""
    assert data["event_count"] == 5


def test_benchmark_result_to_dict_and_duration():
    result = BenchmarkResult(
        scenario_id="consent-denied-001",
        domain=BenchmarkDomain.CONSENT,
        outcome=BenchmarkOutcome.PASS,
        observation=BenchmarkObservation(
            observed_status="DENIED",
            observed_executable=False,
            observed_fault_reason="consent_missing_or_invalid",
            observed_execution_status="",
            event_count=5,
        ),
        metrics=(
            BenchmarkMetric(name="event_count", value=5, unit="count"),
            BenchmarkMetric(name="decision_latency_ms", value=12.5, unit="ms"),
        ),
        reason_code="expectation_met",
        started_at_utc_s=100.0,
        finished_at_utc_s=100.025,
    )

    assert result.duration_ms == 25.0

    data = result.to_dict()
    assert data["scenario_id"] == "consent-denied-001"
    assert data["domain"] == "CONSENT"
    assert data["outcome"] == "PASS"
    assert data["observation"]["observed_status"] == "DENIED"
    assert data["metrics"][0]["name"] == "event_count"
    assert data["metrics"][1]["value"] == 12.5
    assert data["duration_ms"] == 25.0


def test_compare_expectation_passes_when_all_expected_fields_match():
    expectation = BenchmarkExpectation(
        expected_status="APPROVED",
        expected_executable=True,
        expected_fault_reason="",
        expected_execution_status="ACCEPTED",
    )
    observation = BenchmarkObservation(
        observed_status="APPROVED",
        observed_executable=True,
        observed_fault_reason="",
        observed_execution_status="ACCEPTED",
        event_count=6,
    )

    ok, reason = compare_expectation(
        expectation=expectation,
        observation=observation,
    )

    assert ok is True
    assert reason == "expectation_met"


def test_compare_expectation_detects_status_mismatch():
    expectation = BenchmarkExpectation(
        expected_status="APPROVED",
        expected_executable=True,
    )
    observation = BenchmarkObservation(
        observed_status="DENIED",
        observed_executable=False,
        observed_fault_reason="consent_missing_or_invalid",
        event_count=5,
    )

    ok, reason = compare_expectation(
        expectation=expectation,
        observation=observation,
    )

    assert ok is False
    assert reason == "status_mismatch:APPROVED!=DENIED"


def test_compare_expectation_detects_executable_mismatch():
    expectation = BenchmarkExpectation(
        expected_status="APPROVED",
        expected_executable=True,
    )
    observation = BenchmarkObservation(
        observed_status="APPROVED",
        observed_executable=False,
        observed_fault_reason="",
        event_count=5,
    )

    ok, reason = compare_expectation(
        expectation=expectation,
        observation=observation,
    )

    assert ok is False
    assert reason == "executable_mismatch:True!=False"


def test_compare_expectation_detects_fault_reason_mismatch():
    expectation = BenchmarkExpectation(
        expected_status="DENIED",
        expected_executable=False,
        expected_fault_reason="consent_missing_or_invalid",
    )
    observation = BenchmarkObservation(
        observed_status="DENIED",
        observed_executable=False,
        observed_fault_reason="session_safety_red",
        event_count=5,
    )

    ok, reason = compare_expectation(
        expectation=expectation,
        observation=observation,
    )

    assert ok is False
    assert reason == (
        "fault_reason_mismatch:"
        "consent_missing_or_invalid!=session_safety_red"
    )


def test_compare_expectation_detects_execution_status_mismatch():
    expectation = BenchmarkExpectation(
        expected_status="APPROVED",
        expected_executable=True,
        expected_execution_status="ACCEPTED",
    )
    observation = BenchmarkObservation(
        observed_status="APPROVED",
        observed_executable=True,
        observed_fault_reason="",
        observed_execution_status="REJECTED",
        event_count=6,
    )

    ok, reason = compare_expectation(
        expectation=expectation,
        observation=observation,
    )

    assert ok is False
    assert reason == "execution_status_mismatch:ACCEPTED!=REJECTED"
