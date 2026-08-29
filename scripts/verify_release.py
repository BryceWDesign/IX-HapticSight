"""Reproduce the software-side IX-HapticSight v0.2 release checks."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + ENV.get("PYTHONPATH", "")


def run(label: str, args: list[str]) -> None:
    print(f"\n== {label} ==")
    subprocess.run(args, cwd=ROOT, env=ENV, check=True)


def main() -> None:
    run("compile", [sys.executable, "-m", "compileall", "-q", "src", "scripts", "examples"])
    run("tests", [sys.executable, "-m", "pytest", "-q"])
    run("quickstart", [sys.executable, "examples/quickstart.py", "--scene", "sim/scenes/basic_room.json", "--verbose"])
    run("perception-to-contact demo", [sys.executable, "examples/perception_to_contact_demo.py"])
    run("safety-authority benchmark", [sys.executable, "scripts/run_safety_authority_benchmark.py"])
    print("\nIX-HapticSight software release verification: PASS")


if __name__ == "__main__":
    main()
