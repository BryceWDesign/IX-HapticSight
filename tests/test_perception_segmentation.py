from pathlib import Path

import pytest

from ohip_perception import PerceptionFrame, ReferenceSegmenter, SemanticClass

ROOT = Path(__file__).resolve().parents[1]


def segmenter(name="reference_segmenter_primary.json"):
    return ReferenceSegmenter.from_file(ROOT / "models" / name)


def frame(rgb, depth=1.0):
    return PerceptionFrame(
        rgb=[[rgb]],
        depth_m=[[depth]],
        timestamp_s=1.0,
    )


@pytest.mark.parametrize(
    "rgb,depth,expected",
    [
        ((46, 46, 51), 3.2, SemanticClass.BACKGROUND),
        ((178, 122, 94), 1.4, SemanticClass.PERSON),
        ((107, 117, 110), 1.9, SemanticClass.OBJECT),
        ((235, 64, 31), 1.7, SemanticClass.HOT),
        ((31, 97, 219), 1.8, SemanticClass.LIQUID),
        ((184, 186, 191), 1.2, SemanticClass.SHARP),
    ],
)
def test_reference_segmenter_classifies_calibration_prototypes(rgb, depth, expected):
    result = segmenter().infer(frame(rgb, depth))
    assert result.pixels[0][0].semantic_class == expected
    assert 0.0 <= result.pixels[0][0].confidence <= 1.0


def test_frame_rejects_bad_shape():
    f = PerceptionFrame(rgb=[[(0, 0, 0)]], depth_m=[], timestamp_s=1.0)
    with pytest.raises(ValueError):
        f.validate()
