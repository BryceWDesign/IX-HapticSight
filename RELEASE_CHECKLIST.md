# IX-HapticSight Release Checklist

This checklist defines the minimum release gate for the upgraded IX-HapticSight repository.

Its purpose is to prevent the repo from drifting into a polished-looking but weakly supported release.
A release should only move forward when the repository can answer, in a disciplined way:

- what changed
- what was tested
- what evidence exists
- what claims are still intentionally limited
- whether the docs, code, and benchmark artifacts still agree

This checklist is written for repository releases, not for certification or deployment approval.

---

## 1. Scope of This Checklist

This checklist applies to repository releases such as:

- tagged milestone releases
- pre-release candidates
- major architecture release cuts
- benchmark/evidence updates that materially change repo claims

It does **not** imply:
- production approval
- regulatory acceptance
- deployment readiness
- HIL evidence sufficiency
- human-subjects approval
- medical or therapeutic suitability

Those are outside the current scope of this repo.

---

## 2. Release Philosophy

A release should be blocked if any of the following are true:

- docs say one thing and code says another
- benchmarks are stale relative to runtime behavior
- the event/replay story is broken
- safety-related claims got stronger without stronger evidence
- important paths are untested
- author/license/repo identity details are inconsistent
- the README overstates maturity

The release standard is not:
“it seems fine.”

The release standard is:
- consistent
- testable
- traceable
- bounded
- honest

---

## 3. Repository Identity Checks

Before release:

- [ ] Repository name, project name, and core terminology are internally consistent.
- [ ] Author attribution is correct everywhere.
- [ ] License file and license references match the intended release posture.
- [ ] There are no stale author-name remnants or conflicting ownership strings.
- [ ] The project description does not drift into broader claims than the repo supports.

---

## 4. README and Docs Harmony Checks

Before release:

- [ ] README matches the current repository structure.
- [ ] README does not claim certification, production readiness, or validated physical deployment unless evidence truly exists.
- [ ] README non-claims match `ROADMAP.md`, `docs/governance/safety_case.md`, and related governance docs.
- [ ] `docs/index.md` accurately points to the current documentation tree.
- [ ] Benchmark docs match the current implemented benchmark modules.
- [ ] HIL docs are framed as planning/evidence-prep where appropriate, not as already-achieved proof if that proof does not yet exist.
- [ ] Safety docs still match current runtime and logging behavior.

---

## 5. Core Code Health Checks

Before release:

- [ ] The protocol core under `src/ohip/` remains importable.
- [ ] Runtime modules under `src/ohip_runtime/` remain importable.
- [ ] Logging/replay modules under `src/ohip_logging/` remain importable.
- [ ] Interface modules under `src/ohip_interfaces/` remain importable.
- [ ] Benchmark modules under `src/ohip_bench/` remain importable.
- [ ] No new circular-import breakage has been introduced.
- [ ] No release file references modules or data shapes that no longer exist.

---

## 6. Test Gate

Before release:

- [ ] All current unit tests pass locally.
- [ ] Runtime-state tests pass.
- [ ] Runtime-coordinator tests pass.
- [ ] Session-store tests pass.
- [ ] Runtime-config tests pass.
- [ ] Event/logging/replay tests pass.
- [ ] Interface-layer tests pass.
- [ ] Execution-adapter tests pass.
- [ ] Runtime-service tests pass.
- [ ] Benchmark model/runner/reporting/catalog tests pass.

Recommended release command set:
- `pytest -q`
- quickstart smoke
- benchmark catalog smoke

If a release is knowingly shipping with failing tests, that should be called out explicitly in release notes.

---

## 7. Structured Logging and Replay Gate

Before release:

- [ ] Structured event creation still works.
- [ ] JSONL event writing and reading still work.
- [ ] Replay loading and slicing still work.
- [ ] Event kinds documented in `docs/replay/event_log_schema.md` still exist in code.
- [ ] Replay and benchmark docs do not describe capabilities that are missing in code.
- [ ] Event ordering assumptions remain deterministic enough for current benchmark/replay use.

