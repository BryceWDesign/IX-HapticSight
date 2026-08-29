"""Canonical perception models for IX-HapticSight.

The perception layer deliberately keeps learned perception separate from the
safety authority. A model may propose semantic state; it cannot authorize
contact or motion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class SemanticClass(str, Enum):
    BACKGROUND = "background"
    PERSON = "person"
    OBJECT = "object"
    HOT = "hot"
    LIQUID = "liquid"
    SHARP = "sharp"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PerceptionFrame:
    """Normalized RGB-D frame used by the reference vision pipeline.

    RGB values are uint8-like integers in nested [height][width][3] form.
    Depth is metres in nested [height][width] form. ``None`` means depth is
    unavailable for that pixel.
    """

    rgb: list[list[tuple[int, int, int]]]
    depth_m: list[list[float | None]]
    timestamp_s: float
    frame_id: str = "camera"

    @property
    def height(self) -> int:
        return len(self.rgb)

    @property
    def width(self) -> int:
        return len(self.rgb[0]) if self.rgb else 0

    def validate(self) -> None:
        if not self.rgb or not self.rgb[0]:
            raise ValueError("rgb frame must be non-empty")
        if len(self.depth_m) != self.height:
            raise ValueError("depth height must match rgb height")
        width = self.width
        for row, drow in zip(self.rgb, self.depth_m):
            if len(row) != width or len(drow) != width:
                raise ValueError("all rgb/depth rows must have equal width")
            for px in row:
                if len(px) != 3 or any(int(v) < 0 or int(v) > 255 for v in px):
                    raise ValueError("rgb values must be three channels in [0,255]")


@dataclass(frozen=True)
class SegmentationPixel:
    semantic_class: SemanticClass
    confidence: float
    uncertainty: float


@dataclass(frozen=True)
class SegmentationResult:
    pixels: list[list[SegmentationPixel]]
    model_name: str
    timestamp_s: float
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def height(self) -> int:
        return len(self.pixels)

    @property
    def width(self) -> int:
        return len(self.pixels[0]) if self.pixels else 0

    def classes(self) -> Iterable[SemanticClass]:
        for row in self.pixels:
            for pixel in row:
                yield pixel.semantic_class


@dataclass(frozen=True)
class ModelAgreement:
    agreement_ratio: float
    mean_confidence: float
    mean_uncertainty: float
    critical_disagreement_ratio: float
    passed: bool
    reason: str
