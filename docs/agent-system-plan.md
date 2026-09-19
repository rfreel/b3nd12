# Agent system implementation plan

**Goal:** Make state, evidence, next actions, and improvement trajectories usable
through one local interface without conversation history.

**Architecture:** An immutable task contract and append-only journal feed a
deterministic projection. Verification binds command results to source hashes;
benchmarks measure the operator surface separately from research outcomes.

**Stack:** Python 3.12 standard library, POSIX file locking, Git, Bun 1.2.22,
and the existing pinned Bend overlay.

**Spec:** `docs/agent-system-design.md`.

Execution is native in this session, in dependency order. The user delegated
design, implementation, and GitHub publication. A fresh completion review checks
the combined result against this plan. Future agents start with `control.py next`.

## Global constraints

- Preserve the Bend checker and existing laws.
- Add no paid service, scheduled worker, or model dependency.
- Never collapse missing evidence into success.
- Keep the architecture, atomic roadmap, and benchmark registry in Git.
- Preserve the first proof campaign, including its failed runner attempt.

## Review focus

- Duplicate retries and stale concurrent writers: one event or a conflict.
- Torn journals, malformed JSON, and plan drift: reject without repair-by-deletion.
- Path escapes, changed source, and missing evidence: fail closed.
- Dependency reopening: dependent completion becomes stale.
- Timeout and child processes: terminate the process group and retain failure.

## Implementation slices

### A01: Contracts and graph validation

Files: `tools/agent_system/contracts.py`, `system/roadmap.json`,
`tests/test_agent_contracts.py`.

Interface: `load_plan(root) -> dict`, `safe_path(root, relative) -> Path`,
`digest(value) -> str`, and `Problem(code, message)`.

- [x] Reject unsupported versions, duplicate IDs, missing dependencies, cycles,
  invalid statuses, nonpositive budgets, and paths outside the repository.
- [x] Validate that each task has a source scope, acceptance description,
  reopen trigger, and a bounded argv verification command.
- [x] Demonstrate negative cases before admitting the real roadmap.

### A03: Journal and evidence-aware projection

Files: `tools/agent_system/state.py`, `tests/test_agent_state.py`.

Interface: `read_events(path, plan) -> list`, `project(root, plan, events) -> dict`,
`append(root, plan, path, payload, request, head) -> dict`.

- [x] Hash every event and bind it to the frozen plan.
- [x] Lock, replay, compare head, append, flush, and fsync in that order.
- [x] Test identical retries, conflicting retries, stale heads, torn tails,
  tampering, and two writers starting from the same head.
- [x] Require passing fresh evidence for SOLVED; derive STALE without editing history.
- [x] Propagate dependency invalidation and select the next action deterministically.

### A02: Bounded verification

Files: `tools/agent_system/evidence.py`, `tests/test_agent_evidence.py`.

Interface: `verify(root, task, run_id) -> dict`, `fresh(root, task, ref) -> bool`.

- [x] Bind task specification and declared source files to evidence.
- [x] Execute argv directly in the repository with timeout and process-group cleanup.
- [x] Record raw stdout, stderr, exit code, duration, interpreter, and source drift.
- [x] Use exclusive run IDs and reject reused or escaping output locations.
- [x] Test pass, failure, timeout, missing files, changed files, and changed evidence.

### A04: Agent command surface

Files: `control.py`, `tools/agent_system/cli.py`, `tests/test_agent_cli.py`,
`AGENTS.md`, `START_HERE.md`.

- [x] Add status, next, explain, doctor, transition, verify, check, todo, and benchmark.
- [x] Give every response a version, success flag, result or stable error code.
- [x] Keep read commands free of filesystem writes and subprocess execution,
  except doctor, whose probes are explicit in its command contract.
- [x] Return exact task IDs, minimal context files, commands, and reopen conditions.
- [x] Correct the obsolete instruction to execute review-only patch files.

### A05: Benchmark contracts and measured baseline

Files: `system/metrics.json`, `tools/agent_system/benchmarks.py`,
`tests/test_agent_benchmarks.py`, `docs/benchmarks.md`.

- [x] Define units, direction, scope, collection, near-term and long-term targets.
- [x] Measure replay, selection, packet size, cold startup, and integrity rejection.
- [x] Record metric/suite/source/environment identities and explicit nulls for
  unmeasured model metrics.
- [x] Test deterministic measurements, malformed history rejection, and metric coverage.
- [x] Retain raw baseline; do not infer agent productivity from local microbenchmarks.

### A06: Integration and trajectory

Files: `.github/workflows/agent-system.yml`, `system/lessons.json`,
`docs/agent-roadmap.md`, `README.md`, `state/events.jsonl`.

- [x] Run all control tests and the existing Bend pilot after integration.
- [x] Verify each delivered task and record its completion through the public CLI.
- [x] Generate the current TODO view from the journal.
- [x] Publish the branch and pull request with the unimplemented gates named.
- [x] Inspect GitHub checks and resolve failures caused by this change.

## Atomic future work

`system/roadmap.json` is the executable dependency graph. `docs/agent-roadmap.md`
expands each future task into files, probes, admission gates, and a stopping rule.
Future work is OPEN, BLOCKED, or UNRESOLVED until its own evidence closes it.
Do not mark it complete because a plan, schema, or plausible design exists.
