import subprocess
import sys
from pathlib import Path


def test_reference_models_retrain_byte_for_byte(tmp_path):
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(root / "scripts/train_reference_segmenter.py"), "--output-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    for name in (
        "reference_segmenter_primary.json",
        "reference_segmenter_primary.metrics.json",
        "reference_segmenter_secondary.json",
        "reference_segmenter_secondary.metrics.json",
    ):
        assert (tmp_path / name).read_bytes() == (root / "models" / name).read_bytes()
