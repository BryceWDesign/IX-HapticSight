# IX-HapticSight Documentation Index

This index is the top-level map for repository documentation outside the main README.

The README is reserved for final project presentation and onboarding.
This document is for internal navigation and upgrade-era structure.

## Current Core Documents

### Protocol and behavior
- `docs/spec.md`
  - Defines the Optical-Haptic Interaction Protocol baseline, interaction semantics, and primary concepts.

- `docs/state_machine.md`
  - Describes the interaction state model and expected transition behavior.

### Repository governance
- `CONTRIBUTING.md`
  - Contribution rules, review expectations, and safety-first development constraints.

- `ROADMAP.md`
  - Planned maturity path from reference implementation to stronger runtime and evidence-oriented architecture.

- `CHANGELOG.md`
  - Recorded change history and major release milestones.

## Planned Documentation Additions

The following documents are expected to be added during the 72-commit upgrade campaign.

### Architecture
- `docs/architecture/runtime_overview.md`
- `docs/architecture/package_map.md`
- `docs/architecture/node_graph.md`
- `docs/architecture/execution_adapter.md`

### Safety and requirements
- `docs/safety/invariants.md`
- `docs/safety/requirements_traceability.md`
- `docs/safety/fault_handling.md`
- `docs/safety/retreat_semantics.md`

### Sensing and contact
- `docs/sensing/force_torque.md`
- `docs/sensing/tactile.md`
- `docs/sensing/proximity.md`
- `docs/sensing/thermal.md`
- `docs/sensing/contact_fusion.md`

### Replay and benchmarks
- `docs/benchmarks/overview.md`
- `docs/benchmarks/scenario_catalog.md`
- `docs/benchmarks/metrics.md`
- `docs/replay/event_log_schema.md`

### Governance and evidence
- `docs/governance/threat_model.md`
- `docs/governance/privacy_data_handling.md`
- `docs/governance/standards_crosswalk.md`
- `docs/governance/safety_case.md`

### Hardware-in-the-loop
- `docs/hil/test_rig_architecture.md`
- `docs/hil/calibration.md`
- `docs/hil/fault_injection.md`

## Reading Order for Reviewers

Recommended order for technical reviewers:

1. `docs/spec.md`
2. `docs/state_machine.md`
3. `ROADMAP.md`
4. `CONTRIBUTING.md`
5. architecture documents as they are added
6. sensing documents as they are added
7. benchmark and safety documents as they are added

## Documentation Rules

All new technical documents should:

- state scope clearly
- distinguish current implementation from planned behavior
- avoid unsupported deployment claims
- identify assumptions and limits
- remain consistent with the project state machine and safety philosophy

## Note on README Timing

The README is intentionally being updated last in this upgrade campaign so that it reflects the final repository structure and avoids repeated churn during manual commit-by-commit application.
