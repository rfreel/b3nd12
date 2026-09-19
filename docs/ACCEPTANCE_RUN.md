# Acceptance run

This ledger covers the repository-local acceptance and installation repairs on
`improve/verified-stack-and-cli`. It does not close the entire 100-task proposal.
The task-by-task disposition is in [BACKLOG_PROGRESS.md](BACKLOG_PROGRESS.md).

## Environment and commands

Working directory: `/workspace/scratch/907925b1ae78/b3nd12`.
The checkout supplied to tests is Bend 2.0.9 at
`e5a4c4cfe980c2e4e70571562efb5197fe27b2f4`. The host is Linux x86-64, with
Python 3.12.14, Git 2.51.1 and Bun 1.4.2. Schema tests use the external virtual
environment with `jsonschema==4.26.0`; production Python remains standard-library
only. Dependency acquisition precedes these tests.

The coordinator ran the following commands with this interpreter and PATH.
Three independent suites ran concurrently, each with disposable test directories.
All 24 commands exited zero after the final production-source edits.

```sh
export PATH=/workspace/scratch/907925b1ae78/tooling/test-venv/bin:/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH
python tests/patch_stack.py ../bend-pinned
python tests/cli.py ../bend-pinned
python tests/bend_contracts.py ../bend-pinned
python tests/accretion.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/program.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/process.py
python tests/cli_schema.py
python tests/cli_properties.py ../bend-pinned
python tests/install_adversarial.py ../bend-pinned
python tests/checker_failures.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/evidence.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/recheck.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/archive.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/storage.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/output_bounds.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/routing_domain.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/law_conjuncts.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/spec_twin.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/translation.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/smoke.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python tests/benchmark_contract.py ../bend-pinned
python tests/install_receipt.py ../bend-pinned
python tests/backlog.py
python tests/ci_contract.py
```

The longest suites were storage interruption checks at 41.46 seconds, finite
routing checks at 37.08 seconds, and adversarial installation at 27.20 seconds.
These are test durations under concurrent execution, not performance results.
Raw commands, exits, durations and diagnostic logs remain outside Git.

The model-test worker then completed this additional command in 127.82 seconds:

```sh
python3 tests/controller_model.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
```

All 1,213 reachable prefixes and terminal traces through the six-attempt budget
agree with the independent model, including 910 terminal branches. The test uses
real controller/storage code and controlled checker observations. It does not
exhaust candidate bytes or parser errors. An earlier run correctly refused a
concurrent source edit; only the subsequent stable-source run counts as a pass.

Python compilation, `sh -n apply.sh verify.sh`, and `git diff --check` also pass.
The protected patch, overlay, guide, evaluation, sum-example, law, TODO, accepted
route and upstream-pin paths have no diff. The proposal hash remains unchanged.

## Coverage and interpretation

