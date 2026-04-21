"""
IX-HapticSight — Tests for built-in benchmark scenario catalogs.

These tests verify that the benchmark scenario catalog remains explicit,
deterministic, and internally consistent.
"""

import os
import sys

# Make project packages importable without packaging/install
sys.path.insert(0, os.path.abspath("src"))

from ohip_bench.models import BenchmarkDomain  # noqa: E402
from ohip_bench.scenarios import (  # noqa: E402
    make_consent_catalog,
    make_core_catalog,
    make_safety_red_scenario,
    scenario_ids,
)


def test_make_safety_red_scenario_has_expected_shape():
    scenario = make_safety_red_scenario()

    assert scenario.scenario_id == "safety-red-001"
    assert scenario.domain == BenchmarkDomain.SAFETY
    assert scenario.inputs["session"]["safety_level"] == "RED"
    assert scenario.inputs["consent"]["grant_explicit"] is True
    assert scenario.inputs["request"]["requires_contact"] is True

    expectation = scenario.expectation
    assert expectation.expected_status == "DENIED"
    assert expectation.expected_executable is False
    assert expectation.expected_fault_reason == "session_safety_red"
    assert expectation.expected_execution_status == ""


def test_make_consent_catalog_contains_expected_scenarios():
    catalog = make_consent_catalog()

    assert len(catalog) == 2
    ids = scenario_ids(catalog)
    assert ids == [
        "consent-approved-001",
        "consent-denied-001",
    ]

    approved = catalog[0]
    denied = catalog[1]

    assert approved.domain == BenchmarkDomain.CONSENT
    assert approved.expectation.expected_status == "APPROVED"
    assert approved.expectation.expected_executable is True
    assert approved.expectation.expected_execution_status == "ACCEPTED"

    assert denied.domain == BenchmarkDomain.CONSENT
    assert denied.expectation.expected_status == "DENIED"
    assert denied.expectation.expected_executable is False
    assert denied.expectation.expected_fault_reason == "consent_missing_or_invalid"


def test_make_core_catalog_contains_consent_and_safety_cases():
    catalog = make_core_catalog()

    assert len(catalog) == 3

    ids = scenario_ids(catalog)
    assert ids == [
        "consent-approved-001",
        "consent-denied-001",
        "safety-red-001",
    ]

    domains = [scenario.domain for scenario in catalog]
    assert domains == [
        BenchmarkDomain.CONSENT,
        BenchmarkDomain.CONSENT,
        BenchmarkDomain.SAFETY,
    ]


def test_catalog_scenarios_have_non_empty_titles_descriptions_and_tags():
    catalog = make_core_catalog()

    for scenario in catalog:
        assert isinstance(scenario.title, str)
        assert scenario.title != ""
        assert isinstance(scenario.description, str)
        assert scenario.description != ""
        assert isinstance(scenario.tags, tuple)
        assert len(scenario.tags) >= 1


def test_scenario_ids_preserve_input_order():
    catalog = make_core_catalog()
    reversed_catalog = list(reversed(catalog))

    assert scenario_ids(catalog) == [
        "consent-approved-001",
        "consent-denied-001",
        "safety-red-001",
    ]
    assert scenario_ids(reversed_catalog) == [
        "safety-red-001",
        "consent-denied-001",
        "consent-approved-001",
    ]
