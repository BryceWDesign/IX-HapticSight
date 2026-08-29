"""Runtime safety invariant monitoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InvariantSeverity(str, Enum):
    WARN = "WARN"
    STOP = "STOP"
    LATCH = "LATCH"


@dataclass(frozen=True)
class InvariantViolation:
    code: str
    severity: InvariantSeverity
    observed: float | str | bool | None
    limit: float | str | bool | None
    message: str


@dataclass(frozen=True)
class RuntimeInvariantInput:
    commanded_force_N: float
    measured_force_N: float
    force_cap_N: float
    commanded_speed_mps: float
    speed_cap_mps: float
    sensor_age_ms: float
    max_sensor_age_ms: float
    control_age_ms: float
    max_control_age_ms: float
    consent_active: bool
    contact_requested: bool
    e_stop: bool = False
    perception_quorum_ok: bool = True


@dataclass(frozen=True)
class InvariantReport:
    ok: bool
    violations: tuple[InvariantViolation, ...] = field(default_factory=tuple)

    @property
    def requires_stop(self) -> bool:
        return any(v.severity in {InvariantSeverity.STOP, InvariantSeverity.LATCH} for v in self.violations)

    @property
    def requires_latch(self) -> bool:
        return any(v.severity == InvariantSeverity.LATCH for v in self.violations)


class RuntimeInvariantMonitor:
    """Fail-closed invariant monitor intended to run every control cycle."""

    def evaluate(self, state: RuntimeInvariantInput) -> InvariantReport:
        violations: list[InvariantViolation] = []
        if state.e_stop:
            violations.append(InvariantViolation("e_stop", InvariantSeverity.LATCH, True, False, "emergency stop asserted"))
        if state.contact_requested and not state.consent_active:
            violations.append(InvariantViolation("consent_lost", InvariantSeverity.LATCH, False, True, "contact authority requires active consent"))
        if not state.perception_quorum_ok:
            violations.append(InvariantViolation("perception_quorum_failed", InvariantSeverity.STOP, False, True, "independent perception models do not agree"))
        if state.commanded_force_N > state.force_cap_N + 1e-9:
            violations.append(InvariantViolation("force_command_over_cap", InvariantSeverity.LATCH, state.commanded_force_N, state.force_cap_N, "commanded force exceeds granted envelope"))
        if state.measured_force_N > state.force_cap_N + 1e-9:
            violations.append(InvariantViolation("measured_force_over_cap", InvariantSeverity.LATCH, state.measured_force_N, state.force_cap_N, "measured force exceeds granted envelope"))
        if state.commanded_speed_mps > state.speed_cap_mps + 1e-9:
            violations.append(InvariantViolation("speed_command_over_cap", InvariantSeverity.STOP, state.commanded_speed_mps, state.speed_cap_mps, "commanded speed exceeds granted envelope"))
        if state.sensor_age_ms > state.max_sensor_age_ms:
            violations.append(InvariantViolation("sensor_stale", InvariantSeverity.LATCH, state.sensor_age_ms, state.max_sensor_age_ms, "safety sensor data is stale"))
        if state.control_age_ms > state.max_control_age_ms:
            violations.append(InvariantViolation("controller_deadline_miss", InvariantSeverity.STOP, state.control_age_ms, state.max_control_age_ms, "controller update missed watchdog deadline"))
        return InvariantReport(ok=not violations, violations=tuple(violations))
