"""
Runtime configuration loading and component wiring for IX-HapticSight.

This module provides a disciplined path for loading the repository's YAML
configuration files and constructing the baseline runtime-facing core objects:

- ConsentManager
- ContactPlanner
- SafetyGate

It is intentionally conservative:
- no hidden global state
- no ROS 2 assumptions
- no backend transport code
- explicit validation of key profile bindings

The goal is to reduce configuration ambiguity before deeper runtime and
execution layers are added.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from ohip.consent_manager import ConsentManager
from ohip.contact_planner import ContactPlanner
from ohip.safety_gate import HardwareInterface, SafetyGate


@dataclass(frozen=True)
class RuntimeComponentBundle:
    """
    Convenience bundle for the baseline runtime core objects.

    This is not a service container or dependency-injection framework.
    It is just a small explicit grouping that future runtime wrappers can use.
    """

    consent_manager: ConsentManager
    contact_planner: ContactPlanner
    safety_gate: SafetyGate


@dataclass(frozen=True)
class RuntimeConfigBundle:
    """
    Parsed runtime configuration bundle loaded from repository YAML files.
    """

    force_limits: dict[str, Any]
    culture_profiles: dict[str, Any]
    force_limits_path: Path
    culture_profiles_path: Path

    @classmethod
    def from_files(
        cls,
        *,
        force_limits_path: str | Path,
        culture_profiles_path: str | Path,
    ) -> "RuntimeConfigBundle":
        force_path = Path(force_limits_path).expanduser().resolve()
        culture_path = Path(culture_profiles_path).expanduser().resolve()

        if not force_path.is_file():
            raise FileNotFoundError(f"force limits config not found: {force_path}")
        if not culture_path.is_file():
            raise FileNotFoundError(f"culture profiles config not found: {culture_path}")

        force_limits = _load_yaml_file(force_path)
        culture_profiles = _load_yaml_file(culture_path)

        bundle = cls(
            force_limits=force_limits,
            culture_profiles=culture_profiles,
            force_limits_path=force_path,
            culture_profiles_path=culture_path,
        )
        bundle.validate()
        return bundle

    @classmethod
    def from_repo_root(cls, repo_root: str | Path) -> "RuntimeConfigBundle":
        root = Path(repo_root).expanduser().resolve()
        return cls.from_files(
            force_limits_path=root / "configs" / "force_limits.yaml",
            culture_profiles_path=root / "configs" / "culture_profiles.yaml",
        )

    def validate(self) -> None:
        """
        Validate key repository configuration assumptions.

        This is intentionally targeted validation, not a full schema system.
        It catches the most dangerous mismatches early:
        - missing defaults
        - missing profile sections
        - broken profile bindings between culture and force configs
        """
        _require_mapping(self.force_limits, "force_limits")
        _require_mapping(self.culture_profiles, "culture_profiles")

        force_profiles = self.force_limits.get("profiles")
        force_defaults = self.force_limits.get("defaults")
        culture_defaults = self.culture_profiles.get("defaults")
        culture_profiles = self.culture_profiles.get("profiles")

        _require_mapping(force_profiles, "force_limits.profiles")
        _require_mapping(force_defaults, "force_limits.defaults")
        _require_mapping(culture_defaults, "culture_profiles.defaults")
        _require_mapping(culture_profiles, "culture_profiles.profiles")

        social_profile = force_defaults.get("social_touch_profile")
        if not social_profile:
            raise ValueError("force_limits.defaults.social_touch_profile is required")
        if social_profile not in force_profiles:
            raise ValueError(
                f"force_limits.defaults.social_touch_profile references unknown profile: {social_profile}"
            )

        object_profile = force_defaults.get("object_profile")
        if object_profile and object_profile not in force_profiles:
            raise ValueError(
                f"force_limits.defaults.object_profile references unknown profile: {object_profile}"
            )

        inspection_profile = force_defaults.get("inspection_profile")
        if inspection_profile and inspection_profile not in force_profiles:
            raise ValueError(
                f"force_limits.defaults.inspection_profile references unknown profile: {inspection_profile}"
            )

        default_binding = (
            (culture_defaults.get("bindings") or {}).get("force_profile")
            if isinstance(culture_defaults.get("bindings"), dict)
            else None
        )
        if default_binding and default_binding not in force_profiles:
            raise ValueError(
                f"culture_profiles.defaults.bindings.force_profile references unknown force profile: {default_binding}"
            )

        for profile_name, profile_data in culture_profiles.items():
            if not isinstance(profile_data, dict):
                raise ValueError(f"culture profile must be a mapping: {profile_name}")

            bindings = profile_data.get("bindings") or {}
            if bindings and not isinstance(bindings, dict):
                raise ValueError(f"culture profile bindings must be a mapping: {profile_name}")

            force_profile = bindings.get("force_profile")
            if force_profile and force_profile not in force_profiles:
                raise ValueError(
                    f"culture profile '{profile_name}' references unknown force profile: {force_profile}"
                )

    @property
    def force_profile_names(self) -> list[str]:
        profiles = self.force_limits.get("profiles", {})
        return sorted(profiles.keys())

    @property
    def culture_profile_names(self) -> list[str]:
        profiles = self.culture_profiles.get("profiles", {})
        return sorted(profiles.keys())

    @property
    def phrase_bank(self) -> dict[str, dict[str, str]]:
        phrase_bank = self.culture_profiles.get("phrase_bank", {})
        if not isinstance(phrase_bank, dict):
            return {}
        return phrase_bank

    def get_culture_profile(self, profile_name: str = "default") -> dict[str, Any]:
        profiles = self.culture_profiles.get("profiles", {})
        if profile_name not in profiles:
            available = ", ".join(sorted(profiles.keys()))
            raise KeyError(f"unknown culture profile '{profile_name}'. available: {available}")
        profile = profiles[profile_name]
        if not isinstance(profile, dict):
            raise ValueError(f"culture profile must be a mapping: {profile_name}")
        return profile

    def default_force_profile_name(self) -> str:
        defaults = self.force_limits.get("defaults", {})
        profile_name = defaults.get("social_touch_profile")
        if not profile_name:
            raise ValueError("force_limits.defaults.social_touch_profile is missing")
        return str(profile_name)

    def bound_force_profile_for_culture(self, profile_name: str = "default") -> str:
        profile = self.get_culture_profile(profile_name)
        bindings = profile.get("bindings") or {}
        if isinstance(bindings, dict) and bindings.get("force_profile"):
            return str(bindings["force_profile"])

        defaults = self.culture_profiles.get("defaults", {})
        default_bindings = defaults.get("bindings") or {}
        if isinstance(default_bindings, dict) and default_bindings.get("force_profile"):
            return str(default_bindings["force_profile"])

        return self.default_force_profile_name()

    def build_consent_manager(
        self,
        *,
        culture_profile_name: str = "default",
        institutional_policy_enabled: bool = False,
    ) -> ConsentManager:
        defaults = self.culture_profiles.get("defaults", {})
        profile = self.get_culture_profile(culture_profile_name)

        manager = ConsentManager()
        manager.set_profile_from_dict(profile, defaults=defaults if isinstance(defaults, dict) else None)
        manager.enable_institutional_policy(institutional_policy_enabled)
        return manager

    def build_contact_planner(self) -> ContactPlanner:
        return ContactPlanner(self.force_limits)

    def build_safety_gate(
        self,
        *,
        hw_iface: Optional[HardwareInterface] = None,
        active_profile: Optional[str] = None,
    ) -> SafetyGate:
        return SafetyGate(
            self.force_limits,
            hw_iface=hw_iface,
            active_profile=active_profile,
        )

    def build_runtime_components(
        self,
        *,
        culture_profile_name: str = "default",
        institutional_policy_enabled: bool = False,
        hw_iface: Optional[HardwareInterface] = None,
    ) -> RuntimeComponentBundle:
        """
        Construct the baseline runtime core objects using repository configs.

        The safety gate's active force profile is selected from the culture
        profile binding when available so runtime wiring stays consistent.
        """
        active_force_profile = self.bound_force_profile_for_culture(culture_profile_name)

        return RuntimeComponentBundle(
            consent_manager=self.build_consent_manager(
                culture_profile_name=culture_profile_name,
                institutional_policy_enabled=institutional_policy_enabled,
            ),
            contact_planner=self.build_contact_planner(),
            safety_gate=self.build_safety_gate(
                hw_iface=hw_iface,
                active_profile=active_force_profile,
            ),
        )


def _load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected top-level mapping in YAML file: {path}")
    return data


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")


__all__ = [
    "RuntimeComponentBundle",
    "RuntimeConfigBundle",
]
