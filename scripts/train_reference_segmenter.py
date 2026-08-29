"""Reproducibly train the tiny IX-HapticSight reference RGB-D segmenters.

The dataset is synthetic calibration data. It exists to make the repository's
vision path executable and testable without pretending that synthetic training
proves real-world perception quality. Hardware/field data should replace or
augment these models for deployment work.

The generator intentionally avoids Python's random.gauss() and platform-sensitive
floating-point training state. Synthetic samples are produced with a repository-
local integer PRNG and fixed-point arithmetic, then exported as quantized floats.
That makes the committed reference artifacts reproducible byte-for-byte across
supported operating systems and Python patch releases.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path

FEATURE_NAMES = [
    "r",
    "g",
    "b",
    "depth",
    "saturation",
    "brightness",
    "red_dominance",
    "blue_dominance",
]

FIXED_SCALE = 1_000_000
DECIMAL_QUANTUM = Decimal("0.000000000000001")
MASK_64 = (1 << 64) - 1

# Feature-space prototypes in fixed-point millionths. Integer source values keep
# the synthetic calibration corpus stable across platforms.
PROTOTYPES = {
    "background": (180000, 180000, 200000, 800000, 60000, 190000, 0, 20000),
    "person": (700000, 480000, 370000, 350000, 330000, 520000, 180000, 0),
    "object": (420000, 460000, 430000, 480000, 180000, 440000, 10000, 10000),
    "hot": (920000, 250000, 120000, 420000, 660000, 430000, 670000, 0),
    "liquid": (120000, 380000, 860000, 450000, 640000, 450000, 0, 480000),
    "sharp": (720000, 730000, 750000, 300000, 50000, 730000, 0, 20000),
    "unknown": (500000, 100000, 550000, 950000, 550000, 380000, 120000, 170000),
}

NOISE = (45000, 45000, 45000, 35000, 50000, 40000, 40000, 40000)


class StableRNG:
    """Small repository-local SplitMix64 generator with integer-only state."""

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK_64

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK_64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK_64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK_64
        return (z ^ (z >> 31)) & MASK_64

    def randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ValueError("upper must be positive")
        return self.next_u64() % upper


def clamp_units(value: int) -> int:
    return max(0, min(FIXED_SCALE, value))


def gaussian_like_units(rng: StableRNG) -> int:
    """Return a deterministic approximately N(0,1) deviate in fixed-point.

    Irwin-Hall: sum of 12 U(0,1) values minus 6 has variance 1. The
    implementation stays integer-only so the synthetic corpus is identical on
    Windows, Linux, and macOS.
    """

    total = sum(rng.randbelow(FIXED_SCALE + 1) for _ in range(12))
    return total - (6 * FIXED_SCALE)


def sample_class(rng: StableRNG, label: str) -> tuple[int, ...]:
    values: list[int] = []

    for mu, sigma in zip(PROTOTYPES[label], NOISE):
        z = gaussian_like_units(rng)

        # Deterministic integer truncation is sufficient for the synthetic
        # calibration corpus.
        delta = (sigma * z) // FIXED_SCALE
        values.append(clamp_units(mu + delta))

    return tuple(values)


def _quantized_float(value: Decimal) -> float:
    quantized = value.quantize(
        DECIMAL_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )
    return float(format(quantized, "f"))


def train(
    seed: int,
    samples_per_class: int,
) -> tuple[dict[str, list[float]], list[float]]:
    rng = StableRNG(seed)
    sums = defaultdict(lambda: [0] * len(FEATURE_NAMES))
    counts = defaultdict(int)
    all_values: list[list[int]] = [[] for _ in FEATURE_NAMES]

    for label in PROTOTYPES:
        for _ in range(samples_per_class):
            sample = sample_class(rng, label)
            counts[label] += 1

            for i, value in enumerate(sample):
                sums[label][i] += value
                all_values[i].append(value)

    with localcontext() as context:
        context.prec = 50
        scale = Decimal(FIXED_SCALE)

        centroids = {
            label: [
                _quantized_float(
                    Decimal(value)
                    / Decimal(counts[label])
                    / scale
                )
                for value in sums[label]
            ]
            for label in PROTOTYPES
        }

        scales: list[float] = []

        for values in all_values:
            count = Decimal(len(values))
            mean_units = Decimal(sum(values)) / count

            variance_units = sum(
                (Decimal(value) - mean_units) ** 2
                for value in values
            ) / count

            standard_deviation = variance_units.sqrt() / scale

            scales.append(
                _quantized_float(
                    max(
                        standard_deviation,
                        Decimal("0.05"),
                    )
                )
            )

    return centroids, scales


def nearest(
    sample: tuple[int, ...],
    centroids: dict[str, list[float]],
    scales: list[float],
) -> str:
    best_label = ""
    best_distance = float("inf")

    for label, center in centroids.items():
        distance = sum(
            (((value / FIXED_SCALE) - centroid) / scale) ** 2
            for value, centroid, scale in zip(
                sample,
                center,
                scales,
            )
        ) / len(sample)

        if distance < best_distance:
            best_distance = distance
            best_label = label

    return best_label


def evaluate(
    seed: int,
    centroids: dict[str, list[float]],
    scales: list[float],
    n: int = 500,
) -> dict[str, float]:
    rng = StableRNG(seed)
    correct = 0
    total = 0
    per_class_correct = defaultdict(int)
    per_class_total = defaultdict(int)

    for label in PROTOTYPES:
        for _ in range(n):
            sample = sample_class(rng, label)
            pred = nearest(
                sample,
                centroids,
                scales,
            )

            total += 1
            per_class_total[label] += 1

            if pred == label:
                correct += 1
                per_class_correct[label] += 1

    metrics = {
        "accuracy": correct / total,
    }

    for label in PROTOTYPES:
        metrics[f"accuracy_{label}"] = (
            per_class_correct[label]
            / per_class_total[label]
        )

    return metrics


def write_json_lf(path: Path, payload: object) -> None:
    """Write deterministic UTF-8 JSON using LF line endings on every OS."""

    serialized = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(serialized)


def write_model(
    output: Path,
    seed: int,
    name: str,
) -> None:
    centroids, scales = train(
        seed=seed,
        samples_per_class=1000,
    )

    metrics = evaluate(
        seed=seed + 100_000,
        centroids=centroids,
        scales=scales,
    )

    model = {
        "name": name,
        "training_data": "deterministic synthetic calibration set",
        "training_seed": seed,
        "feature_names": FEATURE_NAMES,
        "scales": scales,
        "centroids": centroids,
        "limitations": [
            "Synthetic calibration only; not field validated.",
            "No claim of production-grade semantic segmentation accuracy.",
            "Safety authority must fail closed on low confidence or model disagreement.",
        ],
    }

    write_json_lf(
        output,
        model,
    )

    metrics_path = output.with_suffix(
        ".metrics.json"
    )

    write_json_lf(
        metrics_path,
        metrics,
    )

    print(
        output,
        metrics["accuracy"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-dir",
        default="models",
    )

    args = parser.parse_args()

    out_dir = Path(
        args.output_dir
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_model(
        out_dir / "reference_segmenter_primary.json",
        41021,
        "ixhs-centroid-primary-v1",
    )

    write_model(
        out_dir / "reference_segmenter_secondary.json",
        73199,
        "ixhs-centroid-secondary-v1",
    )


if __name__ == "__main__":
    main()