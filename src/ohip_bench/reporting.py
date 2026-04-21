"""
Benchmark reporting helpers for IX-HapticSight.

This module provides small, backend-agnostic utilities for:
- summarizing benchmark result sets
- grouping results by domain or outcome
- exporting report-friendly dictionaries

The goal is to make benchmark outputs easier to inspect and compare without
pulling presentation logic into the benchmark runner itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import BenchmarkDomain, BenchmarkOutcome, BenchmarkResult


@dataclass(frozen=True)
class BenchmarkSummary:
    """
    Compact aggregate summary for a benchmark result set.
    """

    total: int
    passed: int
    failed: int
    errored: int
    skipped: int
    average_duration_ms: float
    by_domain: dict[str, int]
    by_outcome: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": int(self.total),
            "passed": int(self.passed),
            "failed": int(self.failed),
            "errored": int(self.errored),
            "skipped": int(self.skipped),
            "average_duration_ms": float(self.average_duration_ms),
            "by_domain": dict(self.by_domain),
            "by_outcome": dict(self.by_outcome),
        }


def summarize_results(results: Iterable[BenchmarkResult]) -> BenchmarkSummary:
    """
    Summarize a benchmark result set.

    The summary is intentionally small and deterministic so it can be reused in:
    - local CLI-style reporting later
    - JSON exports
    - README/docs examples
    - CI artifact checks
    """
    result_list = list(results)
    total = len(result_list)

    by_domain: dict[str, int] = {}
    by_outcome: dict[str, int] = {}

    passed = failed = errored = skipped = 0
    duration_sum = 0.0

    for result in result_list:
        domain_key = result.domain.value
        outcome_key = result.outcome.value

        by_domain[domain_key] = by_domain.get(domain_key, 0) + 1
        by_outcome[outcome_key] = by_outcome.get(outcome_key, 0) + 1

        duration_sum += float(result.duration_ms)

        if result.outcome == BenchmarkOutcome.PASS:
            passed += 1
        elif result.outcome == BenchmarkOutcome.FAIL:
            failed += 1
        elif result.outcome == BenchmarkOutcome.ERROR:
            errored += 1
        elif result.outcome == BenchmarkOutcome.SKIPPED:
            skipped += 1

    average_duration_ms = 0.0 if total == 0 else duration_sum / float(total)

    return BenchmarkSummary(
        total=total,
        passed=passed,
        failed=failed,
        errored=errored,
        skipped=skipped,
        average_duration_ms=average_duration_ms,
        by_domain=by_domain,
        by_outcome=by_outcome,
    )


def results_by_domain(results: Iterable[BenchmarkResult]) -> dict[str, list[BenchmarkResult]]:
    """
    Group benchmark results by domain string.
    """
    grouped: dict[str, list[BenchmarkResult]] = {}
    for result in results:
        grouped.setdefault(result.domain.value, []).append(result)
    return grouped


def results_by_outcome(results: Iterable[BenchmarkResult]) -> dict[str, list[BenchmarkResult]]:
    """
    Group benchmark results by outcome string.
    """
    grouped: dict[str, list[BenchmarkResult]] = {}
    for result in results:
        grouped.setdefault(result.outcome.value, []).append(result)
    return grouped


def domain_pass_rate(
    results: Iterable[BenchmarkResult],
    *,
    domain: BenchmarkDomain | str,
) -> float:
    """
    Compute pass rate for one domain as a fraction in [0, 1].

    Returns 0.0 when there are no results for the requested domain.
    """
    domain_value = domain.value if isinstance(domain, BenchmarkDomain) else str(domain)
    filtered = [result for result in results if result.domain.value == domain_value]
    if not filtered:
        return 0.0

    passed = sum(1 for result in filtered if result.outcome == BenchmarkOutcome.PASS)
    return passed / float(len(filtered))


def export_results(results: Iterable[BenchmarkResult]) -> list[dict[str, object]]:
    """
    Export a benchmark result set as a list of dictionaries.
    """
    return [result.to_dict() for result in results]


__all__ = [
    "BenchmarkSummary",
    "summarize_results",
    "results_by_domain",
    "results_by_outcome",
    "domain_pass_rate",
    "export_results",
]
