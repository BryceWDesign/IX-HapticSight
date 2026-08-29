from pathlib import Path

from ohip_perception import PerceptionFrame, ReferenceSegmenter, VisionPipeline

ROOT = Path(__file__).resolve().parents[1]


def test_two_model_pipeline_reaches_quorum_on_calibration_scene():
    primary = ReferenceSegmenter.from_file(ROOT / "models/reference_segmenter_primary.json")
    secondary = ReferenceSegmenter.from_file(ROOT / "models/reference_segmenter_secondary.json")
    pipeline = VisionPipeline(primary, secondary=secondary)
    f = PerceptionFrame(
        rgb=[[(178, 122, 94), (235, 64, 31)]],
        depth_m=[[1.4, 1.7]],
        timestamp_s=1.0,
    )
    out = pipeline.process(f)
    assert out.agreement is not None
    assert out.agreement.passed
    assert out.safe_for_autonomy
    assert any(v.level.value == "RED" for v in out.hazards)
