"""Vision-derived tri-level hazard map generation."""
from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Iterable

from ohip.schemas import HazardClass, SafetyLevel, SafetyMapCell

from .models import PerceptionFrame, SegmentationResult, SemanticClass


@dataclass(frozen=True)
class HazardVoxel:
    cell: tuple[int, int, int]
    level: SafetyLevel
    hazard_class: HazardClass
    confidence: float
    source: str


_CLASS_POLICY: dict[SemanticClass, tuple[SafetyLevel, HazardClass]] = {
    SemanticClass.BACKGROUND: (SafetyLevel.GREEN, HazardClass.UNKNOWN),
    SemanticClass.OBJECT: (SafetyLevel.YELLOW, HazardClass.UNKNOWN),
    SemanticClass.PERSON: (SafetyLevel.YELLOW, HazardClass.MOVING),
    SemanticClass.HOT: (SafetyLevel.RED, HazardClass.HOT),
    SemanticClass.LIQUID: (SafetyLevel.RED, HazardClass.LIQUID),
    SemanticClass.SHARP: (SafetyLevel.RED, HazardClass.BLADE),
    SemanticClass.UNKNOWN: (SafetyLevel.RED, HazardClass.UNKNOWN),
}


class VisionHazardProjector:
    """Project RGB-D segmentation into a coarse camera-frame safety voxel map.

    The reference projection intentionally uses a simple pinhole approximation
    and keeps uncertain/no-depth observations conservative.
    """

    def __init__(
        self,
        *,
        voxel_size_m: float = 0.05,
        horizontal_fov_deg: float = 70.0,
        min_confidence: float = 0.55,
    ) -> None:
        self.voxel_size_m = float(voxel_size_m)
        self.horizontal_fov_deg = float(horizontal_fov_deg)
        self.min_confidence = float(min_confidence)

    def project(self, frame: PerceptionFrame, segmentation: SegmentationResult) -> list[HazardVoxel]:
        frame.validate()
        if segmentation.height != frame.height or segmentation.width != frame.width:
            raise ValueError("segmentation dimensions must match perception frame")
        output: dict[tuple[int, int, int], HazardVoxel] = {}
        half_width = max(1.0, frame.width / 2.0)
        tan_half_fov = __import__("math").tan(__import__("math").radians(self.horizontal_fov_deg / 2.0))

        for y in range(frame.height):
            for x in range(frame.width):
                pixel = segmentation.pixels[y][x]
                depth = frame.depth_m[y][x]
                if depth is None or depth <= 0.0:
                    if pixel.semantic_class in {SemanticClass.BACKGROUND, SemanticClass.OBJECT}:
                        continue
                    depth = self.voxel_size_m
                z = float(depth)
                x_norm = (x - half_width) / half_width
                x_m = x_norm * z * tan_half_fov
                y_m = ((frame.height / 2.0 - y) / max(1.0, frame.height / 2.0)) * z * tan_half_fov
                cell = (
                    floor(x_m / self.voxel_size_m),
                    floor(y_m / self.voxel_size_m),
                    floor(z / self.voxel_size_m),
                )
                level, hazard = _CLASS_POLICY[pixel.semantic_class]
                if pixel.confidence < self.min_confidence:
                    level = SafetyLevel.RED
                    hazard = HazardClass.UNKNOWN
                voxel = HazardVoxel(
                    cell=cell,
                    level=level,
                    hazard_class=hazard,
                    confidence=float(pixel.confidence),
                    source=f"vision:{segmentation.model_name}",
                )
                prev = output.get(cell)
                if prev is None or self._severity(voxel.level) > self._severity(prev.level):
                    output[cell] = voxel
                elif prev.level == voxel.level and voxel.confidence > prev.confidence:
                    output[cell] = voxel
        return sorted(output.values(), key=lambda v: v.cell)

    @staticmethod
    def to_safety_cells(voxels: Iterable[HazardVoxel], updated_ms: int) -> list[SafetyMapCell]:
        return [
            SafetyMapCell(
                cell=v.cell,
                hazard_class=v.hazard_class,
                level=v.level,
                updated_ms=updated_ms,
            )
            for v in voxels
        ]

    @staticmethod
    def _severity(level: SafetyLevel) -> int:
        return {SafetyLevel.GREEN: 0, SafetyLevel.YELLOW: 1, SafetyLevel.RED: 2}[level]
