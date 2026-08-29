from types import SimpleNamespace

import pytest

from ohip_ros2 import tactile_multiarray_to_frame


def test_tactile_multiarray_converts_real_transport_contract():
    msg = SimpleNamespace(data=[
        0.0, 0.0, 0.0,
        0.0, 0.0, 1.0,
        25.0, 3.0,
        0.2, 0.1,
    ])
    frame = tactile_multiarray_to_frame(msg)
    assert frame.patch_count() == 1
    assert frame.patches[0].pressure_kpa == 3.0
    assert frame.patches[0].area_mm2 == 25.0
    assert frame.quality.source_name == "ros2_tactile"


def test_tactile_multiarray_rejects_malformed_payload():
    with pytest.raises(ValueError):
        tactile_multiarray_to_frame(SimpleNamespace(data=[1.0, 2.0]))
