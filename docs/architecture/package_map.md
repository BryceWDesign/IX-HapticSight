# Package Map

This document defines the planned package responsibilities for the IX-HapticSight upgrade path.

It is written to separate stable protocol logic from runtime integration, sensing adapters, replay tooling, and benchmark infrastructure.

Where the current repository already has code, that is noted explicitly.
Where a package is planned but not yet fully implemented, that is also noted explicitly.

---

## 1. Current Package Baseline

The present repository has one core Python package:

- `src/ohip/`

That package currently contains:

- `__init__.py`
- `schemas.py`
- `consent_manager.py`
- `contact_planner.py`
- `nudge_scheduler.py`
- `rest_pose.py`
- `safety_gate.py`

This is a reasonable reference-implementation layout, but it mixes concerns that should eventually be separated for runtime clarity and long-term maintainability.

---

## 2. Target Package Direction

The long-term structure should preserve a small, understandable core and add adjacent packages for runtime, interfaces, replay, and benchmarking.

The target direction is:

- `src/ohip/`
- `src/ohip_runtime/`
- `src/ohip_interfaces/`
- `src/ohip_logging/`
- `src/ohip_bench/`
- `src/ohip_ros2/`

This does not mean all packages must become large immediately.
It means responsibilities should stop collapsing into one directory as the repository grows.

---

## 3. Planned Responsibility by Package

### `src/ohip/`
Purpose:
- stable protocol definitions
- canonical data models
- policy structures
- contact request semantics
- shared enums and validation helpers
- deterministic core logic that is runtime-agnostic

Current modules already here:
- `schemas.py`
- `consent_manager.py`
- `contact_planner.py`
- `nudge_scheduler.py`
- `rest_pose.py`
- `safety_gate.py`

Likely long-term contents:
- `schemas.py`
- `policy_models.py`
- `interaction_state.py`
- `consent_rules.py`
- `contact_constraints.py`
- `hazard_models.py`

Rule:
- this package should stay lightweight and not absorb runtime transport code

---

### `src/ohip_runtime/`
Purpose:
- runtime orchestration
- state ownership
- coordinator logic
- transition control
- timeout handling
- policy and safety evaluation sequencing
- runtime-level fault handling

Planned examples:
- runtime coordinator
- interaction session controller
- state transition manager
- fault latch manager
- watchdog helpers

Rule:
- this package decides when things happen, not how hardware talks

---

### `src/ohip_interfaces/`
Purpose:
- device-agnostic input/output interfaces
- normalized sensor payloads
- execution adapter contracts
- runtime backend abstraction

Planned subdomains:
- force-torque interfaces
- tactile interfaces
- proximity interfaces
- thermal interfaces
- execution command interfaces

Likely future modules:
- `force_torque.py`
- `tactile.py`
- `proximity.py`
- `thermal.py`
- `execution_adapter.py`
- `signal_health.py`

Rule:
- raw device-specific transport should not leak into core policy logic

---

### `src/ohip_logging/`
Purpose:
- structured event logging
- replay records
- event serialization
- audit bundle generation
- trace export helpers

Planned examples:
- event schema definitions
- log writers
- replay session loaders
- evidence bundle indexing
- transition history formatting

Rule:
- logs must explain behavior without requiring a human to read unrelated console output

---

### `src/ohip_bench/`
Purpose:
- benchmark scenario definitions
- metrics collection
- deterministic test harnesses
- replayable benchmark execution
- scenario result packaging

Planned benchmark groups:
- consent benchmarks
- hazard benchmarks
- contact benchmarks
- retreat and veto benchmarks
- logging/replay integrity benchmarks

Rule:
- benchmark logic should be independent from presentation docs and easy to re-run

---

### `src/ohip_ros2/`
Purpose:
- ROS 2-specific node wrappers
- ROS 2 message/service bridges
- parameter handling integration
- launch files
- lifecycle integration scaffolding

Planned examples:
- lifecycle nodes
- runtime coordinator node
- consent node
- safety node
- contact planning bridge
- replay publishing tools

