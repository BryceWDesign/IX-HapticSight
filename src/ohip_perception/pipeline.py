"""End-to-end image/depth ingestion to semantic and hazard state."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import time

from PIL import Image

from .fusion import PerceptionQuorum
from .hazard_map import HazardVoxel, VisionHazardProjector
from .models import ModelAgreement, PerceptionFrame, SegmentationResult
from .segmentation import ReferenceSegmenter


@dataclass(frozen=True)
class PerceptionPipelineResult:
    primary: SegmentationResult
    secondary: SegmentationResult | None
    agreement: ModelAgreement | None
    hazards: list[HazardVoxel]
    safe_for_autonomy: bool
    reason: str


class VisionPipeline:
    def __init__(
        self,
        primary: ReferenceSegmenter,
        *,
        secondary: ReferenceSegmenter | None = None,
        quorum: PerceptionQuorum | None = None,
        projector: VisionHazardProjector | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.quorum = quorum or PerceptionQuorum()
        self.projector = projector or VisionHazardProjector()

    @staticmethod
    def load_rgbd(
        rgb_path: str | Path,
        *,
        depth_m: list[list[float | None]] | None = None,
        default_depth_m: float = 1.0,
        timestamp_s: float | None = None,
    ) -> PerceptionFrame:
        image = Image.open(rgb_path).convert("RGB")
        width, height = image.size
        flat = list(image.getdata())
        rgb = [flat[y * width : (y + 1) * width] for y in range(height)]
        if depth_m is None:
            depth_m = [[float(default_depth_m) for _ in range(width)] for _ in range(height)]
        return PerceptionFrame(
            rgb=[[tuple(int(v) for v in px) for px in row] for row in rgb],
            depth_m=depth_m,
            timestamp_s=time() if timestamp_s is None else float(timestamp_s),
        )

    def process(self, frame: PerceptionFrame) -> PerceptionPipelineResult:
        primary = self.primary.infer(frame)
        secondary_result = self.secondary.infer(frame) if self.secondary is not None else None
        agreement = None
        if secondary_result is not None:
            agreement = self.quorum.compare(primary, secondary_result)
            if not agreement.passed:
                hazards = self.projector.project(frame, primary)
                return PerceptionPipelineResult(
                    primary=primary,
                    secondary=secondary_result,
                    agreement=agreement,
                    hazards=hazards,
                    safe_for_autonomy=False,
                    reason=agreement.reason,
                )
        hazards = self.projector.project(frame, primary)
        return PerceptionPipelineResult(
            primary=primary,
            secondary=secondary_result,
            agreement=agreement,
            hazards=hazards,
            safe_for_autonomy=True,
            reason="perception_ok",
        )
