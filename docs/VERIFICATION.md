# Verification ledger

The latest integrated checks and backlog repairs are recorded in
[BACKLOG_PROGRESS.md](BACKLOG_PROGRESS.md). Earlier measurements below retain
their original scope and do not serve as new performance claims.

Target repository: rfreel/b3nd12. Upstream pin:
`e5a4c4cfe980c2e4e70571562efb5197fe27b2f4`, Bend 2.0.9.
Environment: Linux x86-64, Python 3.12, Git, Bun 1.4.2.

## Executed acceptance commands

Working directory: `/workspace/scratch/907925b1ae78/b3nd12`.
Bun was installed outside the repository. These are the exact invocation forms:

```sh
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/patch_stack.py ../bend-pinned
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/cli.py ../bend-pinned
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/bend_contracts.py ../bend-pinned
python3 -m py_compile b3nd12.py stack.py tests/cli.py tests/patch_stack.py tests/bend_contracts.py
sh -n apply.sh verify.sh
git diff --check
```

All passed on the final implementation. The three acceptance scripts use real
Git checkouts and subprocesses. No generated checkout or compiled output is
committed. The original patch-only repair was also tested with Bun before the
management changes were introduced.

## Coverage matrix

| Requirement | Path / test | Data source and observed evidence | Remaining limit |
|---|---|---|---|
| Ordered ranks | patch_stack.py direct git apply | All nine ranks applied with whitespace errors enabled | Specific declared pin |
| Installer parity | apply.sh through patch_stack.py | All 25 files match existing overlays/additive delivery exactly | Existing delivery is the oracle |
| Preflight refusal | malformed rank 9, missing rank, delivery drift, mode mutation | No target status change after refused installs | Filesystem failure after writes is not transactional |
| Clean/pin guard | wrong commit and dirty reapplication | Nonzero exit; target unchanged | Exclusive checkout access required |
| Real index preservation | installation oracle | No staged files after install | Caller must not mutate concurrently |
| Protected theory | CLI staged mutation test | Staged edit refused even after working bytes restored | No theorem about upstream theory itself |
| Exact file bytes | CLI tamper test | Changed main.ts refused | Ignored artifacts outside delivery check |
| File modes | index preflight and core.filemode=false test | Executable-bit changes refused despite Git ignoring them | POSIX permission model |
| Every management command JSON | cli.py subprocess assertions | Required envelope fields, types at key boundaries, status and error keys checked | No third-party full JSON Schema validator |
| TTY/non-TTY | cli.py real PTY plus pipes | Terminal quick start is text; pipes produce one JSON object | Linux PTY tested |
| Error recovery and aliases | cli.py | Missing/config/argument/invariant errors, normalized read-only aliases, exact apply | Exit 4 reserved, no external service command |
| Stream separation | cli.py | JSON stderr empty; human failure on stderr | Installer diagnostic text is nested in context |
| Help and examples | cli.py, runtime routes | Quick-start size bounded; guide routes executed | No rendered-doc tooling configured |
| Proof-import contract | bend_contracts.py | Missing LAWS import gives BND101; actual valid proof checks | One representative proof |
| Diagnostic schema | bend_contracts.py | BND000 success and BND200 graph error from real Bend | Existing schema permits extra fields |
| Graph and routing | bend_contracts.py | Named root, node, router, PROGRAM, PROVE, full guide and why output | Representative slice |
| End-to-end program | bend_contracts.py | Real source interprets to 5n; emitted JS runs to 5n | Native/GPU unverified |
| Syntax/whitespace | py_compile, sh -n, git diff --check | Pass | No configured lint/type checker for Python |

## Failures found and repaired

The first positive proof fixture omitted required parentheses in `def
Laws.identity()`. The actual Bend parser refused it. Correcting the fixture
made the complete positive proof pass; the negative import case remains refused.
This was a test-fixture error, not a language change.

Review found that `git diff --summary` alone could miss executable-bit changes
when `core.filemode=false`. Verification now compares filesystem executable
bits with the pinned tree directly; a regression test sets that configuration
and changes the mode. Preflight compares temporary-index modes as well.

The original verifier checked keywords and only an unstaged theory diff.
It could not establish delivered-byte equivalence or catch a staged kernel edit
whose working copy had been restored. Both cases now have negative tests.

## Skipped and blocked checks

- Native C, Metal and CUDA execution: compatible Clang/device tooling unavailable.
- Upstream cluster test/performance gates: cluster transport unavailable in the
  preceding investigation; not represented as a local gate pass.
- Release/installer/hub service integration: sibling site repository and isolated
  release infrastructure unavailable. The manager contacts no external service.
- Provider pagination, rate-limit and authentication tests: not applicable to
  the management CLI, which has no provider integration. Upstream package-hub
  coverage is not claimed.
- Browser, viewport and assistive-technology checks: no functional UI changes.
- Formatter, linter, security scanner and packaging job: none configured in
  B3ND12. Python/shell syntax and manual boundary review were executed instead.
- Universal semantic equivalence: not claimed from finite tests. Installed
  source bytes equal the existing delivery, and selected executable paths pass.

## Review outcome

The committed work changes installation, management presentation and verification.
It does not change the upstream pin, installed file set, overlay source bytes,
Bend diagnostics, foreign effects, compiler runtime, or theory. No source files
are reorganized. Temporary upstream 2.0.15 experiments remain outside this repo
and are not included in its commits. Raw timing and profile records remain in
the investigation workspace, outside Git. Commit messages record their own
scope and checks; branch hashes and the actual push result are reported after
publication.

## Management performance measurement

