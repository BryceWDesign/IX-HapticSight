"""Executable HIL harness with explicit no-hardware semantics.

The harness never manufactures HIL success. A run is ``PASSED`` only when a
hardware probe positively reports required devices and the supplied executor
returns measured samples satisfying the declared acceptance criteria.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from time import time
from typing import Callable, Iterable


class HILStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_RUN_NO_HARDWARE = "NOT_RUN_NO_HARDWARE"
    NOT_RUN_INCOMPLETE = "NOT_RUN_INCOMPLETE"


@dataclass(frozen=True)
class HardwareCapability:
    capability: str
    present: bool
    device_id: str = ""
    detail: str = ""


@dataclass(frozen=True)
class HILSample:
    timestamp_s: float
    measured_force_N: float
    measured_latency_ms: float
    faulted: bool = False


@dataclass(frozen=True)
class HILAcceptanceCriteria:
    required_capabilities: tuple[str, ...] = ("robot_motion", "force_torque")
    max_force_N: float = 3.5
    max_latency_ms: float = 25.0
    min_samples: int = 20


@dataclass(frozen=True)
class HILResult:
    status: HILStatus
    reason: str
    capabilities: tuple[HardwareCapability, ...]
    samples: tuple[HILSample, ...]
    criteria: HILAcceptanceCriteria
    started_at_s: float
    finished_at_s: float

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "capabilities": [asdict(c) for c in self.capabilities],
            "samples": [asdict(s) for s in self.samples],
            "criteria": asdict(self.criteria),
            "started_at_s": self.started_at_s,
            "finished_at_s": self.finished_at_s,
        }


class HILHarness:
    def __init__(self, criteria: HILAcceptanceCriteria | None = None) -> None:
        self.criteria = criteria or HILAcceptanceCriteria()

    def run(
        self,
        *,
        probe: Callable[[], Iterable[HardwareCapability]],
        executor: Callable[[], Iterable[HILSample]] | None,
    ) -> HILResult:
        started = time()
        capabilities = tuple(probe())
        present = {c.capability for c in capabilities if c.present}
        missing = [name for name in self.criteria.required_capabilities if name not in present]
        if missing:
            return HILResult(
                HILStatus.NOT_RUN_NO_HARDWARE,
                "missing:" + ",".join(missing),
                capabilities,
                (),
                self.criteria,
                started,
                time(),
            )
        if executor is None:
            return HILResult(
                HILStatus.NOT_RUN_INCOMPLETE,
                "executor_not_configured",
                capabilities,
                (),
                self.criteria,
                started,
                time(),
            )
        samples = tuple(executor())
        if len(samples) < self.criteria.min_samples:
            status, reason = HILStatus.FAILED, "insufficient_samples"
        elif any(s.faulted for s in samples):
            status, reason = HILStatus.FAILED, "fault_observed"
        elif any(s.measured_force_N > self.criteria.max_force_N for s in samples):
            status, reason = HILStatus.FAILED, "force_limit_exceeded"
        elif any(s.measured_latency_ms > self.criteria.max_latency_ms for s in samples):
            status, reason = HILStatus.FAILED, "latency_limit_exceeded"
        else:
            status, reason = HILStatus.PASSED, "measured_hil_pass"
        return HILResult(status, reason, capabilities, samples, self.criteria, started, time())
