"""
IX-HapticSight — Tests for runtime configuration loading and wiring.

These tests validate the new runtime configuration bundle against the
repository's real YAML files and a few targeted invalid-config cases.
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Make both `ohip` and `ohip_runtime` importable without packaging
sys.path.insert(0, os.path.abspath("src"))

import yaml  # noqa: E402

from ohip.consent_manager import ConsentManager  # noqa: E402
from ohip.contact_planner import ContactPlanner  # noqa: E402
from ohip.safety_gate import SafetyGate  # noqa: E402
from ohip_runtime.config import (  # noqa: E402
    RuntimeComponentBundle,
    RuntimeConfigBundle,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_runtime_config_bundle_loads_real_repo_files():
    bundle = RuntimeConfigBundle.from_repo_root(repo_root())

    assert bundle.force_limits_path.name == "force_limits.yaml"
    assert bundle.culture_profiles_path.name == "culture_profiles.yaml"

    assert "profiles" in bundle.force_limits
    assert "profiles" in bundle.culture_profiles

    assert "human_soft_touch_v1" in bundle.force_profile_names
    assert "default" in bundle.culture_profile_names
    assert "support_request" in bundle.phrase_bank

    assert bundle.default_force_profile_name() == "human_soft_touch_v1"
    assert bundle.bound_force_profile_for_culture("default") == "human_soft_touch_v1"
    assert bundle.bound_force_profile_for_culture("us") == "human_soft_touch_v1"


def test_runtime_config_builds_runtime_components_from_real_repo_files():
    bundle = RuntimeConfigBundle.from_repo_root(repo_root())

    components = bundle.build_runtime_components(
        culture_profile_name="default",
        institutional_policy_enabled=False,
    )

    assert isinstance(components, RuntimeComponentBundle)
    assert isinstance(components.consent_manager, ConsentManager)
    assert isinstance(components.contact_planner, ContactPlanner)
    assert isinstance(components.safety_gate, SafetyGate)
    assert components.safety_gate._active_profile == "human_soft_touch_v1"


def test_get_culture_profile_unknown_raises():
    bundle = RuntimeConfigBundle.from_repo_root(repo_root())

    try:
        bundle.get_culture_profile("missing_profile")
        raised = False
    except KeyError:
        raised = True

    assert raised is True


def test_invalid_force_profile_binding_is_rejected():
    root = repo_root()
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        force_data = yaml.safe_load((root / "configs" / "force_limits.yaml").read_text(encoding="utf-8"))
        culture_data = yaml.safe_load((root / "configs" / "culture_profiles.yaml").read_text(encoding="utf-8"))

        culture_data["profiles"]["default"]["bindings"]["force_profile"] = "does_not_exist"

        force_path = tmp / "force_limits.yaml"
        culture_path = tmp / "culture_profiles.yaml"

        force_path.write_text(yaml.safe_dump(force_data, sort_keys=False), encoding="utf-8")
        culture_path.write_text(yaml.safe_dump(culture_data, sort_keys=False), encoding="utf-8")

        try:
            RuntimeConfigBundle.from_files(
                force_limits_path=force_path,
                culture_profiles_path=culture_path,
            )
            raised = False
        except ValueError as exc:
            raised = True
            assert "unknown force profile" in str(exc)

        assert raised is True


def test_missing_social_touch_profile_is_rejected():
    root = repo_root()
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        force_data = yaml.safe_load((root / "configs" / "force_limits.yaml").read_text(encoding="utf-8"))
        culture_data = yaml.safe_load((root / "configs" / "culture_profiles.yaml").read_text(encoding="utf-8"))

        force_data["defaults"].pop("social_touch_profile", None)

        force_path = tmp / "force_limits.yaml"
        culture_path = tmp / "culture_profiles.yaml"

        force_path.write_text(yaml.safe_dump(force_data, sort_keys=False), encoding="utf-8")
        culture_path.write_text(yaml.safe_dump(culture_data, sort_keys=False), encoding="utf-8")

        try:
            RuntimeConfigBundle.from_files(
                force_limits_path=force_path,
                culture_profiles_path=culture_path,
            )
            raised = False
        except ValueError as exc:
            raised = True
            assert "social_touch_profile" in str(exc)

        assert raised is True
