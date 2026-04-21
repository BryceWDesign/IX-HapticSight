"""
Deterministic benchmark runner for IX-HapticSight.

This module provides a small, backend-agnostic benchmark harness that can
exercise the current runtime service against explicit scenario definitions.

The runner is intentionally conservative:
- one fresh runtime service per scenario
- one explicit session per scenario
- one explicit request path per scenario
- structured observation and metrics only
- no hidden global state

Scenario input convention
-------------------------
The benchmark runner expects `BenchmarkScenario.inputs` to contain plain Python
data under a few stable keys. Supported keys include:

- "session":
    {
        "session_id": "sess-1",
        "subject_id": "person-1",
        "interaction_state": "IDLE",
        "execution_state": "IDLE",
        "safety_level": "GREEN",
        "consent_valid": false,
        "consent_fresh": false
    }

- "request":
    {
        "request_id": "req-1",
        "interaction_kind": "SUPPORT_CONTACT",
        "source": "OPERATOR",
        "target_name": "shoulder",
        "requested_scope": "shoulder_contact",
        "requires_contact": true,
        "requires_consent_freshness": true
    }

- "consent":
    {
        "grant_explicit": true,
        "scopes": ["shoulder_contact"],
        "source": "verbal"
    }

- "nudge":
    {
        "level": "GREEN",
        "target": {"frame": "W", "xyz": [0.42, -0.18, 1.36], "rpy": [0.0, 0.0, 1.57]},
        "normal": [0.0, 0.8, 0.6],
        "rationale": "test shoulder support",
        "priority": 0.9,
        "expires_in_ms": 500
    }

- "start_pose":
    {"frame": "W", "xyz": [0.10, 0.00, 1.00], "rpy": [0.0, 0.0, 0.0]}
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Callable, Optional

from ohip.schemas import Nudge, NudgeLevel, Pose, RPY, SafetyLevel, Vector3
from ohip_runtime.requests import (
    InteractionKind,
    InteractionRequest,
    RequestSource,
)
from ohip_runtime.runtime_service import RuntimeService, RuntimeServiceResult
from ohip_runtime.state import (
    ExecutionState,
    InteractionSession,
    InteractionState,
    RuntimeHealth,
)

from .models import (
    BenchmarkDomain,
    BenchmarkExpectation,
    BenchmarkMetric,
    BenchmarkObservation,
    BenchmarkOutcome,
    BenchmarkResult,
    BenchmarkScenario,
    compare_expectation,
)


RuntimeServiceFactory = Callable[[], RuntimeService]


@dataclass(frozen=True)
class BenchmarkRunArtifacts:
    """
    Internal structured bundle from one benchmark execution.
    """

    service_result: RuntimeServiceResult
    event_count: int
    duration_ms: float


class BenchmarkRunner:
    """
    Deterministic benchmark runner for RuntimeService-backed scenarios.
    """

    def __init__(self, *, service_factory: RuntimeServiceFactory) -> None:
        self._service_factory = service_factory

    def run(self, scenario: BenchmarkScenario) -> BenchmarkResult:
        started = time()
        try:
            artifacts = self._execute_scenario(scenario)
            observation = self._make_observation(artifacts.service_result, artifacts.event_count)
            success, reason = compare_expectation(
                expectation=scenario.expectation,
                observation=observation,
            )
            outcome = BenchmarkOutcome.PASS if success else BenchmarkOutcome.FAIL

            metrics = (
                BenchmarkMetric(
                    name="event_count",
                    value=float(artifacts.event_count),
                    unit="count",
                    note="structured events emitted during the scenario",
                ),
                BenchmarkMetric(
                    name="decision_duration_ms",
                    value=float(artifacts.duration_ms),
                    unit="ms",
                    note="wall-clock time spent handling the runtime request",
                ),
            )

            finished = time()
            return BenchmarkResult(
                scenario_id=scenario.scenario_id,
                domain=scenario.domain,
                outcome=outcome,
                observation=observation,
                metrics=metrics,
                reason_code=reason,
                started_at_utc_s=started,
                finished_at_utc_s=finished,
            )

        except Exception as exc:  # noqa: BLE001
            finished = time()
            return BenchmarkResult(
                scenario_id=scenario.scenario_id,
                domain=scenario.domain,
                outcome=BenchmarkOutcome.ERROR,
                observation=BenchmarkObservation(
                    observed_status="ERROR",
                    observed_executable=None,
                    observed_fault_reason=str(exc),
                    observed_execution_status="",
                    event_count=0,
                ),
                metrics=(),
                reason_code=f"runner_error:{type(exc).__name__}",
                started_at_utc_s=started,
                finished_at_utc_s=finished,
            )

    def run_many(self, scenarios: list[BenchmarkScenario]) -> list[BenchmarkResult]:
        return [self.run(scenario) for scenario in scenarios]

    def _execute_scenario(self, scenario: BenchmarkScenario) -> BenchmarkRunArtifacts:
        service = self._service_factory()

        session = self._build_session(scenario)
        service.upsert_session(session)

        self._apply_scenario_consent(service, scenario, session)

        request = self._build_request(scenario, session)
        nudge = self._build_nudge(scenario)
        start_pose = self._build_start_pose(scenario)

        started = time()
        result = service.handle_request(
            request=request,
            nudge=nudge,
            start_pose=start_pose,
        )
        finished = time()

        recorder_buffer = service._recorder.buffer()  # noqa: SLF001
        return BenchmarkRunArtifacts(
            service_result=result,
            event_count=len(recorder_buffer),
            duration_ms=max(0.0, (finished - started) * 1000.0),
        )

    @staticmethod
    def _make_observation(
        result: RuntimeServiceResult,
        event_count: int,
    ) -> BenchmarkObservation:
        execution_status = ""
        if result.execution_response is not None:
            execution_status = result.execution_response.status.value

        fault_reason = ""
        if result.session.active_fault is not None:
            fault_reason = result.session.active_fault.reason_code

        return BenchmarkObservation(
            observed_status=result.decision.status.value,
            observed_executable=bool(result.decision.executable),
            observed_fault_reason=fault_reason,
            observed_execution_status=execution_status,
            event_count=event_count,
        )

    @staticmethod
    def _build_session(scenario: BenchmarkScenario) -> InteractionSession:
        data = dict(scenario.inputs.get("session", {}))

        session_id = str(data.get("session_id", "bench-session"))
        subject_id = data.get("subject_id", "bench-subject")

        interaction_state = InteractionState(str(data.get("interaction_state", "IDLE")))
        execution_state = ExecutionState(str(data.get("execution_state", "IDLE")))
        safety_level = SafetyLevel(str(data.get("safety_level", "GREEN")))

        consent_valid = bool(data.get("consent_valid", False))
        consent_fresh = bool(data.get("consent_fresh", False))

        return InteractionSession(
            session_id=session_id,
            subject_id=None if subject_id is None else str(subject_id),
            interaction_state=interaction_state,
            execution_state=execution_state,
            runtime_health=RuntimeHealth.NOMINAL,
            safety_level=safety_level,
            consent_valid=consent_valid,
            consent_fresh=consent_fresh,
        )

    @staticmethod
    def _build_request(
        scenario: BenchmarkScenario,
        session: InteractionSession,
    ) -> InteractionRequest:
        data = dict(scenario.inputs.get("request", {}))

        return InteractionRequest(
            request_id=str(data.get("request_id", "bench-request")),
            session_id=session.session_id,
            subject_id=session.subject_id,
            interaction_kind=InteractionKind(str(data.get("interaction_kind", "SUPPORT_CONTACT"))),
            source=RequestSource(str(data.get("source", "BENCHMARK"))),
            target_name=str(data.get("target_name", "")),
            requested_scope=str(data.get("requested_scope", "")),
            requires_contact=bool(data.get("requires_contact", False)),
            requires_consent_freshness=bool(data.get("requires_consent_freshness", True)),
            notes=str(data.get("notes", "")),
        )

    @staticmethod
    def _build_pose(data: dict) -> Pose:
        frame = str(data.get("frame", "W"))
        xyz = list(data.get("xyz", [0.0, 0.0, 0.0]))
        rpy = list(data.get("rpy", [0.0, 0.0, 0.0]))

        if len(xyz) != 3:
            raise ValueError("pose.xyz must contain exactly 3 elements")
        if len(rpy) != 3:
            raise ValueError("pose.rpy must contain exactly 3 elements")

        return Pose(
            frame=frame,
            xyz=Vector3(float(xyz[0]), float(xyz[1]), float(xyz[2])),
            rpy=RPY(float(rpy[0]), float(rpy[1]), float(rpy[2])),
        )

    def _build_nudge(self, scenario: BenchmarkScenario) -> Optional[Nudge]:
        data = scenario.inputs.get("nudge")
        if not data:
            return None

        nudge_data = dict(data)
        normal = list(nudge_data.get("normal", [0.0, 0.0, 1.0]))
        if len(normal) != 3:
            raise ValueError("nudge.normal must contain exactly 3 elements")

        return Nudge(
            level=NudgeLevel(str(nudge_data.get("level", "GREEN"))),
            target=self._build_pose(dict(nudge_data["target"])),
            normal=Vector3(float(normal[0]), float(normal[1]), float(normal[2])),
            rationale=str(nudge_data.get("rationale", "")),
            priority=float(nudge_data.get("priority", 0.5)),
            expires_in_ms=int(nudge_data.get("expires_in_ms", 500)),
        )

    def _build_start_pose(self, scenario: BenchmarkScenario) -> Optional[Pose]:
        data = scenario.inputs.get("start_pose")
        if not data:
            return None
        return self._build_pose(dict(data))

    @staticmethod
    def _apply_scenario_consent(
        service: RuntimeService,
        scenario: BenchmarkScenario,
        session: InteractionSession,
    ) -> None:
        consent_data = dict(scenario.inputs.get("consent", {}))
        if not consent_data:
            return

        grant_explicit = bool(consent_data.get("grant_explicit", False))
        if not grant_explicit:
            return

        scopes = list(consent_data.get("scopes", []))
        source = str(consent_data.get("source", "benchmark"))
        if session.subject_id is None:
            raise ValueError("explicit benchmark consent requires session.subject_id")

        service._coordinator._consent.grant_explicit(  # noqa: SLF001
            subject_id=session.subject_id,
            scopes=scopes,
            source=source,
        )


def make_consent_scenario(
    *,
    scenario_id: str,
    title: str,
    explicit_consent: bool,
    expected_status: str,
    expected_executable: bool,
    expected_execution_status: str = "",
    expected_fault_reason: str = "",
) -> BenchmarkScenario:
    """
    Convenience helper for common consent-path benchmark scenarios.
    """
    return BenchmarkScenario(
        scenario_id=scenario_id,
        title=title,
        domain=BenchmarkDomain.CONSENT,
        description=title,
        inputs={
            "session": {
                "session_id": "sess-1",
                "subject_id": "person-1",
                "interaction_state": "IDLE",
                "execution_state": "IDLE",
                "safety_level": "GREEN",
                "consent_valid": False,
                "consent_fresh": False,
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
                "grant_explicit": explicit_consent,
                "scopes": ["shoulder_contact"],
                "source": "benchmark",
            },
            "nudge": {
                "level": "GREEN",
                "target": {
                    "frame": "W",
                    "xyz": [0.42, -0.18, 1.36],
                    "rpy": [0.0, 0.0, 1.57],
                },
                "normal": [0.0, 0.8, 0.6],
                "rationale": "benchmark shoulder support",
                "priority": 0.9,
                "expires_in_ms": 500,
            },
            "start_pose": {
                "frame": "W",
                "xyz": [0.10, 0.00, 1.00],
                "rpy": [0.0, 0.0, 0.0],
            },
        },
        expectation=BenchmarkExpectation(
            expected_status=expected_status,
            expected_executable=expected_executable,
            expected_fault_reason=expected_fault_reason,
            expected_execution_status=expected_execution_status,
        ),
        tags=("consent", "runtime", "benchmark"),
    )


__all__ = [
    "BenchmarkRunner",
    "make_consent_scenario",
]
