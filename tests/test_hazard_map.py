from ohip.schemas import HazardClass, SafetyLevel
from ohip_perception import (
    PerceptionFrame,
    SegmentationPixel,
    SegmentationResult,
    SemanticClass,
    VisionHazardProjector,
)


def test_hot_pixel_becomes_red_hot_voxel():
    frame = PerceptionFrame(rgb=[[(255, 0, 0)]], depth_m=[[1.0]], timestamp_s=1.0)
    seg = SegmentationResult(
        pixels=[[SegmentationPixel(SemanticClass.HOT, 0.99, 0.01)]],
        model_name="test",
        timestamp_s=1.0,
    )
    voxels = VisionHazardProjector().project(frame, seg)
    assert len(voxels) == 1
    assert voxels[0].level == SafetyLevel.RED
    assert voxels[0].hazard_class == HazardClass.HOT


def test_low_confidence_fails_closed_to_red_unknown():
    frame = PerceptionFrame(rgb=[[(0, 0, 0)]], depth_m=[[1.0]], timestamp_s=1.0)
    seg = SegmentationResult(
        pixels=[[SegmentationPixel(SemanticClass.BACKGROUND, 0.20, 0.80)]],
        model_name="test",
        timestamp_s=1.0,
    )
    voxels = VisionHazardProjector(min_confidence=0.55).project(frame, seg)
    assert voxels[0].level == SafetyLevel.RED
    assert voxels[0].hazard_class == HazardClass.UNKNOWN
