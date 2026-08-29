"""Deterministic recovery state machine for unexpected contact and faults."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryStage(str, Enum):
    NONE = "NONE"
    ZERO_EFFORT = "ZERO_EFFORT"
    RETRACT = "RETRACT"
    SAFE_HOLD = "SAFE_HOLD"
    OPERATOR_REQUIRED = "OPERATOR_REQUIRED"


@dataclass(frozen=True)
class RecoveryCommand:
    stage: RecoveryStage
    target_speed_mps: float
    target_force_N: float
    requires_operator_clear: bool
    reason: str


class RecoveryPlanner:
    """Translate runtime violations into bounded recovery behavior."""

    def __init__(self, *, retract_speed_mps: float = 0.03) -> None:
        self.retract_speed_mps = float(retract_speed_mps)

    def from_reason(self, reason: str, *, contact_detected: bool, e_stop: bool = False) -> RecoveryCommand:
        code = reason.lower()
        if e_stop or "e_stop" in code:
            return RecoveryCommand(RecoveryStage.OPERATOR_REQUIRED, 0.0, 0.0, True, "e_stop")
        if any(token in code for token in ("overforce", "force_over", "collision", "red_hazard", "consent_lost")):
            if contact_detected:
                return RecoveryCommand(RecoveryStage.ZERO_EFFORT, 0.0, 0.0, True, reason)
            return RecoveryCommand(RecoveryStage.RETRACT, self.retract_speed_mps, 0.0, True, reason)
        if any(token in code for token in ("stale", "deadline", "quorum", "uncertainty", "watchdog")):
            return RecoveryCommand(RecoveryStage.SAFE_HOLD, 0.0, 0.0, True, reason)
        return RecoveryCommand(RecoveryStage.RETRACT, self.retract_speed_mps, 0.0, False, reason)
