"""
IX-HapticSight — Tests for the deterministic benchmark runner.

These tests verify that the benchmark runner can:
- execute explicit consent scenarios against a fresh runtime service
- produce PASS results when observations match expectations
- produce FAIL results when expectations are intentionally wrong
- produce ERROR results for malformed benchmark inputs
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip.consent_manager import ConsentManager  # noqa: E402
from ohip.contact_planner import ContactPlanner  # noqa: E402
from ohip.safety_gate import SafetyGate  # noqa: E402
from ohip.schemas import Pose, SafetyLevel  # noqa: E402
from ohip_interfaces.simulated_execution_adapter import (  # noqa: E402
    SimulatedExecutionAdapter,
)
from ohip_logging.recorder import EventRecorder  # noqa: E402
from ohip_runtime.coordinator import RuntimeCoordinator  # noqa: E402
from ohip_runtime.runtime_service import RuntimeService  # noqa: E402
from ohip_runtime.session_store import SessionStore  # noqa: E402

from ohip_bench.models import (  # noqa: E402
    BenchmarkDomain,
    BenchmarkExpectation,
    BenchmarkOutcome,
    BenchmarkScenario,
)
from ohip_bench.runner import (  # noqa: E402
    BenchmarkRunner,
    make_consent_scenario,
)


def risk_green(_pose: Pose) -> SafetyLevel:
    return SafetyLevel.GREEN


def make_envelopes() -> dict:
    return {
        "defaults": {
            "social_touch_profile": "default_social",
        },
        "profiles": {
            "default_social": {
                "max_force_N": 1.2,
                "dwell_ms_min": 1000,
                "dwell_ms_max": 3000,
                "approach_speed_mps": 0.15,
                "release_speed_mps": 0.20,
                "impedance": {
                    "normal_N_per_mm": [0.3, 0.6],
                    "tangential_N_per_mm": [0.1, 0.3],
                },
            }
        },
        "safety": {
            "red_stop_ms": 100,
        },
    }


def make_service_factory(log_path: Path):
    def factory() -> RuntimeService:
        envelopes = make_envelopes()
        consent_manager = ConsentManager()
        planner = ContactPlanner(envelopes)
        gate = SafetyGate(envelopes)
        coordinator = RuntimeCoordinator(
            consent_manager=consent_manager,
            contact_planner=planner,
            safety_gate=gate,
            risk_query=risk_green,
        )
        store = SessionStore()
        recorder = EventRecorder.from_path(log_path)
        adapter = SimulatedExecutionAdapter()
        return RuntimeService(
            session_store=store,
            coordinator=coordinator,
            recorder=recorder,
            execution_adapter=adapter,
        )

    return factory


def test_benchmark_runner_passes_explicit_consent_scenario():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "bench_pass.jsonl"
        runner = BenchmarkRunner(
            service_factory=make_service_factory(log_path),
        )

        scenario = make_consent_scenario(
            scenario_id="consent-pass-001",
            title="Explicit consent allows support contact",
            explicit_consent=True,
            expected_status="APPROVED",
            expected_executable=True,
            expected_execution_status="ACCEPTED",
        )

        result = runner.run(scenario)

        assert result.scenario_id == "consent-pass-001"
        assert result.domain == BenchmarkDomain.CONSENT
        assert result.outcome == BenchmarkOutcome.PASS
        assert result.reason_code == "expectation_met"
        assert result.observation.observed_status == "APPROVED"
        assert result.observation.observed_executable is True
        assert result.observation.observed_execution_status == "ACCEPTED"
        assert result.observation.event_count == 6

        metric_names = [metric.name for metric in result.metrics]
        assert metric_names == ["event_count", "decision_duration_ms"]


def test_benchmark_runner_passes_denied_consent_scenario():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "bench_denied.jsonl"
        runner = BenchmarkRunner(
            service_factory=make_service_factory(log_path),
        )

        scenario = make_consent_scenario(
            scenario_id="consent-denied-001",
            title="Missing consent blocks support contact",
            explicit_consent=False,
            expected_status="DENIED",
            expected_executable=False,
            expected_fault_reason="consent_missing_or_invalid",
        )

        result = runner.run(scenario)

        assert result.outcome == BenchmarkOutcome.PASS
        assert result.reason_code == "expectation_met"
        assert result.observation.observed_status == "DENIED"
        assert result.observation.observed_executable is False
        assert result.observation.observed_fault_reason == "consent_missing_or_invalid"
        assert result.observation.observed_execution_status == ""
        assert result.observation.event_count == 5


def test_benchmark_runner_reports_fail_for_wrong_expectation():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "bench_fail.jsonl"
        runner = BenchmarkRunner(
            service_factory=make_service_factory(log_path),
        )

        scenario = make_consent_scenario(
            scenario_id="consent-fail-001",
            title="Intentional mismatch to verify FAIL behavior",
            explicit_consent=False,
            expected_status="APPROVED",
            expected_executable=True,
            expected_execution_status="ACCEPTED",
        )

        result = runner.run(scenario)

        assert result.outcome == BenchmarkOutcome.FAIL
        assert result.observation.observed_status == "DENIED"
        assert result.observation.observed_executable is False
        assert result.reason_code == "status_mismatch:APPROVED!=DENIED"


def test_benchmark_runner_reports_error_for_malformed_scenario():
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "bench_error.jsonl"
        runner = BenchmarkRunner(
            service_factory=make_service_factory(log_path),
        )

        bad_scenario = BenchmarkScenario(
            scenario_id="scenario-error-001",
            title="Malformed pose input should trigger runner error",
            domain=BenchmarkDomain.CONSENT,
            description="Pose xyz has the wrong length.",
            inputs={
                "session": {
                    "session_id": "sess-1",
                    "subject_id": "person-1",
                    "interaction_state": "IDLE",
                    "execution_state": "IDLE",
                    "safety_level": "GREEN",
                },
                "request": {
                    "request_id": "req-1",
                    "interaction_kind": "SUPPORT_CONTACT",
                    "source": "BENCHMARK",
                    "target_name": "shoulder",
                    "requested_scope": "shoulder_contact",
                    "requires_contact": True,
                    "requires_consent_freshness": True,
                },
                "consent": {
                    "grant_explicit": True,
                    "scopes": ["shoulder_contact"],
                    "source": "benchmark",
                },
                "nudge": {
                    "level": "GREEN",
                    "target": {
                        "frame": "W",
                        "xyz": [0.42, -0.18],  # malformed on purpose
                        "rpy": [0.0, 0.0, 1.57],
                    },
                    "normal": [0.0, 0.8, 0.6],
                    "rationale": "bad pose",
                    "priority": 0.9,
                    "expires_in_ms": 500,
                },
            },
            expectation=BenchmarkExpectation(
                expected_status="APPROVED",
                expected_executable=True,
                expected_execution_status="ACCEPTED",
            ),
            tags=("error", "validation"),
        )

        result = runner.run(bad_scenario)

        assert result.outcome == BenchmarkOutcome.ERROR
        assert result.reason_code.startswith("runner_error:")
        assert result.observation.observed_status == "ERROR"
        assert result.observation.event_count == 0
