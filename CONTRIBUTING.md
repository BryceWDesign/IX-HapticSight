# Contributing to IX-HapticSight

Thank you for contributing to IX-HapticSight.

This project is being developed as a safety-first, audit-friendly optical-haptic interaction architecture. Contributions are welcome, but they must preserve the project's core design goals:

- bounded physical behavior
- explicit consent semantics
- deterministic safety overrides
- measurable contact limits
- traceable changes
- clear non-claims

## Contribution Principles

All contributions should follow these rules:

1. **Safety before capability**
   - Do not add convenience features that weaken safety constraints.
   - Do not bypass hazard, consent, force, or retreat logic.

2. **No silent behavioral drift**
   - Any change that affects approach, contact, retreat, or override behavior must be documented.
   - New defaults must be justified.

3. **Determinism over ambiguity**
   - Core safety and policy decisions must remain inspectable and reproducible.
   - Learned or probabilistic components must not directly control hard safety envelopes.

4. **Traceability**
   - Changes must be linked to a requirement, invariant, benchmark, test, or risk item.
   - Safety-relevant code should not be merged without corresponding tests.

5. **Measured language**
   - Do not describe the project as certified, medically validated, production safe, or deployment ready unless that status is explicitly supported by evidence.
   - Avoid unsupported claims about emotion recognition, user intent certainty, or social appropriateness.

## Scope of Acceptable Contributions

Examples of acceptable contributions include:

- runtime architecture improvements
- benchmark harnesses
- simulation scenarios
- ROS 2 node scaffolding
- state machine validation
- replay and logging tools
- safety-case traceability artifacts
- standards crosswalk documentation
- tactile, force-torque, proximity, and thermal interface abstractions
- test fixtures and deterministic fault-injection tooling

Examples of contributions that require extra scrutiny:

- changes to force limits
- caregiver or override behavior
- human-state interpretation logic
- data retention or privacy behavior
- motion execution envelopes
- emergency stop or retreat semantics
- autonomous contact initiation logic

## Pull Request Expectations

Each pull request should include, where applicable:

- a concise statement of purpose
- affected modules and files
- risk summary
- test coverage summary
- any changed assumptions
- any new invariants or benchmark criteria
- documentation updates for externally visible behavior

## Code Style Expectations

- Prefer small, reviewable changes.
- Prefer explicit data structures and typed interfaces where practical.
- Avoid hidden globals and implicit state.
- Keep safety decisions readable and easy to audit.
- Use descriptive names over clever shortcuts.
- Separate policy logic from transport or runtime plumbing.

## Documentation Expectations

Contributors should update documentation whenever they change:

- state transitions
- safety thresholds
- consent semantics
- benchmark behavior
- logging schema
- configuration meaning
- deployment assumptions

## Testing Expectations

At minimum, safety-relevant changes should include one or more of:

- unit tests
- state-transition tests
- invariant tests
- integration tests
- replay tests
- fault-injection tests
- benchmark scenario updates

If a change cannot be tested yet, the limitation must be stated explicitly in the pull request notes.

## Security and Responsible Reporting

If you discover a vulnerability, unsafe failure mode, or privacy issue:

- do not publish exploit details in a public issue first
- provide a clear reproduction description
- identify affected modules and likely impact
- suggest containment or rollback steps if known

## Licensing and Attribution

Contributors must preserve project attribution and comply with the repository license and associated usage terms that are present in the repository at the time of contribution.

## Final Review Standard

The standard for merging is not "works on my machine."

The standard is:

- understandable
- testable
- bounded
- reviewable
- consistent with the project safety model
