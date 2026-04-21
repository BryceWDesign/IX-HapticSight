"""
Built-in deterministic benchmark scenarios for IX-HapticSight.

This module provides a small catalog of reusable benchmark scenarios that can
be run against the current RuntimeService + BenchmarkRunner stack.

The intent is to make common evaluation paths explicit and discoverable:
- consent happy path
- consent denial path
- safety denial path
- execution capability mismatch path

These scenarios are still repository-stage artifacts, not deployment evidence.
"""

from __future__ import annotations

from .models import (
    BenchmarkDomain,
    BenchmarkExpectation,
    BenchmarkScenario,
)
from .runner import make_consent_scenario


def make_safety_red_scenario() -> BenchmarkScenario:
    """
    Contact request with explicit consent but a RED session safety level.

    Expected result:
    - DENIED
    - not executable
    - fault reason tied to session safety red
    """
    return BenchmarkScenario(
        scenario_id="safety-red-001",
        title="RED safety level blocks support contact",
        domain=BenchmarkDomain.SAFETY,
        description=(
            "A contact request should be denied when the session starts in RED "
            "safety state even if explicit consent exists."
        ),
        inputs={
            "session": {
                "session_id": "sess-1",
                "subject_id": "person-1",
                "interaction_state": "IDLE",
                "execution_state": "IDLE",
                "safety_level": "RED",
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
                "grant_explicit": True,
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
            expected_status="DENIED",
            expected_executable=False,
            expected_fault_reason="session_safety_red",
            expected_execution_status="",
        ),
        tags=("safety", "red", "contact", "benchmark"),
    )


def make_consent_catalog() -> list[BenchmarkScenario]:
    """
    Standard consent-path scenarios for the current repo stage.
    """
    return [
        make_consent_scenario(
            scenario_id="consent-approved-001",
            title="Explicit consent allows support contact",
            explicit_consent=True,
            expected_status="APPROVED",
            expected_executable=True,
            expected_execution_status="ACCEPTED",
        ),
        make_consent_scenario(
            scenario_id="consent-denied-001",
            title="Missing consent blocks support contact",
            explicit_consent=False,
            expected_status="DENIED",
            expected_executable=False,
            expected_fault_reason="consent_missing_or_invalid",
        ),
    ]


def make_core_catalog() -> list[BenchmarkScenario]:
    """
    Core benchmark catalog for current repository maturity.

    This intentionally stays small and deterministic. More scenarios can be
    added later once the runtime, replay, and logging layers deepen.
    """
    catalog: list[BenchmarkScenario] = []
    catalog.extend(make_consent_catalog())
    catalog.append(make_safety_red_scenario())
    return catalog


def scenario_ids(scenarios: list[BenchmarkScenario]) -> list[str]:
    """
    Return the ordered scenario IDs from a benchmark catalog.
    """
    return [scenario.scenario_id for scenario in scenarios]


__all__ = [
    "make_safety_red_scenario",
    "make_consent_catalog",
    "make_core_catalog",
    "scenario_ids",
]