Rule:
- ROS 2 integration should remain an adapter layer, not redefine protocol semantics

---

## 4. Relationship Between Packages

The dependency direction should be controlled.

Preferred dependency flow:

- `ohip`
  - has no dependency on ROS 2 packages
- `ohip_runtime`
  - may depend on `ohip`
- `ohip_interfaces`
  - may depend on `ohip`
- `ohip_logging`
  - may depend on `ohip`
- `ohip_bench`
  - may depend on `ohip`, `ohip_runtime`, and `ohip_logging`
- `ohip_ros2`
  - may depend on `ohip`, `ohip_runtime`, and `ohip_interfaces`

Avoid the reverse where possible.

In particular:
- `ohip` should not depend on `ohip_ros2`
- `ohip` should not depend on device transport libraries
- `ohip` should not depend on benchmark harness code

This keeps the protocol core portable and easy to test.

---

## 5. Current-to-Target Mapping

This section shows where existing modules are likely to remain or move conceptually.

### `src/ohip/schemas.py`
Current role:
- canonical protocol data types

Likely future role:
- remains in `ohip`
- may be split into smaller files over time

---

### `src/ohip/consent_manager.py`
Current role:
- consent evaluation logic

Likely future role:
- remains partially in `ohip`
- runtime-facing orchestration may move to `ohip_runtime`

Split concept:
- rule evaluation stays in core
- session/time handling moves to runtime

---

### `src/ohip/contact_planner.py`
Current role:
- bounded contact decision logic

Likely future role:
- core planning constraints remain in `ohip`
- execution-bound planning orchestration may use `ohip_runtime`
- hardware command translation belongs in interfaces or ROS 2 integration

---

### `src/ohip/nudge_scheduler.py`
Current role:
- schedule and timing logic for interaction

Likely future role:
- policy rules remain in `ohip`
- runtime timers and callbacks move to `ohip_runtime`

---

### `src/ohip/rest_pose.py`
Current role:
- rest and posture generation logic

Likely future role:
- posture target generation can remain in `ohip`
- runtime delivery of poses belongs elsewhere

---

### `src/ohip/safety_gate.py`
Current role:
- hazard and force gating logic

Likely future role:
- core safety decision rules remain in `ohip`
- runtime watchdog, fault latching, and actuator abort routing live in `ohip_runtime`

---

## 6. Why This Separation Matters

The current repository is still small enough that everything in one package is understandable.

That will stop being true once the project gains:

- runtime coordinators
- sensing adapters
- message definitions
- replay tooling
- benchmark runners
- ROS 2 nodes
- HIL scaffolding

Without separation, the result becomes harder to review and easier to break.

With separation:
- policy stays readable
- runtime stays replaceable
- interfaces stay swappable
- evidence tooling stays organized

---

## 7. Review Questions for New Package Work

When adding or moving code, the reviewer should ask:

1. Does this belong in the protocol core or in runtime plumbing?
2. Does this code depend on a specific backend or transport?
3. Could this logic be reused without ROS 2?
4. Is this sensor-specific or policy-generic?
5. Is this behavior needed at runtime, or only for replay or benchmarking?
6. Does this change make the dependency graph cleaner or worse?

If the answer is unclear, the default should be to keep the protocol core smaller.

---

## 8. Near-Term Package Priorities

The first package-growth priorities should be:

1. preserve and stabilize `ohip`
2. create `ohip_runtime` for orchestration
3. create `ohip_interfaces` for sensing and execution boundaries
4. create `ohip_logging` for structured event and replay artifacts
5. create `ohip_bench` for benchmark harnesses
6. add `ohip_ros2` after the previous boundaries are clear

This order reduces confusion and prevents ROS-specific assumptions from leaking into everything else.

---

## 9. Final Rule

The package map should help the repository become easier to understand as it grows.

If a package split adds ceremony without clarifying responsibility, it is premature.

If a package split makes safety, runtime ownership, replay, or interface boundaries clearer, it is likely justified.
