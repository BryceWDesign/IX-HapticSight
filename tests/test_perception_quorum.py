from ohip_perception import PerceptionQuorum, SegmentationPixel, SegmentationResult, SemanticClass


def result(cls, conf=0.9):
    return SegmentationResult(
        pixels=[[SegmentationPixel(cls, conf, 1-conf)]],
        model_name="m",
        timestamp_s=1.0,
    )


def test_quorum_passes_matching_models():
    q = PerceptionQuorum(min_agreement=1.0, max_critical_disagreement=0.0)
    out = q.compare(result(SemanticClass.PERSON), result(SemanticClass.PERSON))
    assert out.passed
    assert out.reason == "quorum_ok"


def test_quorum_fails_critical_disagreement():
    q = PerceptionQuorum(min_agreement=0.0, max_critical_disagreement=0.0)
    out = q.compare(result(SemanticClass.PERSON), result(SemanticClass.BACKGROUND))
    assert not out.passed
    assert out.critical_disagreement_ratio == 1.0
