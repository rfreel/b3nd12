# Backlog implementation receipts

The immutable proposal is `TODO_100.md`, digest
`029cce7396b70398091b6d6238a310ca5ab3922ca07aeaec4acc9fa4f5524f6d`.
Its unchecked boxes preserve the original proposal. This separate ledger records
implementation and verification; it does not activate a new Bend contract.

## Status and acceptance boundary

`DONE` identifies work with recorded local acceptance and independent review.
The publication record supplies its exact source revision. `REVIEW` identifies
implementation still awaiting a required acceptance result.
`OPEN` identifies unfinished local work, including designs that need review.
`BLOCKED` identifies a missing authority, dependency or execution capability. None of the
last three statuses is a completion receipt.

The table covers all 100 proposal IDs. The proposal's C and X prerequisites remain
binding. User authorization to continue work does not establish an approved
runtime digest, isolated execution principal, experimental contract or hardware.
No task is completed merely because related infrastructure now exists.

## Previously accepted implementation group

| Task | Source revision | Recorded local acceptance | Remaining limit |
|---|---|---|---|
| T001 | [8e9d0cb](https://github.com/rfreel/b3nd12/commit/8e9d0cb964baca310fc910b080a8ad11c4d4f978) | Mode drift on theory and untouched upstream files refused with `core.filemode=false`; restored baseline passes | Exclusive checkout access; staged non-theory policy is separate |
| T005 | [e341288](https://github.com/rfreel/b3nd12/commit/e34128890a7c2b42a86eb782e961eb1ee05ffc86) | Repository-contained output paths and symlink aliases refused before writes; external replay passes | Cooperative filesystem access |
| T041 | [15f83d1](https://github.com/rfreel/b3nd12/commit/15f83d15070b3e2c31eccb92656a64107de55bb4) | Global help before/after commands preserves literal operands and target state | Format conflicts remain errors |
| T081 | [a547a58](https://github.com/rfreel/b3nd12/commit/a547a58bbb3b0b5322225117125a83ea65460e2c) | Five suites ran locally; workflow failure injection stopped later suites; [hosted run 35426650861](https://github.com/rfreel/b3nd12/actions/runs/35426650861) succeeded at the published first-group head `f4c930a` | This hosted result does not cover the expanded working-tree lane |

Four implementation workers owned separate source/test areas. Two review
assignments examined their diffs. The coordinator ran the five original suites,
backlog and CI contract tests, compilation checks, and `git diff --check` before
publishing those commits. This historical evidence does not cover the subsequent
working-tree changes. Workers and reviewers share filesystem authority.

## Complete disposition

| Task | Status | Evidence or next required discriminator |
|---|---|---|
| T001 | DONE | Previously accepted upstream mode checks; rerun with current installation changes. |
| T002 | DONE | Checker observations distinguish exact law refusal from crash, timeout, spawn failure and missing certificate; `tests/checker_failures.py`. |
| T003 | BLOCKED | No independently approved runtime digest and trust source; operational probes cannot supply approval. |
| T004 | OPEN | Design and review immutable compiler snapshot execution; source validation still assumes cooperative files. |
| T005 | DONE | Previously accepted physical output boundary; concurrent path replacement remains outside the guarantee. |
| T006 | OPEN | Shared helper and caller guards pass cooperative descendant-cleanup tests; cleanup is depth-limited and the benchmark has a separate runner, so universal coverage is unproved. |
| T007 | OPEN | Design and review whole-run elapsed-time and memory policy; per-process bounds do not satisfy this task. |
| T008 | DONE | Independent evidence verifier reconstructs finite decisions and rejects changed chains against retained digests; `tests/evidence.py`. |
| T009 | DONE | Baseline ledger event binds the manifest and its source/input/tool identities; verifier mutation tests. |
| T010 | DONE | `tests/routing_domain.py` enumerates the finite routing domain with independent expectations and real checker calls. |
| T011 | DONE | Atomic evidence publication and terminal ledger commit point; `tests/storage.py` exercises process-kill boundaries. |
| T012 | DONE | Failed checker observations retain command, stage, output and termination classification; failure fixtures cannot earn proof credit. |
| T013 | BLOCKED | Resume requires accepted whole-run budgeting and prefix recovery; current replay refuses existing output directories. |
| T014 | DONE | Accepted books can be reconstructed and rechecked from verified packets; `tests/recheck.py`. |
| T015 | DONE | Independent reconstruction derives summary and detects a conflicting saved summary; `tests/evidence.py`. |
| T016 | DONE | Verified archive round trip and hostile-member rejection; `tests/archive.py`; directory publication is not crash-atomic. |
| T017 | OPEN | Design and review evidence migration policy; old incompatible packets are refused, not migrated. |
| T018 | DONE | Candidate, artifact, subprocess and archive bounds pass; non-UTF8 noisy output produces durable truncated UNKNOWN evidence within storage limits. |
| T019 | DONE | Disk-full, permissions, short writes, fsync and rename failures exercised by `tests/storage.py`; no physical power-loss claim. |
| T020 | BLOCKED | No external authenticated terminal-receipt store or trust channel has been established. |
| T021 | BLOCKED | Workers and controller share an execution principal; operating-system isolation has not been established. |
| T022 | BLOCKED | Depends on T021 and a reviewed controller-only promotion policy. |
| T023 | BLOCKED | Depends on T022; concurrent promotion semantics and atomic authority boundary are unreviewed. |
| T024 | BLOCKED | Depends on T023 and authenticated submission identities. |
| T025 | BLOCKED | Depends on T021 and an enforced worker filesystem view. |
| T026 | BLOCKED | No reviewed worker capability policy or independently enforced network/environment boundary. |
| T027 | BLOCKED | Depends on T024; no authenticated lease/reassignment service exists. |
| T028 | OPEN | Design and review general worker queue capacity and admission semantics. |
| T029 | OPEN | Child-process cleanup is implemented; distributed worker cancellation and durable cancellation semantics still need a reviewed design. |
| T030 | BLOCKED | Depends on T021/T022; proposal-only behavior does not authenticate contract activation authority. |
| T031 | DONE | Explicit 25-file manifest replaces scope discovery; manifest/mode/role mutation fixtures. |
| T032 | OPEN | Review staged non-theory verification policy; existing installation preserves a clean real index. |
| T033 | OPEN | Review rollback policy; post-write failure intentionally leaves the target for diagnosis. |
| T034 | OPEN | Design lock ownership and recovery; exclusive access remains an assumption. |
| T035 | DONE | Preflight and installation consume the same temporary patch copies; source mutation fixture confirms installed identity. |
| T036 | DONE | Filesystem obstruction fixtures preserve ignored collisions, symlink parents and inaccessible paths. |
| T037 | DONE | Explicit Git environment/configuration/filter matrix and linked-worktree checks; not an audit of every Git feature. |
| T038 | DONE | Binary, path, rank, symlink, deletion and scope mutation controls in installation suites. |
| T039 | DONE | Installation receipts bind inputs and tool identities and replay into independent clones; `tests/install_receipt.py`. |
| T040 | OPEN | Shell static/runtime reporting and smoke tests exist; confirm hung-runtime behavior and consistent machine-readable runtime status before completion. |
| T041 | DONE | Previously accepted global-help behavior; current CLI suites rerun its contract. |
| T042 | DONE | Strict command-specific success schemas validate existing outputs and reject malformed results. |
| T043 | DONE | Full Draft 2020-12 validation replaces key-only assertions; malformed payload controls in `tests/cli_schema.py`. |
| T044 | DONE | 102 generated parser cases; semantic command arrays replay with an inserted `--`, not as raw argv. |
| T045 | DONE | Every declared Failure code has format-parity coverage; some causes are injected rather than reproduced as real outages. |
| T046 | DONE | Every read-only command and representative errors run through real PTYs, pipes and explicit format overrides. |
| T047 | OPEN | Review bootstrap/import failure output policy; the normal envelope begins after imports succeed. |
| T048 | DONE | Invalid user tasks remain exit 2; malformed routes and wrong content produce configuration errors, exit 3. |
| T049 | DONE | File/mode/Git-control and copied-management snapshots remain unchanged across read-only success/failure calls. |
| T050 | DONE | Unicode, trailing newline, leading-dash, symlink and non-root path tests; newline root parsing repaired. |
| T051 | DONE | Independent disposable books falsify each acceptance-law conjunct; `tests/law_conjuncts.py`. |
| T052 | DONE | Evidence translation mutations and declared surviving cases are reported by `tests/translation.py`. |
| T053 | DONE | Frozen spec-twin hashes/write set challenged while legal sum/proof edits pass; `tests/spec_twin.py`. |
| T054 | OPEN | Review transitive import parsing and authorization policy; lexical checks are not that policy. |
| T055 | OPEN | Review the statement of a separate TODO-accounting Bend book; routing law remains unchanged. |
| T056 | DONE | Independent model and real frozen controller agree on 1,213 reachable prefix/terminal traces and 910 terminal branches; checker outcomes are controlled inputs. |
| T057 | BLOCKED | Pinned native compiler/toolchain execution evidence is absent. |
| T058 | BLOCKED | Complete interpreted/JavaScript/native corpus comparison depends on the native lane. |
| T059 | BLOCKED | Matching GPU hardware/backend and pinned execution evidence are unavailable. |
| T060 | OPEN | No tested backend counterexample minimizer with retained regression fixture has been delivered. |
| T061 | DONE | Versioned management benchmark records commands, identities, raw timings and resource observations; benchmark contract test. |
| T062 | OPEN | Design timing-noise controls and review the exclusion policy before measuring candidates. |
| T063 | OPEN | Review representative CPU/allocation/I/O profiling; timings alone do not establish hotspots. |
| T064 | BLOCKED | Git batching change depends on profiling, equivalence oracle and controlled comparison policy. |
| T065 | BLOCKED | Metadata reuse depends on measured justification and a reviewed experiment. |
| T066 | OPEN | Define a large-input workload and review memory/latency comparison before testing streaming. |
| T067 | OPEN | Review cold/warm population definitions and cache treatment. |
| T068 | OPEN | Define fixed resource budgets and review the worker-count sweep before a saturation study. |
| T069 | BLOCKED | Depends on accepted T062 controls and measured false-alarm rates. |
| T070 | OPEN | Review whole-task cost accounting and outcome surfaces before a study. |
| T071 | OPEN | Define and review representative fresh-agent tasks and protected outcome oracles. |
| T072 | BLOCKED | No enforced held-out answer boundary or exposure ledger. |
| T073 | OPEN | Design the strongest-control comparison under the new study contract; constructed routing gains are not agent productivity evidence. |
| T074 | BLOCKED | Depends on T071–T073 and verified fresh-worker identities/cost telemetry. |
| T075 | BLOCKED | History-free worker access, handoff oracle and study contract remain unestablished. |
| T076 | BLOCKED | Equal-budget serial/six-worker trial requires hidden defects, cost telemetry and a reviewed study. |
| T077 | BLOCKED | Isolated contexts and hidden-defect experiment with joint-miss uncertainty are unavailable. |
| T078 | OPEN | Design and review the planted reviewer-challenge corpus and scoring rules. |
| T079 | BLOCKED | Repository-injection study and enforced protected-state boundary require review. |
| T080 | BLOCKED | Complete provider-reconciled worker/tool/retry usage telemetry is unavailable. |
| T081 | DONE | Original lane passed locally and in hosted run 35426650861; expanded lane still needs its own hosted result. |
| T082 | BLOCKED | Immutable runner/toolchain identity policy and reproduction on two clean workers remain unestablished. |
| T083 | BLOCKED | No macOS execution evidence; Linux-only results cannot establish cross-platform conformance. |
| T084 | DONE | Independent `--no-local` clone has no alternates and installs without origin access; installation adversarial suite. |
| T085 | OPEN | Documentation commands have focused tests, but no complete declared-example inventory and clean-checkout runner. |
| T086 | DONE | Bounded operational probes distinguish unusable tools; deliberate spoofing and native/GPU readiness remain outside their scope. |
| T087 | OPEN | No complete bounded failure-artifact publication lane with source/command binding and redaction tests. |
| T088 | BLOCKED | Download provenance approval and trust source are not established by observed executable hashes. |
| T089 | OPEN | No prepared acceptance run under enforced network denial has demonstrated independence from provider calls. |
| T090 | OPEN | Several suites contain planted mutations; a complete cross-suite catalog with surviving-mutation accounting remains unfinished. |
| T091 | OPEN | Design and review general typed task receipts and task/source binding. |
| T092 | OPEN | Review general dependency admission and impossible-budget rules. |
| T093 | OPEN | Review cross-task benefit attribution; existing duplicate completion checks cover only the frozen replay. |
| T094 | OPEN | Review scheduler reopen conditions and changed-evidence admission. |
| T095 | OPEN | Review evidence-driven reranking against fixed objectives; backlog order is not an adaptive scheduler. |
| T096 | OPEN | Review a general protected-capability corpus and advancement policy; current suites cover declared local paths. |
| T097 | BLOCKED | Depends on T021 and authenticated distinct author/reviewer identities. |
| T098 | OPEN | Review accepted-improvement rollback and reversed-benefit accounting. |
| T099 | OPEN | Operating documentation has been updated, but a complete stale-claim/example detection oracle remains unfinished. |
| T100 | BLOCKED | T001–T099 lack accepted completion receipts; no successor list may be treated as complete or activated. |

## Current focused evidence

The checks below map implemented behavior to its executable evidence. The
coordinator's final 24-suite rerun passed after the subprocess repair, and
independent reviewers accepted the completed changes with the stated limits.
See [ACCEPTANCE_RUN.md](ACCEPTANCE_RUN.md) for commands and results. Install
`requirements-test.txt` into the test interpreter and put Bun on PATH for
installed CLI smoke coverage.

| Area | Checks | Interpretation limits |
|---|---|---|
| Process control | `tests/process.py`, `tests/checker_failures.py`, `tests/output_bounds.py` | Actual descendant/noisy-child tests plus controlled failure injection; no separate security principal. |
| Evidence | `tests/evidence.py`, `tests/archive.py`, `tests/recheck.py` | Retained-digest consistency and accepted-book rechecking; no authenticated external root or runtime approval. |
| Durability | `tests/storage.py`, `tests/program.py` | Process interruption and syscall failures; no physical power-loss or resume guarantee. |
| Installation | `tests/patch_stack.py`, `tests/install_adversarial.py`, `tests/install_receipt.py` | Cooperative source and exclusive checkout; no transactional rollback. |
| CLI | `tests/cli_schema.py`, `tests/cli.py`, `tests/cli_properties.py` | Full schema, 102 parser cases, actual PTYs and snapshots; synthetic error origins are labeled. |
| Proof | `tests/routing_domain.py`, `tests/law_conjuncts.py`, `tests/translation.py`, `tests/spec_twin.py` | Finite routing law and official frozen example; no native/GPU or general productivity result. |
| Controller model | `tests/controller_model.py` | Complete reachable six-attempt four-outcome tree, pruned at the third productive result or first UNKNOWN; controlled checker with real controller/storage. |
| Measurement | `tests/benchmark_contract.py` | Reproducible measurement entry point; no optimization or statistically established speedup claim. |
| Runtime smoke | `tests/smoke.py` | Static success remains visible with missing or failed Bun; T040's full acceptance remains open. |

## Combined acceptance and publication

The final 24-suite integrated rerun passed after repair of the nested subprocess
termination race. The general T006 obligation remains open because the helper's
cooperative, depth-limited cleanup and separate benchmark runner do not establish
universal child-process coverage. The separate final controller-model run passed
all 1,213 reachable prefix/terminal traces and 910 terminal branches in 127.82
seconds. No REVIEW rows remain. Totals are 36 DONE, 35 OPEN and 29 BLOCKED.

The [acceptance run](ACCEPTANCE_RUN.md) records integrated checks and review
findings. These coherent commits identify the tested implementation. Together
they contain the current acceptance surface; testing was performed on their
combined source, not separately on every intermediate commit.

| Source group | Commit | Accepted task coverage |
|---|---|---|
| Cooperative process bounds | [7947219](https://github.com/rfreel/b3nd12/commit/7947219e51f5a6829f6eecea361b9aae5c020622) | Supports later tasks; T006 remains open |
| Evidence, durability and proof checks | [2090bff](https://github.com/rfreel/b3nd12/commit/2090bffa1faf49779e3093ba41c0b95614ca9530) | T002, T008–T012, T014–T016, T018–T019, T051–T053, T056 |
| Sealed installation and replay | [cb17251](https://github.com/rfreel/b3nd12/commit/cb17251affa1b83490893c30dd867389c11d582e) | T031, T035–T039, T084; partial T040 |
| CLI contracts and readiness | [fa8569d](https://github.com/rfreel/b3nd12/commit/fa8569d143ed98f9600be0d07ad05154d8d2c726) | T042–T046, T048–T050, T086 |
| Reproducible management benchmark | [14e99c8](https://github.com/rfreel/b3nd12/commit/14e99c861efd829107e9696d1366f1b3d5f4dad2) | T061 |

The branch is `improve/verified-stack-and-cli`. The final publication report
records the branch-head identity and push result. Unfinished criteria retain
their OPEN or BLOCKED status; supporting infrastructure does not count as their
completion.

The original nine patches, four overlays, 25-file delivery boundary, pinned Bend
checker, frozen routing law, TODO contract, accepted routes and frozen sum example
remain protected. No native/GPU performance, general fresh-agent productivity or
parallel-review speedup is claimed. The historical `PARALLEL_TEST.md` describes
its own baseline, not the current acceptance result.
