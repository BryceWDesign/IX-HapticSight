from __future__ import annotations

import json

from ohip_bench.safety_authority import run_authority_benchmark

results = run_authority_benchmark()
report = {
    "schema": "ixhs-safety-authority-benchmark-v1",
    "passed": all(r.passed for r in results),
    "pass_count": sum(1 for r in results if r.passed),
    "scenario_count": len(results),
    "results": [r.to_dict() for r in results],
}
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["passed"] else 1)