| Requirement | Execution evidence | Limit |
|---|---|---|
| Exact installation | Nine sealed ranks install all 25 declared files; source-patch mutation cannot replace preflighted bytes | Exclusive access; post-write rollback is not implemented |
| Git and filesystem refusal | Environment, attributes, linked worktrees, ignored collisions, modes and patch mutations | Explicit supported matrix, not every Git option or filesystem |
| Installation replay | Receipt hashes bind source, manifest, patch order and both Python identities; independent clone reproduces delivery | Retained digest is supplied by the operator; no download authentication |
| Checker classification | Real positive/negative books plus crash, timeout, spawn and certificate controls | A substituted runtime is not independently authenticated |
| Routing predicate | All 64 semantic tables against four declared baselines, 256 real checker decisions | Finite task set; no claim over arbitrary agent work |
| Evidence translation | Eight generated-source mutations are detected by a separate literal oracle | Four corrupted books still pass Bend, demonstrating the observation-trust boundary |
| Packet verification | Changed chains and rehashed false conclusions refused; summaries reconstructed without running saved source | Conditional integrity relative to retained digests |
| Controller accounting | Complete reachable six-attempt four-verdict tree agrees with an independent transition model | Checker observations are simulated in this state-machine test |
| Durability | Forty-one process-kill boundaries and write/fsync/rename failure fixtures | POSIX filesystem guarantees; not physical power-loss certification |
| Diagnostic storage | ASCII and invalid-UTF8 noisy children retain bounded UNKNOWN receipts | Truncated prefixes and observed-byte lower bounds, not complete output |
| Archive and proof reconstruction | Exact round trip, hostile ZIP refusals and reconstructed accepted books | Directory import is not crash-atomic; original process authenticity is not proved |
| CLI | Full command schemas, 102 parser cases, actual PTYs, error parity and read-only state snapshots | Rare error causes include controlled injection |
| Frozen sum example | Original hashes, legal write set and eight forbidden mutations checked | Native and GPU execution remain unavailable |
| Runtime smoke | Missing, failing and real Bun leave static verification distinguishable | Full JSON runtime-status parity and a dedicated hung-smoke case remain open |
| Benchmark entry point | Real equivalent-work measurement contract runs with source/tool identities and raw observations | No optimization, noise model or speedup is established |
| CI orchestration | Exact 23-suite shell block stops on each injected failure | Executable doubles establish ordering, not hosted execution |

## Review findings repaired

Six workers examined separate areas; reviewers also inspected other workers'
changes. They share filesystem authority and are not independent security
principals. The review found and repaired:

- A verifier that did not recognize the producer's new `output_limit` status.
- Invalid UTF-8 diagnostics whose JSON expansion exceeded the durable artifact
  cap. The checker capture limit is now 256 KiB and the regression runs a real
  noisy process.
- Installation receipts that identified the calling Python but omitted the
  installer's PATH-resolved `python3`.
- Nested cleanup races. Supported cooperative wrappers now use bounded nesting
  and decreasing grace periods; a TERM-resistant child regression passes.
- A benchmark source manifest that omitted untracked production dependencies.

T006 remains unfinished: the supported wrapper protocol does not establish
arbitrary process-tree containment, and the measurement runner has a separate
deadline mechanism. Repeated external cancellation, hostile session escapes and
unresponsive wrappers are outside the demonstrated guarantee.

## Remaining gates

No source reorganization, frozen-contract expansion, native/GPU optimization,
fresh-agent productivity claim or autonomous successor activation is included.
Native compilation lacks the pinned compiler prerequisite; GPU and macOS lanes
lack matching hardware. Namespace-isolation probes fail on this host. Provider
usage reconciliation and an authenticated external receipt authority are absent.
Repository-local unfinished designs remain OPEN rather than being described as
infrastructure failures. T100 cannot run while earlier tasks lack acceptance.

## Management baseline

The following command completed after the acceptance suites and model run, with
the implementation files unchanged throughout measurement:

```sh
python3 benchmarks/management.py ../bend-pinned --output ../evidence-bend/management-current --runs 10 --warmup 1
```

| Equivalent verification surface | p50 ms | p95 ms | p99 ms | Jobs/s | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|
| Exact shell verification | 78.49 | 86.95 | 86.95 | 12.65 | 41.23 |
| Exact JSON verification | 87.68 | 94.39 | 94.39 | 11.36 | 41.23 |

Each surface has ten measured runs after one warmup. Pair order alternates, Bun
is excluded, and startup is included. Percentiles use nearest rank, so p95 and
p99 are the observed maximum at this sample size. RSS is the operating system's
`wait4` accounting, not simultaneous total process-tree memory. Raw CPU and
physical block counters, commands, exits and executable/source hashes are kept
with the external report. Completion polling has 2 ms granularity.

This measures the prepublication working tree over `f4c930a`, identified by every
source-file hash in the report. It is not a result for the unchanged `f4c930a`
commit. Later editorial and publication records do not change the measured
implementation. No timing-noise threshold, CPU/allocation profile, before/after
optimization result or comparison with historical host measurements is claimed.
