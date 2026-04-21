"""
IX-HapticSight — Tests for benchmark reporting helpers.

These tests verify that the benchmark reporting layer can:
- summarize benchmark result sets
- group results by domain and outcome
- compute per-domain pass rates
- export report-friendly dictionaries
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_bench.models import (  # noqa: E402
    BenchmarkDomain,
    BenchmarkObservation,
    BenchmarkOutcome,
    BenchmarkResult,
)
from ohip_bench.reporting import (  # noqa: E402
    BenchmarkSummary,
    domain_pass_rate,
    export_results,
    results_by_domain,
    results_by_outcome,
    summarize_results,
)


def make_result(
    *,
    scenario_id: str,
    domain: BenchmarkDomain,
    outcome: BenchmarkOutcome,
    observed_status: str,
    duration_ms: float,
) -> BenchmarkResult:
    start = 100.0
    finish = start + (duration_ms / 1000.0)
    return BenchmarkResult(
        scenario_id=scenario_id,
        domain=domain,
        outcome=outcome,
        observation=BenchmarkObservation(
            observed_status=observed_status,
            observed_executable=(observed_status == "APPROVED"),
            observed_fault_reason="" if observed_status == "APPROVED" else "fault_reason",
            observed_execution_status="ACCEPTED" if observed_status == "APPROVED" else "",
            event_count=5,
        ),
        metrics=(),
        reason_code="reason",
        started_at_utc_s=start,
        finished_at_utc_s=finish,
    )


def test_summarize_results_counts_and_average_duration():
    results = [
        make_result(
            scenario_id="r1",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=10.0,
        ),
        make_result(
            scenario_id="r2",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.FAIL,
            observed_status="DENIED",
            duration_ms=20.0,
        ),
        make_result(
            scenario_id="r3",
            domain=BenchmarkDomain.SAFETY,
            outcome=BenchmarkOutcome.ERROR,
            observed_status="ERROR",
            duration_ms=30.0,
        ),
        make_result(
            scenario_id="r4",
            domain=BenchmarkDomain.REPLAY,
            outcome=BenchmarkOutcome.SKIPPED,
            observed_status="SKIPPED",
            duration_ms=40.0,
        ),
    ]

    summary = summarize_results(results)

    assert isinstance(summary, BenchmarkSummary)
    assert summary.total == 4
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.errored == 1
    assert summary.skipped == 1
    assert summary.average_duration_ms == 25.0
    assert summary.by_domain == {
        "CONSENT": 2,
        "SAFETY": 1,
        "REPLAY": 1,
    }
    assert summary.by_outcome == {
        "PASS": 1,
        "FAIL": 1,
        "ERROR": 1,
        "SKIPPED": 1,
    }


def test_summarize_results_empty_set():
    summary = summarize_results([])

    assert summary.total == 0
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.errored == 0
    assert summary.skipped == 0
    assert summary.average_duration_ms == 0.0
    assert summary.by_domain == {}
    assert summary.by_outcome == {}


def test_results_grouping_helpers():
    results = [
        make_result(
            scenario_id="r1",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=10.0,
        ),
        make_result(
            scenario_id="r2",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.FAIL,
            observed_status="DENIED",
            duration_ms=20.0,
        ),
        make_result(
            scenario_id="r3",
            domain=BenchmarkDomain.SAFETY,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=30.0,
        ),
    ]

    grouped_by_domain = results_by_domain(results)
    assert list(grouped_by_domain.keys()) == ["CONSENT", "SAFETY"]
    assert [result.scenario_id for result in grouped_by_domain["CONSENT"]] == ["r1", "r2"]
    assert [result.scenario_id for result in grouped_by_domain["SAFETY"]] == ["r3"]

    grouped_by_outcome = results_by_outcome(results)
    assert list(grouped_by_outcome.keys()) == ["PASS", "FAIL"]
    assert [result.scenario_id for result in grouped_by_outcome["PASS"]] == ["r1", "r3"]
    assert [result.scenario_id for result in grouped_by_outcome["FAIL"]] == ["r2"]


def test_domain_pass_rate():
    results = [
        make_result(
            scenario_id="r1",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=10.0,
        ),
        make_result(
            scenario_id="r2",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.FAIL,
            observed_status="DENIED",
            duration_ms=20.0,
        ),
        make_result(
            scenario_id="r3",
            domain=BenchmarkDomain.SAFETY,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=30.0,
        ),
    ]

    assert domain_pass_rate(results, domain=BenchmarkDomain.CONSENT) == 0.5
    assert domain_pass_rate(results, domain="SAFETY") == 1.0
    assert domain_pass_rate(results, domain="REPLAY") == 0.0


def test_export_results():
    results = [
        make_result(
            scenario_id="r1",
            domain=BenchmarkDomain.CONSENT,
            outcome=BenchmarkOutcome.PASS,
            observed_status="APPROVED",
            duration_ms=10.0,
        ),
        make_result(
            scenario_id="r2",
            domain=BenchmarkDomain.SAFETY,
            outcome=BenchmarkOutcome.FAIL,
            observed_status="DENIED",
            duration_ms=20.0,
        ),
    ]

    exported = export_results(results)

    assert len(exported) == 2
    assert exported[0]["scenario_id"] == "r1"
    assert exported[0]["domain"] == "CONSENT"
    assert exported[0]["outcome"] == "PASS"
    assert exported[1]["scenario_id"] == "r2"
    assert exported[1]["domain"] == "SAFETY"
    assert exported[1]["outcome"] == "FAIL"
