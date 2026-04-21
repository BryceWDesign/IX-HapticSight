# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.
This project follows semantic versioning principles for tagged releases.

## [Unreleased]

### Added
- Python packaging baseline via `pyproject.toml`.
- Repository hygiene baseline via `.gitignore`.
- Changelog for tracking safety, runtime, benchmark, and governance upgrades across the v0.1 to v1.0 buildout.

### Planned
- Repository authorship and scope cleanup.
- Runtime package restructuring.
- ROS 2 lifecycle node scaffolding.
- Motion execution and safety shield expansion.
- Tactile, proximity, thermal, and force/torque interfaces.
- Logging, replay, integrity, and threat-model artifacts.
- Benchmark harnesses and simulation scenario packs.
- HIL scaffolding and safety-case traceability artifacts.

## [0.1.0] - 2026-04-10

### Added
- Initial OHIP schemas and protocol reference implementation.
- Consent management logic.
- Contact planning logic.
- Nudge scheduling logic.
- Rest-pose generation logic.
- Safety gate logic.
- Example quickstart script.
- Core configuration files for force limits and culture profiles.
- Basic simulation scene.
- Unit tests for schemas and scheduler.

### Notes
- `0.1.0` is the pre-upgrade baseline imported before the 72-commit architecture and runtime expansion campaign.
- The project at this stage is a reference implementation and documentation-first prototype, not a deployable robotics runtime.
