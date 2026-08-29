"""Runnable reference segmentation for IX-HapticSight.

This is intentionally small and auditable. It is a nearest-centroid semantic
classifier operating on normalized RGB-D features. The committed model file is
reproducibly trained by ``scripts/train_reference_segmenter.py`` using a
synthetic calibration dataset. It is a real executable model, but it is not
claimed to be production perception or a substitute for robot-specific data.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .models import PerceptionFrame, SegmentationPixel, SegmentationResult, SemanticClass


@dataclass(frozen=True)
class CentroidModel:
    name: str
    feature_names: tuple[str, ...]
    centroids: Mapping[SemanticClass, tuple[float, ...]]
    scales: tuple[float, ...]

    @classmethod
    def load(cls, path: str | Path) -> "CentroidModel":
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        feature_names = tuple(str(x) for x in doc["feature_names"])
        scales = tuple(float(x) for x in doc.get("scales", [1.0] * len(feature_names)))
        centroids = {
            SemanticClass(key): tuple(float(x) for x in values)
            for key, values in doc["centroids"].items()
        }
        if any(len(v) != len(feature_names) for v in centroids.values()):
            raise ValueError("centroid feature dimensions do not match feature_names")
        if len(scales) != len(feature_names):
            raise ValueError("scale dimensions do not match feature_names")
        return cls(
            name=str(doc.get("name", "centroid-segmenter")),
            feature_names=feature_names,
            centroids=centroids,
            scales=scales,
        )


class ReferenceSegmenter:
    """Small semantic segmentation model with calibrated confidence output."""

    def __init__(self, model: CentroidModel) -> None:
        self.model = model

    @classmethod
    def from_file(cls, path: str | Path) -> "ReferenceSegmenter":
        return cls(CentroidModel.load(path))

    def infer(self, frame: PerceptionFrame) -> SegmentationResult:
        frame.validate()
        rows: list[list[SegmentationPixel]] = []
        conf_sum = 0.0
        uncertainty_sum = 0.0
        count = 0
        for y in range(frame.height):
            out_row: list[SegmentationPixel] = []
            for x in range(frame.width):
                features = self._features(frame, x, y)
                ranked = sorted(
                    (
                        (self._distance(features, centroid), cls_name)
                        for cls_name, centroid in self.model.centroids.items()
                    ),
                    key=lambda item: item[0],
                )
                best_d, best_cls = ranked[0]
                second_d = ranked[1][0] if len(ranked) > 1 else best_d + 1.0
                margin = max(0.0, second_d - best_d)
                confidence = max(0.0, min(1.0, 1.0 - best_d / 1.75))
                separation = margin / (second_d + 1e-9)
                confidence = max(0.0, min(1.0, 0.65 * confidence + 0.35 * separation))
                uncertainty = 1.0 - confidence
                out_row.append(SegmentationPixel(best_cls, confidence, uncertainty))
                conf_sum += confidence
                uncertainty_sum += uncertainty
                count += 1
            rows.append(out_row)
        denom = float(max(1, count))
        return SegmentationResult(
            pixels=rows,
            model_name=self.model.name,
            timestamp_s=frame.timestamp_s,
            metrics={
                "mean_confidence": conf_sum / denom,
                "mean_uncertainty": uncertainty_sum / denom,
            },
        )

    def _distance(self, features: Sequence[float], centroid: Sequence[float]) -> float:
        total = 0.0
        for value, center, scale in zip(features, centroid, self.model.scales):
            s = max(abs(scale), 1e-6)
            total += ((value - center) / s) ** 2
        return math.sqrt(total / max(1, len(features)))

    @staticmethod
    def _features(frame: PerceptionFrame, x: int, y: int) -> tuple[float, ...]:
        r, g, b = frame.rgb[y][x]
        depth = frame.depth_m[y][x]
        depth_norm = 1.0 if depth is None else max(0.0, min(1.0, float(depth) / 4.0))
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        saturation = (max_c - min_c) / 255.0
        brightness = (r + g + b) / (3.0 * 255.0)
        red_dominance = max(0.0, (r - max(g, b)) / 255.0)
        blue_dominance = max(0.0, (b - max(r, g)) / 255.0)
        return (
            r / 255.0,
            g / 255.0,
            b / 255.0,
            depth_norm,
            saturation,
            brightness,
            red_dominance,
            blue_dominance,
        )
