"""Deterministic multimodal safety fusion.

Vision, force/torque, tactile, proximity, and thermal modalities contribute to
one conservative safety classification. This is deliberately rule-based and
inspectable. Learned representations can feed it, but they do not get to hide
which modality caused a veto.
"""
from __future__ import annotations

from dataclasses import dataclass

from ohip.schemas import SafetyLevel
from ohip_interfaces.force_torque import ContactForceAssessment
from ohip_interfaces.proximity import ProximityAssessment
from ohip_interfaces.tactile import TactileContactAssessment
from ohip_interfaces.thermal import ThermalAssessment


@dataclass(frozen=True)
class MultimodalSafetyInput:
    vision_level: SafetyLevel = SafetyLevel.GREEN
    perception_quorum_ok: bool = True
    perception_uncertainty: float = 0.0
    force: ContactForceAssessment | None = None
    tactile: TactileContactAssessment | None = None
    proximity: ProximityAssessment | None = None
    thermal: ThermalAssessment | None = None
    require_force: bool = False
    require_tactile: bool = False
    require_proximity: bool = False
    require_thermal: bool = False


@dataclass(frozen=True)
class MultimodalSafetyDecision:
    level: SafetyLevel
    reasons: tuple[str, ...]
    available_modalities: tuple[str, ...]
    missing_required_modalities: tuple[str, ...]


class MultimodalSafetyFusion:
    def __init__(self, *, uncertainty_yellow: float = 0.25, uncertainty_red: float = 0.70) -> None:
        self.uncertainty_yellow = float(uncertainty_yellow)
        self.uncertainty_red = float(uncertainty_red)

    def evaluate(self, state: MultimodalSafetyInput) -> MultimodalSafetyDecision:
        reasons: list[str] = []
        available: list[str] = []
        missing: list[str] = []
        level = state.vision_level

        def escalate(candidate: SafetyLevel, reason: str) -> None:
            nonlocal level
            if self._severity(candidate) > self._severity(level):
                level = candidate
            reasons.append(reason)

        if not state.perception_quorum_ok:
            escalate(SafetyLevel.RED, "perception_quorum_failed")
        uncertainty = max(0.0, min(1.0, float(state.perception_uncertainty)))
        if uncertainty >= self.uncertainty_red:
            escalate(SafetyLevel.RED, "perception_uncertainty_red")
        elif uncertainty >= self.uncertainty_yellow:
            escalate(SafetyLevel.YELLOW, "perception_uncertainty_yellow")

        if state.force is None:
            if state.require_force:
                missing.append("force")
        else:
            available.append("force")
            if state.force.excessive_force:
                escalate(SafetyLevel.RED, "force_excessive")
            elif state.force.contact_detected:
                escalate(SafetyLevel.YELLOW, "force_contact")

        if state.tactile is None:
            if state.require_tactile:
                missing.append("tactile")
        else:
            available.append("tactile")
            if state.tactile.excessive_pressure:
                escalate(SafetyLevel.RED, "tactile_pressure_excessive")
            if state.tactile.excessive_shear:
                escalate(SafetyLevel.RED, "tactile_shear_excessive")
            elif state.tactile.contact_detected:
                escalate(SafetyLevel.YELLOW, "tactile_contact")

        if state.proximity is None:
            if state.require_proximity:
                missing.append("proximity")
        else:
            available.append("proximity")
            if not state.proximity.corridor_clear:
                escalate(SafetyLevel.RED, "proximity_stop")
            elif state.proximity.near_contact:
                escalate(SafetyLevel.YELLOW, "proximity_caution")

        if state.thermal is None:
            if state.require_thermal:
                missing.append("thermal")
        else:
            available.append("thermal")
            if state.thermal.over_limit:
                escalate(SafetyLevel.RED, "thermal_stop")
            elif state.thermal.heat_detected:
                escalate(SafetyLevel.YELLOW, "thermal_caution")

        if missing:
            escalate(SafetyLevel.RED, "required_modality_missing")
        if not reasons:
            reasons.append("multimodal_nominal")
        return MultimodalSafetyDecision(
            level=level,
            reasons=tuple(reasons),
            available_modalities=tuple(available),
            missing_required_modalities=tuple(missing),
        )

    @staticmethod
    def _severity(level: SafetyLevel) -> int:
        return {SafetyLevel.GREEN: 0, SafetyLevel.YELLOW: 1, SafetyLevel.RED: 2}[level]
