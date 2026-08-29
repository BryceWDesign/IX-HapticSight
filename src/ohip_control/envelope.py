"""Dynamic, uncertainty-aware execution envelopes for IX-HapticSight.

This module is deliberately independent of any learned policy. Learned systems
may request an action; this envelope computes the maximum motion/force authority
that the deterministic runtime is willing to grant at that instant.
"""
from __future__ import annotations

from dataclasses import dataclass

from ohip.schemas import SafetyLevel


@dataclass(frozen=True)
class DynamicEnvelopeInput:
    requested_force_N: float
    requested_speed_mps: float
    base_force_cap_N: float
    base_speed_cap_mps: float
    proximity_m: float | None = None
    perception_uncertainty: float = 0.0
    safety_level: SafetyLevel = SafetyLevel.GREEN
    human_present: bool = False


@dataclass(frozen=True)
class DynamicEnvelopeDecision:
    allowed: bool
    force_cap_N: float
    speed_cap_mps: float
    force_command_N: float
    speed_command_mps: float
    authority_scale: float
    reason: str


class DynamicSafetyEnvelope:
    """Compute a conservative action envelope from dynamic scene state."""

    def __init__(
        self,
        *,
        yellow_scale: float = 0.35,
        uncertainty_start: float = 0.25,
        uncertainty_stop: float = 0.70,
        human_slow_distance_m: float = 0.8,
        human_stop_distance_m: float = 0.20,
    ) -> None:
        self.yellow_scale = float(yellow_scale)
        self.uncertainty_start = float(uncertainty_start)
        self.uncertainty_stop = float(uncertainty_stop)
        self.human_slow_distance_m = float(human_slow_distance_m)
        self.human_stop_distance_m = float(human_stop_distance_m)

    def evaluate(self, state: DynamicEnvelopeInput) -> DynamicEnvelopeDecision:
        if state.safety_level == SafetyLevel.RED:
            return self._deny("red_hazard")
        uncertainty = max(0.0, min(1.0, float(state.perception_uncertainty)))
        if uncertainty >= self.uncertainty_stop:
            return self._deny("perception_uncertainty_stop")

        scale = 1.0
        reasons: list[str] = []
        if state.safety_level == SafetyLevel.YELLOW:
            scale = min(scale, self.yellow_scale)
            reasons.append("yellow_zone")

        if uncertainty > self.uncertainty_start:
            span = max(1e-9, self.uncertainty_stop - self.uncertainty_start)
            uncertainty_scale = max(0.0, 1.0 - (uncertainty - self.uncertainty_start) / span)
            scale = min(scale, uncertainty_scale)
            reasons.append("uncertainty_derate")

        if state.human_present and state.proximity_m is not None:
            proximity = float(state.proximity_m)
            if proximity <= self.human_stop_distance_m:
                return self._deny("human_proximity_stop")
            if proximity < self.human_slow_distance_m:
                span = max(1e-9, self.human_slow_distance_m - self.human_stop_distance_m)
                proximity_scale = max(0.05, (proximity - self.human_stop_distance_m) / span)
                scale = min(scale, proximity_scale)
                reasons.append("human_proximity_derate")

        force_cap = max(0.0, float(state.base_force_cap_N)) * scale
        speed_cap = max(0.0, float(state.base_speed_cap_mps)) * scale
        force_cmd = min(max(0.0, float(state.requested_force_N)), force_cap)
        speed_cmd = min(max(0.0, float(state.requested_speed_mps)), speed_cap)
        reason = "+".join(reasons) if reasons else "full_authority"
        return DynamicEnvelopeDecision(
            allowed=True,
            force_cap_N=force_cap,
            speed_cap_mps=speed_cap,
            force_command_N=force_cmd,
            speed_command_mps=speed_cmd,
            authority_scale=scale,
            reason=reason,
        )

    @staticmethod
    def _deny(reason: str) -> DynamicEnvelopeDecision:
        return DynamicEnvelopeDecision(
            allowed=False,
            force_cap_N=0.0,
            speed_cap_mps=0.0,
            force_command_N=0.0,
            speed_command_mps=0.0,
            authority_scale=0.0,
            reason=reason,
        )