This is a core credibility gate for the repo.

---

## 8. Benchmark Gate

Before release:

- [ ] Built-in scenario catalog still loads.
- [ ] Consent-path scenarios still behave as expected.
- [ ] Safety-red scenario still behaves as expected.
- [ ] Benchmark runner still produces structured results.
- [ ] Benchmark reporting still summarizes correctly.
- [ ] Benchmark docs still match the actual current catalog and metrics.
- [ ] Any benchmark drift is either fixed or called out explicitly in release notes.

A release should not quietly ship with benchmark semantics that have changed without explanation.

---

## 9. Safety and Governance Gate

Before release:

- [ ] `docs/safety/invariants.md` still reflects current runtime architecture.
- [ ] `docs/safety/requirements_traceability.md` is not obviously stale relative to major repo behavior.
- [ ] `docs/safety/fault_handling.md` still matches current runtime fault concepts.
- [ ] `docs/safety/retreat_semantics.md` still matches current stated behavior.
- [ ] Privacy and threat-model docs still fit the current logging/replay/runtime direction.
- [ ] The safety-case doc still accurately describes the maturity level of the repo.
- [ ] Standards crosswalk language remains conservative and accurate.

If the governance layer becomes stale, the repo starts losing trust fast.

---

## 10. CI Gate

Before release:

- [ ] GitHub Actions workflow file is present and valid.
- [ ] Matrix test job reflects supported Python versions.
- [ ] Dependency install path is current.
- [ ] Quickstart smoke step is still valid.
- [ ] Benchmark catalog smoke step is still valid.

A release should not claim test automation while the workflow is obviously broken.

---

## 11. Evidence-Honesty Gate

Before release, verify the repo is not overstating evidence.

### Allowed release posture examples
- reference implementation
- runtime-oriented architecture
- structured benchmark support
- replay-capable event trail
- HIL-prep documentation
- bounded concept-stage safety architecture

### Release-blocking overstatements
- “validated physical safety” without real measured evidence
- “production ready” without real operational evidence
- “collaborative robot compliant” without true support
- “privacy-safe by design” in a way that suggests full legal sufficiency
- “hardware-proven” without actual physical artifact support

If the wording gets ahead of the evidence, stop the release and fix the wording.

---

## 12. Release Notes Gate

Before release:

- [ ] Changelog is updated.
- [ ] Release notes state what changed in code, docs, benchmarks, or interfaces.
- [ ] Release notes state what evidence was added, if any.
- [ ] Release notes preserve non-claims where needed.
- [ ] Any known limitations are still visible.

Good release notes reduce confusion.
Weak release notes create re-review work later.

---

## 13. Recommended Release Summary Format

A good release summary should include:

1. **What this release is**
   - example: runtime-and-benchmark architecture milestone

2. **What materially changed**
   - runtime service
   - structured logging
   - replay
   - interface abstractions
   - benchmark runner
   - safety/governance docs

3. **What evidence exists now**
   - unit tests
   - replayable event trails
   - built-in deterministic scenarios

4. **What still does not exist**
   - HIL data
   - real hardware validation
   - deployment approval

This is the tone the final README should inherit.

---

## 14. Release-Blocking Conditions

Do **not** cut a release if any of these are true:

- tests are failing in core paths without explicit release-note disclosure
- README overstates maturity
- docs materially contradict code
- benchmark runner or catalog is broken
- event/replay path is broken
- author/license identity is inconsistent
- core import paths are broken
- release notes are missing for material changes

---

## 15. Final Release Gate Question

Before cutting the release, ask:

> If a serious reviewer opened this repo cold, would the docs, code, tests, and benchmark story tell the same bounded and honest story?

If the answer is no, do not release yet.

---

## 16. Final Rule

The release should make the repository easier to trust, not merely nicer to look at.

If polish increases faster than evidence, the release is not ready.
