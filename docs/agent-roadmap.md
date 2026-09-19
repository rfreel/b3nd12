# Long-term implementation map

Current state comes from `python3 control.py todo`. The task contract lives in
`system/roadmap.json`; it contains exact dependencies, files, checks, acceptance
criteria, estimated effort, and reopen conditions. This document expands the
future work into small actions. It does not duplicate mutable completion status.

Foundation tasks A01 through A06 build contracts, evidence, journal, command
surface, benchmarks, and integration. Their file-level checklist is in
`docs/agent-system-plan.md`. The following work is ordered by dependencies,
not by an assumption that every feature should be built immediately.

Each B task owns `tools/agent_system/<name>.py` and
`tests/test_agent_<name>.py`, where `<name>` is stated below. The task's declared
test command is its first admission check. Add real integration evidence before
claiming infrastructure guarantees. Estimates in the roadmap are prioritization
hints, not promises that a multi-host or longitudinal study takes an hour.

## B01: Version migration and crash recovery (`migration`)

- Preserve the source plan, destination plan, source head, and migration reason.
- Permit added tasks and explicit replacements; reject silent edits to the
  meaning of a previously completed task.
- Map old IDs to retained or superseded IDs. Give changed acceptance criteria
  new unsolved tasks rather than inheriting prior completion.
- Inject interruption before write, during write, after flush, and after fsync.
- Recover only from a separately retained verified prefix and save the damaged
  bytes. Require a new recovery event; never truncate silently.
- Stop when replay before and after approved migration agrees for unchanged
  tasks and all interruption probes have classified outcomes.

## B02: Campaign adapter (`campaign_adapter`)

- Define a candidate manifest with hypothesis, objective, editable files,
  evaluation identity, and budget before execution.
- Adapt the existing proof campaign's raw records to the common evidence format.
- Bind baseline, candidate, laws, evaluator, compiler, and environment hashes.
- Preserve aborted runs with a terminal failure record, not only a traceback.
- Enforce an explicit consecutive-failure cap and remaining-time budget.
- Reject a missing pair, missing raw diagnostic, changed evaluator, or invented
  hypothesis. Stop after a real campaign passes the adapter and mutation probes.

## B03: Scoped lesson retrieval (`lessons`)

- Require failure, reproducer, evidence digest, scope, guard, and reopen trigger.
- Index by affected operation and failure class; return a bounded result set.
- Include the counterexample that limits each lesson's application.
- Test an applicable case, an unrelated case, stale evidence, and a narrowed scope.
- Count actual useful reuse before promoting a local lesson to policy.
- Stop at deterministic retrieval until five lessons justify more complex ranking.

## B04: Environment identity (`environment`)

- Record compiler commit, runtime version, backend, OS, CPU/GPU, resource limits,
  environment variables that affect execution, and suite digest.
- Separate correctness compatibility from performance comparability.
- Define which differences force a new baseline; expose the differing fields.
- Reproduce one accepted result in a clean compatible environment.
- Reject comparisons after changing compiler, backend, or timing hardware.
- Stop when comparisons have an explicit compatible/incompatible explanation.

## B05: Performance evidence (`performance`)

- Declare primary metric, hard constraints, minimum effect, and sample budget.
- Alternate baseline and candidate runs; retain warmup and measured phases.
- Compute paired differences and an interval; preserve raw measurements.
- Measure peak memory separately from wall time and proof-check time.
- Reject noisy gains and correct-but-over-budget candidates; retain trade-offs.
- Stop when one real claimed gain is either independently repeated or classified
  inconclusive under the predeclared rule.

## B06: Diverse held-out tasks (`holdout`)

- Assemble 100 tasks spanning parsing, imports, equality direction, induction,
  affine use, recursion, effects, evidence integrity, scheduling, and recovery.
- Give every task an oracle, allowed actions, failure examples, and budget.
- Split development and final holdout by family where possible to reduce leakage.
- Freeze manifests and seed assignments before trying agents.
- Verify the oracle accepts at least one witness and rejects known wrong answers.
- Stop at a versioned corpus with no missing oracle or accidental duplicate.

## B07: Agent usability study (`agent_trials`)

- Check provider access and declare total dollar, token, time, and call ceilings.
- Select 30 tasks and three independent repeats; preserve model and prompt identity.
- Pair the old workflow and new control interface under equal budgets.
- Record first action, success, tokens, tool calls, spend, interventions, and failures.
- Keep final holdout results out of search-time feedback.
- Stop at the budget or completed matrix; publish confidence and missing cells.
  Do not synthesize agent outcomes from local unit tests.

## B08: Verified cache (`cache`)

- Key entries by source, dependencies, evaluator, laws, objective, and environment.
- Store the original evidence object and its freshness conditions.
- Reuse correctness results only where the contract permits; do not reuse timing
  measurements as if a new performance experiment ran.
- Mutate every key component individually and require a miss.
- Measure hit rate, lookup cost, and avoided verification cost on real repetition.
- Stop if lookup and invalidation cost outweigh the saved work.

## B09: Worker isolation (`isolation`)

- Create a distinct unprivileged process identity and private candidate directory.
- Expose only candidate submission and bounded diagnostic feedback.
- Mount evaluator, laws, controller, and evidence storage outside worker write access.
- Deny worker access to credentials and signing material.
- Probe filesystem escapes, inherited descriptors, process exhaustion, output
  floods, and attempts to fabricate accepted results.