Exact measurement command from the same working directory:
`python3 ../evidence-bend/measure-management.py`. The script and raw JSON are
kept in the separate evidence packet. It creates a disposable installed checkout,
extracts the original keyword verifier from the baseline commit, warms each
command once, then runs 30 serial fresh processes. Bun is absent from PATH for
all three comparisons. Percentiles use nearest rank; p99 at this sample size is
the observed maximum. RSS is Linux wait4 maximum child RSS.

| Verification path | p50 ms | p95 ms | p99 ms | Jobs/s | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|
| Original keyword verifier | 185.89 | 199.24 | 209.16 | 5.309 | 15.93 |
| Exact shell verifier | 585.44 | 625.53 | 645.60 | 1.696 | 16.85 |
| JSON management verifier | 580.74 | 629.38 | 634.75 | 1.704 | 16.85 |

The stronger verifier costs about 400 ms more at the median in this environment.
This is an integrity tradeoff, not a speedup or an equivalent-work performance
comparison. Differences between the two new paths are within the observed
variation; neither is claimed faster. Existing Bend program performance is
unchanged at the source level because the installed delivery bytes are unchanged.

A Python cProfile observation attributed approximately 90.2% of elapsed profiler
time to waiting for subprocess pipes, 2.3% to byte splitting, 1.3% to verify's
own work, 0.5% to regex parsing, and 0.3% to process creation. These are host-side
attributions, not an on-CPU profile of Git. Tracemalloc peaked at 858,269 bytes
for the Python verification call; it excludes Git's allocations. wait4 recorded
zero physical input blocks and 240 output blocks per 30-run group under the
warm cache. Block counts are not logical bytes read. Native syscall and Git
allocation profiling are not claimed.

No additional performance optimization was admitted. Batching more Git queries
is a possible later experiment; its score is impact 2 × confidence .6 / effort 2
= .6, below the integrity work. Persistent caches add invalidation risk without
a demonstrated interactive workload. Timing thresholds remain deferred until
unchanged controls establish a stable host baseline. Exact-byte and refusal
oracles provide deterministic regression protection now.

## Environment acceptance rounds

The current acceptance experiment is documented in ACCRETION.md. Executed:

```sh
python3 accretion/run.py --bend-root ../bend-pinned --bun ../tooling/node_modules/@oven/bun-linux-x64/bin/bun --promote
python3 tests/accretion.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
```

Three exact-content routing improvements checked successfully: total reads
9 → 8 → 7 → 6. Each round printed `All terms check.` through the checker.
Seven controls were refused: no gain, increased reads, wrong content, path escape,
unknown task, duplicate task and oversized candidate. The integration test also
checks the public task commands and refusal of modified compiler input. A no-gain
control now runs before any promotion to detect a permissive law early.

The three original acceptance scripts were rerun after adding task routing.
Python syntax and whitespace checks passed. Installed overlays and the declared
25-file scope remain unchanged. The earlier frozen spec-twin example is preserved
without edits to its law, seq, pow2 or main.

This is deterministic workload evidence, not a held-out fresh-agent study. The
Bend proof establishes the frozen predicate over evaluator-produced observations;
it does not authenticate those observations or enforce operating-system privileges.
The controlled demonstration's promotion mode refuses to restart from accepted
nonempty state. General external candidate evaluation is review-only. No claim of
an autonomous production RSI controller, native execution, or GPU performance is
made.

## Frozen TODO controller

The repository-only controller uses the original routing law and evaluator.
Its contract freezes the empty experimental baseline, outcomes of 8, 7 and 6
reads, six candidate attempts, three observations per valid candidate and the
final successor-proposal task. It does not reset or install accepted routes.

Executed from the repository root:

```sh
python3 tests/program.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python3 accretion/program.py --contract-sha256 8e0074c4bddb7a8de684d11d7a2db93021c013bd290d2fe8378dff941fb1c40b --bend-root ../bend-pinned --bun ../tooling/node_modules/@oven/bun-linux-x64/bin/bun --output ../evidence-bend/frozen-todo-final
python3 -m py_compile accretion/program.py tests/program.py
git diff --check
```

The existing patch-stack, management CLI and Bend contract commands listed above
also passed after this change. The original accretion suite passed before the
controller addition; its source and evaluator were unchanged. CI runs both
accretion suites before applying patches to the pristine checker checkout.

| Requirement | Observed evidence | Limit |
|---|---|---|
| Frozen contract and expected content | Modified outcomes, wrong seal and modified oracle refused before trial output creation | Operator retains the trusted digest independently |
| Ordered completion | Three trials produce 9 → 8 → 7 → 6; nine real checker certificates | Constructed routing workload |
| No duplicate credit | Repeated successful data is neutral; prior outcome recorded once | Finite three-outcome contract |
| Bounded failed search | Six unsuccessful trials consume all six slots; seventh candidate is not evaluated | Trial-count budget, not a wall-time quota |
| Evidence preservation | Before/candidate buffers, receipts, snapshots and linked ledger retained; reused output directory refused | Hash chain is not a signature or external immutable store |
| Unresolved evidence | Process returning success without a certificate stops with no completion | Controlled failure injection, not a real compiler defect |
| Successor dependency | Partial runs produce no proposal; complete run produces an exhausted proposal without activation | New workload selection remains a separate review |
| Delivery preservation | Installer matches all 25 files; theory bytes unchanged; task commands pass | Native/GPU checks remain unavailable |

An initial failure-injection fixture used a process that also refused the runtime
version query, stopping before its intended boundary. The corrected fixture
returns exit zero without a certificate and exercises unresolved evidence during
a trial. Productive trials use the actual pinned checker.

The final replay reports no remaining route candidate. It supplies no new timing,
allocation, GPU or fresh-agent performance claim. Budget and TODO accounting are
controller logic; the unchanged Bend law certifies only the original finite
improvement predicate.
