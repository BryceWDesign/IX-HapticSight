"""Perception quorum and model-disagreement handling.

Safety-critical perception should not silently trust one classifier. The quorum
compares independently configured models and fails closed when disagreement is
high, especially for human/sharp/hot/liquid classes.
"""
from __future__ import annotations

from .models import ModelAgreement, SegmentationResult, SemanticClass


CRITICAL_CLASSES = {
    SemanticClass.PERSON,
    SemanticClass.HOT,
    SemanticClass.LIQUID,
    SemanticClass.SHARP,
}


class PerceptionQuorum:
    def __init__(
        self,
        *,
        min_agreement: float = 0.90,
        max_critical_disagreement: float = 0.03,
        min_mean_confidence: float = 0.55,
    ) -> None:
        self.min_agreement = float(min_agreement)
        self.max_critical_disagreement = float(max_critical_disagreement)
        self.min_mean_confidence = float(min_mean_confidence)

    def compare(self, primary: SegmentationResult, secondary: SegmentationResult) -> ModelAgreement:
        if primary.height != secondary.height or primary.width != secondary.width:
            return ModelAgreement(0.0, 0.0, 1.0, 1.0, False, "shape_mismatch")

        total = 0
        agree = 0
        critical_disagree = 0
        conf_sum = 0.0
        unc_sum = 0.0
        for prow, srow in zip(primary.pixels, secondary.pixels):
            for p, s in zip(prow, srow):
                total += 1
                if p.semantic_class == s.semantic_class:
                    agree += 1
                elif p.semantic_class in CRITICAL_CLASSES or s.semantic_class in CRITICAL_CLASSES:
                    critical_disagree += 1
                conf_sum += min(p.confidence, s.confidence)
                unc_sum += max(p.uncertainty, s.uncertainty)

        denom = float(max(1, total))
        agreement_ratio = agree / denom
        critical_ratio = critical_disagree / denom
        mean_conf = conf_sum / denom
        mean_unc = unc_sum / denom
        passed = (
            agreement_ratio >= self.min_agreement
            and critical_ratio <= self.max_critical_disagreement
            and mean_conf >= self.min_mean_confidence
        )
        if agreement_ratio < self.min_agreement:
            reason = "model_disagreement"
        elif critical_ratio > self.max_critical_disagreement:
            reason = "critical_class_disagreement"
        elif mean_conf < self.min_mean_confidence:
            reason = "low_confidence"
        else:
            reason = "quorum_ok"
        return ModelAgreement(
            agreement_ratio=agreement_ratio,
            mean_confidence=mean_conf,
            mean_uncertainty=mean_unc,
            critical_disagreement_ratio=critical_ratio,
            passed=passed,
            reason=reason,
        )