- Stop before unattended use unless the actual host rejects every declared escape.

## B10: Cross-clone leases (`leases`)

- Specify owner, task, epoch, expiration, and fencing token.
- Use a transactional shared backend only after multiple clones require it.
- Admit exactly one claimant and reject effects from an expired owner.
- Reconcile worker death without treating missing results as success.
- Test overlapping claims, delayed writes, clock disagreement, and restart.
- Stop after a real two-worker failure drill preserves a single accepted history.

## B11: Independent attestation (`attestation`)

- Keep signing material in the verifier's authority domain.
- Sign task, source, evaluator, environment, result, and artifact identities.
- Verify before acceptance and retain signer/key version.
- Reject altered artifacts, forged signatures, and replay against another task.
- Define revocation and rotation without rewriting historical evidence.
- Stop after a worker cannot mint evidence that the independent verifier accepts.

## B12: Host merge policy (`host_gates`)

- Read current GitHub rules and identify exact required check names.
- Select authorized law reviewers and define exception handling explicitly.
- Configure rules only with the necessary repository authority.
- Demonstrate that a failing check prevents merge and a law change follows review.
- Retain host responses and rule identity, not screenshots of a green workflow.
- Stop if host access cannot establish the required policy; report the boundary.

## B13: Variable-suite laws (`generalized_laws`)

- Define a regression case list and an acceptance predicate over every retained case.
- Prove accepted repairs preserve the previous passing cases.
- Prove evidence retention without assuming a fixed two-case Boolean universe.
- Retain a valid repair witness, a deletion counterexample, and a regression case.
- Run the compiler and independent execution checks without changing its kernel.
- Stop when the actual consumer's suite is covered; do not generalize unused domains.

## B14: Measured scheduling (`scheduling`)

- Collect observed task cost, successful discrimination, and verified downstream gain.
- Keep the current static ordering as the comparison policy.
- Declare a bounded exploration allowance; avoid fabricated expected-value precision.
- Evaluate on task sequences withheld from policy fitting.
- Count exploration overhead and failures in total cost.
- Stop unless equal-budget improvement reproduces without worse integrity outcomes.

## B15: Lesson transfer (`transfer`)

- Select ten independently reproduced lessons and disjoint task families.
- Pair with-lesson and without-lesson trials at equal context and compute budgets.
- Include explicit out-of-scope cases that could be harmed by each lesson.
- Measure positive transfer, negative transfer, and uncertainty.
- Narrow or retire lessons that hurt a new family; retain the limiting counterexample.
- Stop after reporting the full matrix, including null and negative results.

## B16: Platform behavior (`portability`)

- Run identical persistence and process tests on Linux and macOS.
- Exercise file locks, interrupted writes, source-path resolution, and child cleanup.
- Compare filesystem durability assumptions and document unsupported operations.
- Validate WSL separately if Windows use is needed; do not claim native support.
- Preserve platform-specific failures as gated capability results.
- Stop after both supported hosts reproduce the same accepted transition semantics.

## B17: History compaction (`compaction`)

- Benchmark 10000 events before adding a snapshot mechanism.
- Anchor a snapshot to the source plan and exact journal prefix digest.
- Replay the suffix and compare the entire projection with full replay.
- Reject altered anchors, reordered suffixes, and missing prefix provenance.
- Keep a full audit path and explicit migration between snapshot versions.
- Stop unless measured replay cost justifies the extra representation.

## B18: Supervised search (`supervision`)

- Give the supervisor immutable observations and explicit search-policy knobs.
- Permit changes only between campaigns; freeze each active evaluator and objective.
- Keep worker, supervisor, checker, and signing authority separate.
- Compare static search, worker-only adaptation, and supervisor adaptation at equal
  total budget, including supervisor tokens and failed suggestions.
- Preserve unresolved hypotheses and their cheapest discriminating probes.
- Stop unless the additional supervision produces independently repeated benefit.

## B19: Trajectory reporting (`trajectory`)

- Ingest complete run records with cohort identities and actual costs.
- Compute comparable 30-day and 90-day windows with denominators and uncertainty.
- Track repeated failure classes, independent gains, rollbacks, intervention cost,
  cache reuse, and lesson transfer without hiding missing cells.
- Link each aggregate to its source runs; quarantine incompatible environments.
- Trigger review on integrity regression or rising cost with flat verified gain.
- Stop at an auditable report; do not add a dashboard until someone needs it.

## B20: Continuation and stopping (`stopping`)

- Preserve fixed-budget campaigns as the baseline policy.
- Fit stopping candidates on past development runs with complete attempt costs.
- Evaluate held-out campaigns for saved cost and missed useful improvements.
- Bound forced exploration to avoid declaring a plateau from repeated local moves.
- Keep unresolved alternatives and explicit reopen triggers when a run stops.
- Stop when the policy has demonstrated benefit at equal tolerated missed-gain risk.

## Review cadence

After each delivered slice, run its acceptance check and the smallest affected
integration check. After a real trial cohort, revisit priorities using measured
cost and value. Change the frozen contract only through B01's migration once it
exists. Until then, propose the new contract as a separate reviewed version.
The system should grow only where the current evidence identifies friction.
