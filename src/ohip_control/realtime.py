"""Bounded soft-real-time contact controller.

The controller is executable and timing-instrumented, but Python cannot provide
a certified hard-real-time guarantee. Hardware deployments should move the same
invariants into a suitable RT process/PLC/safety controller.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import perf_counter

from .invariants import RuntimeInvariantInput, RuntimeInvariantMonitor
from .recovery import RecoveryCommand, RecoveryPlanner, RecoveryStage


class ControllerState(str, Enum):
    IDLE = "IDLE"
    APPROACH = "APPROACH"
    CONTACT = "CONTACT"
    RETREAT = "RETREAT"
    SAFE_HOLD = "SAFE_HOLD"
    FAULTED = "FAULTED"


@dataclass(frozen=True)
class ControllerInput:
    requested_speed_mps: float
    requested_force_N: float
    measured_force_N: float
    force_cap_N: float
    speed_cap_mps: float
    sensor_age_ms: float
    consent_active: bool
    contact_requested: bool
    perception_quorum_ok: bool
    e_stop: bool = False
    contact_detected: bool = False


@dataclass(frozen=True)
class ControllerOutput:
    state: ControllerState
    command_speed_mps: float
    command_force_N: float
    stop: bool
    latched: bool
    reason: str
    recovery: RecoveryCommand | None
    compute_time_ms: float
    deadline_missed: bool


class BoundedRealtimeController:
    """A fail-closed control-cycle kernel with explicit watchdog timing."""

    def __init__(
        self,
        *,
        target_period_ms: float = 5.0,
        max_sensor_age_ms: float = 25.0,
        monitor: RuntimeInvariantMonitor | None = None,
        recovery: RecoveryPlanner | None = None,
    ) -> None:
        self.target_period_ms = float(target_period_ms)
        self.max_sensor_age_ms = float(max_sensor_age_ms)
        self.monitor = monitor or RuntimeInvariantMonitor()
        self.recovery = recovery or RecoveryPlanner()
        self.state = ControllerState.IDLE
        self.latched = False
        self.last_reason = "idle"

    def clear_latch(self) -> None:
        self.latched = False
        self.last_reason = "cleared"
        self.state = ControllerState.IDLE

    def step(self, state: ControllerInput) -> ControllerOutput:
        start = perf_counter()
        if self.latched:
            elapsed = (perf_counter() - start) * 1000.0
            return ControllerOutput(
                state=ControllerState.FAULTED,
                command_speed_mps=0.0,
                command_force_N=0.0,
                stop=True,
                latched=True,
                reason=self.last_reason,
                recovery=RecoveryCommand(RecoveryStage.OPERATOR_REQUIRED, 0.0, 0.0, True, self.last_reason),
                compute_time_ms=elapsed,
                deadline_missed=elapsed > self.target_period_ms,
            )

        command_speed = min(max(0.0, state.requested_speed_mps), max(0.0, state.speed_cap_mps))
        command_force = min(max(0.0, state.requested_force_N), max(0.0, state.force_cap_N))

        inv = RuntimeInvariantInput(
            commanded_force_N=command_force,
            measured_force_N=float(state.measured_force_N),
            force_cap_N=float(state.force_cap_N),
            commanded_speed_mps=command_speed,
            speed_cap_mps=float(state.speed_cap_mps),
            sensor_age_ms=float(state.sensor_age_ms),
            max_sensor_age_ms=self.max_sensor_age_ms,
            control_age_ms=0.0,
            max_control_age_ms=self.target_period_ms * 2.0,
            consent_active=bool(state.consent_active),
            contact_requested=bool(state.contact_requested),
            e_stop=bool(state.e_stop),
            perception_quorum_ok=bool(state.perception_quorum_ok),
        )
        report = self.monitor.evaluate(inv)
        recovery_cmd: RecoveryCommand | None = None
        reason = "control_ok"
        stop = False
        if report.violations:
            primary = report.violations[0]
            reason = primary.code
            stop = report.requires_stop
            recovery_cmd = self.recovery.from_reason(
                primary.code,
                contact_detected=state.contact_detected,
                e_stop=state.e_stop,
            )
            command_speed = recovery_cmd.target_speed_mps if recovery_cmd.stage == RecoveryStage.RETRACT else 0.0
            command_force = recovery_cmd.target_force_N
            if report.requires_latch or recovery_cmd.requires_operator_clear:
                self.latched = True
                self.state = ControllerState.FAULTED
                self.last_reason = reason
            elif recovery_cmd.stage == RecoveryStage.SAFE_HOLD:
                self.state = ControllerState.SAFE_HOLD
            else:
                self.state = ControllerState.RETREAT
        else:
            if state.contact_requested and state.contact_detected:
                self.state = ControllerState.CONTACT
            elif state.contact_requested:
                self.state = ControllerState.APPROACH
            else:
                self.state = ControllerState.IDLE

        elapsed = (perf_counter() - start) * 1000.0
        deadline_missed = elapsed > self.target_period_ms
        if deadline_missed and not self.latched:
            self.state = ControllerState.SAFE_HOLD
            stop = True
            reason = "controller_compute_deadline_miss"
            command_speed = 0.0
            command_force = 0.0
            recovery_cmd = self.recovery.from_reason(reason, contact_detected=state.contact_detected)
        return ControllerOutput(
            state=self.state,
            command_speed_mps=command_speed,
            command_force_N=command_force,
            stop=stop,
            latched=self.latched,
            reason=reason,
            recovery=recovery_cmd,
            compute_time_ms=elapsed,
            deadline_missed=deadline_missed,
        )
