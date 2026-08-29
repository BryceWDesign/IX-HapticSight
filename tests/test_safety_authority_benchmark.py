from ohip_bench.safety_authority import run_authority_benchmark


def test_all_independent_safety_authority_scenarios_pass():
    results = run_authority_benchmark()
    assert len(results) >= 8
    assert all(r.passed for r in results)
