"""
Benchmark models for IX-HapticSight.

This module defines backend-agnostic scenario, metric, and result structures
for deterministic repository benchmarks. These models are intended to support:

- consent-path benchmarks
- safety-veto benchmarks
- planning/execution benchmarks
- replay-backed regression checks

Design goals:
- explicit inputs
- explicit expected outcomes
- structured measurable outputs
- no hidden dependence on one runtime transport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any, Optional


class BenchmarkDomain(str, Enum):
    CONSENT = "CONSENT"
    SAFETY = "SAFETY"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    LOGGING = "LOGGING"
    REPLAY = "REPLAY"
    INTEGRATION = "INTEGRATION"


class BenchmarkOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class BenchmarkMetric:
    """
    One measured metric from a benchmark run.
    """

    name: str
    value: float
    unit: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": float(self.value),
            "unit": self.unit,
            "note": self.note,
        }


@dataclass(frozen=True)
class BenchmarkExpectation:
    """
    Explicit expected outcome for one benchmark scenario.

    This is intentionally narrow and machine-friendly so that benchmark logic
    can compare real outputs against stated expectations without relying on
    vague prose.
    """

    expected_status: str
    expected_executable: Optional[bool] = None
    expected_fault_reason: str = ""
    expected_execution_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_status": self.expected_status,
            "expected_executable": self.expected_executable,
            "expected_fault_reason": self.expected_fault_reason,
            "expected_execution_status": self.expected_execution_status,
        }


@dataclass(frozen=True)
class BenchmarkScenario:
    """
    Canonical scenario definition for one deterministic benchmark case.

    `inputs` is intentionally a plain mapping so the benchmark package can
    describe scenarios without importing every runtime model eagerly.
    """

    scenario_id: str
    title: str
    domain: BenchmarkDomain
    description: str
    inputs: dict[str, Any]
    expectation: BenchmarkExpectation
    tags: tuple[str, ...] = ()
    created_at_utc_s: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "domain": self.domain.value,
            "description": self.description,
            "inputs": dict(self.inputs),
            "expectation": self.expectation.to_dict(),
            "tags": list(self.tags),
            "created_at_utc_s": float(self.created_at_utc_s),
        }


@dataclass(frozen=True)
class BenchmarkObservation:
    """
    Observed structured outcome from one benchmark run.
    """

    observed_status: str
    observed_executable: Optional[bool] = None
    observed_fault_reason: str = ""
    observed_execution_status: str = ""
    event_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_status": self.observed_status,
            "observed_executable": self.observed_executable,
            "observed_fault_reason": self.observed_fault_reason,
            "observed_execution_status": self.observed_execution_status,
            "event_count": int(self.event_count),
        }


@dataclass(frozen=True)
class BenchmarkResult:
    """
    Structured result for one executed benchmark scenario.
    """

    scenario_id: str
    domain: BenchmarkDomain
    outcome: BenchmarkOutcome
    observation: BenchmarkObservation
    metrics: tuple[BenchmarkMetric, ...] = ()
    reason_code: str = ""
    started_at_utc_s: float = field(default_factory=time)
    finished_at_utc_s: float = field(default_factory=time)

    @property
    def duration_ms(self) -> float:
        return max(0.0, (float(self.finished_at_utc_s) - float(self.started_at_utc_s)) * 1000.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "domain": self.domain.value,
            "outcome": self.outcome.value,
            "observation": self.observation.to_dict(),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "reason_code": self.reason_code,
            "started_at_utc_s": float(self.started_at_utc_s),
            "finished_at_utc_s": float(self.finished_at_utc_s),
            "duration_ms": float(self.duration_ms),
        }


def compare_expectation(
    *,
    expectation: BenchmarkExpectation,
    observation: BenchmarkObservation,
) -> tuple[bool, str]:
    """
    Compare one observed benchmark outcome against its explicit expectation.

    Returns:
    - success flag
    - compact reason string
    """
    if expectation.expected_status != observation.observed_status:
        return False, (
            f"status_mismatch:"
            f"{expectation.expected_status}!={observation.observed_status}"
        )

    if expectation.expected_executable is not None:
        if expectation.expected_executable != observation.observed_executable:
            return False, (
                f"executable_mismatch:"
                f"{expectation.expected_executable}!={observation.observed_executable}"
            )

    if expectation.expected_fault_reason:
        if expectation.expected_fault_reason != observation.observed_fault_reason:
            return False, (
                f"fault_reason_mismatch:"
                f"{expectation.expected_fault_reason}!={observation.observed_fault_reason}"
            )

    if expectation.expected_execution_status:
        if expectation.expected_execution_status != observation.observed_execution_status:
            return False, (
                f"execution_status_mismatch:"
                f"{expectation.expected_execution_status}!={observation.observed_execution_status}"
            )

    return True, "expectation_met"


__all__ = [
    "BenchmarkDomain",
    "BenchmarkOutcome",
    "BenchmarkMetric",
    "BenchmarkExpectation",
    "BenchmarkScenario",
    "BenchmarkObservation",
    "BenchmarkResult",
    "compare_expectation",
]
