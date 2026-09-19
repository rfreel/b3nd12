# Supermodularity pilot

Target: rfreel/b3nd12, pinned Bend 2.0.9 overlay. The earlier abstract System sketch is not implementation evidence.

## Completion checklist

- [x] Identify repository, inspect instructions, and preserve the checker boundary.
- [x] Assign six independent workers with exclusive write ownership; coordinator integrates.
- [x] Establish pinned upstream and executable Bend runtime.
- [x] Implement a concrete Bend repair model, laws, and checked proofs.
- [x] Demonstrate accepted repair, rejected broken repair, rejected evidence loss, and unresolved preservation.
- [x] Implement strict external repair evidence validation without mutating input records.
- [x] Implement exact four-configuration interaction calculation with comparable evaluation metadata.
- [x] Run a reproducible experiment using existing overlay capabilities; retain zero or negative interaction honestly.
- [x] Add local and CI verification against the upstream pin, including negative checks.
- [x] Review integrated changes for vacuous predicates, bypasses, scope drift, and provenance gaps.
- [x] Run fresh integrated verification and record commands, outcomes, and limits.
- [x] Update the repository ledger and documentation with only demonstrated results.
- [x] Produce the next improvement list from measured gaps, with acceptance tests and reopen conditions; do not automatically execute adjacent work.

## Acceptance criteria

The proof pilot must use executable definitions and admit at least one valid repair. Invalid target repair, regression, and evidence loss must not be accepted. External reports must retain unresolved results and reject incomparable evaluations. The interaction calculation uses one fixed higher-is-better metric and exact arithmetic. The four configurations must come from reproducible work, not invented scores. No modification to bend2/bend.ts is permitted.

Formal proofs establish properties of the finite model. Report validation checks supplied evidence consistency. Neither establishes the truth of external measurements. No positive interaction claim is required for completion.

## Dependency order and ownership

1. Coordinator: repository identity, upstream/runtime, checklist, final integration and verification.
2. Contracts worker: pilot/supermodularity/ model, laws, proofs, and proof rejection fixtures.
3. Admission worker: tools/repair_gate.py and tests/test_repair_gate.py.
4. Interaction worker: tools/interaction.py, tests/test_interaction.py, experiments/.
5. CI worker: scripts/verify-supermodularity.sh and workflow.
6. Review worker: read-only independent challenge of actual changes.
7. Documentation worker: docs/supermodularity.md.

Workers inspect independently; shared API changes and final integration are serialized. Completion requires coordinator-run verification of the combined tree.

## Observed result

`./scripts/verify-supermodularity.sh /path/to/patched-bend-checkout` returned 0.
Eight Bend laws checked with zero unsafe terms. Two false proofs were rejected.
A proof with one transitive unsafe dependency was rejected by the safety gate.
All 17 Python tests passed without skips. The real staged-checker bypass was
reproduced and repaired: target FAIL to PASS, with both baseline passes retained.
The report gate accepted that repair. Diagnostic scores were 1, 1, 1, 1, giving
interaction 0. The independent reviewer reproduced the integrated result.

Evidence: experiments/checker_repair.results.json and
experiments/diagnostic_interaction.results.json. Next candidates and reopening
conditions: docs/supermodularity-next.md. Hosting merge policy remains open.
