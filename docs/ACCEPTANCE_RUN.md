# Acceptance run

This ledger covers the repository-local acceptance and installation repairs on
`improve/verified-stack-and-cli`. It does not close the entire 100-task proposal.
The task-by-task disposition is in [BACKLOG_PROGRESS.md](BACKLOG_PROGRESS.md).
Published head `0b20423` passed
[hosted run 35431837293](https://github.com/rfreel/b3nd12/actions/runs/35431837293).
The subsequent changes passed the local integrated checks below. Their hosted
publication result is separate from the result for `0b20423`.

## Subsequent integrated acceptance

The native worker ran
`python3 tests/native_backend.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun ../tooling/apt-native/root/usr/bin/clang-18 --output ../evidence-bend/native-20260919-final`.
The command passed with Ubuntu Clang 18.1.3. It checked the frozen proof and ran
the frozen native sum with one and four threads; both printed `2147450880`.
Sixteen programs, consisting of sum and seq at eight `(d,i)` pairs, agreed across
interpreter, emitted JavaScript and native CPU execution. The pairs were `(0,0)`,
`(0,7)`, `(1,5)`, `(2,3)`, `(3,11)`, `(4,1)`, `(5,9)` and `(6,2)`.

The external report records 88 commands and 48 corpus backend executions. Its
SHA-256 is `9bb6f5b3ecbd25d54ae45c0c1af017e27e2ffc29e914b7e85e218e367a8ef674`.
Compiler acquisition used six packages whose bytes and sizes matched an Ubuntu
package index authenticated through the existing Ubuntu archive keyring. The
provenance record has SHA-256
`8abd50d011e0468c85ad51aa409915db463b75a14766271f069ad55e2639ee44`.
Frozen source and compiler inputs remained unchanged. This is bounded CPU
execution evidence, not a performance result, GPU result or runtime-authority
approval. Independent review accepted the native check; its later offline rerun
also passed as recorded below.

The prepared-check workflow now runs through `offline.py` after dependency
acquisition. The Linux x86-64 guard sets `no_new_privs` and installs a seccomp
filter inherited by descendants. It closes inherited descriptors above stderr,
refuses socket-backed standard streams, rejects alternate ABIs, and denies
named socket creation, connections, asynchronous I/O setup and importing another
process's descriptor. It permits anonymous `AF_UNIX` socket pairs and `recvfrom`
for Bun's local subprocess streams. Unsupported hosts or filter installation
failure refuse execution.

`tests/offline.py` passes actual Python, Git and Bun network-refusal probes,
local execution and descriptor checks. It runs outside the filter so its control
process can create a loopback listener. Independent review and full prepared
suite execution under the repaired guard passed. The guard does not
isolate files, other agents or external helpers, and does not establish a hostile
worker boundary.

The first integrated offline run passed 26 ordinary checks but failed the native
check because the initial filter also denied Bun's local subprocess IPC. That
native run is a failure and supplies no backend acceptance. Focused probes
identified the required anonymous socket-pair and receive operations. After the
narrow filter change, the network-refusal controls and independent review passed.
The repaired filter then passed all 26 ordinary checks and the native corpus.
The failed packet remains at `../evidence-bend/native-offline-final`; the first
ordinary-run records remain at `../evidence-bend/continuation-offline`.

The exact repaired ordinary-run command was
`python3 offline.py -- ../tooling/test-venv/bin/python ../evidence-bend/continuation-offline-repaired/run.py`.
Its `results.json` and per-suite logs retain all commands, exits and durations.
All 26 exits are zero; the controller model took approximately 130 seconds.
These are test durations, not performance measurements.

The exact repaired native command was
`python3 offline.py -- python3 tests/native_backend.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun ../tooling/apt-native/root/usr/bin/clang-18 --output ../evidence-bend/native-offline-repaired`.
It passed all 88 commands and 16 corpus cases. The report SHA-256 is
`5bbd13eccf0272d56c957eedcdb529681edaeaaac219ae940eb3790a3d37a0e5`.
The accompanying `invocation.json` binds the command and the offline guard digest
`5f34af8d4b9c5a9a800ba1dc6d4b72e54874dcb6e8344f0064a00d81d29729d3`.

Reviewed staged-index checks, static/runtime statuses, bootstrap exceptions,
documentation recipes and the controlled mutation catalog also passed. Together
these results close T032, T040, T047, T057, T058, T085, T089 and T090. The full
backlog remains incomplete: 44 DONE, 29 OPEN and 27 BLOCKED. T099's general
claim-to-test mapping and hostile-worker isolation remain unfinished.

Final review found that the published CLI JSON example omitted the `index`
check. The example and its retained fingerprint were corrected. The documentation
test now compares the complete example envelope with an actual verification
result, normalizing only the temporary target path. A control that removes
`index` is rejected. The focused documentation suite passed again under the
offline guard after this repair.

## Published baseline environment and commands

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

## Published baseline coverage and interpretation

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
| Frozen sum example | Original hashes, legal write set and eight forbidden mutations checked | Native and GPU execution were unavailable at this baseline |
| Runtime smoke | Missing, failing and real Bun leave static verification distinguishable | JSON status parity and hung-smoke coverage were incomplete at this baseline |
| Benchmark entry point | Real equivalent-work measurement contract runs with source/tool identities and raw observations | No optimization, noise model or speedup is established |
| CI orchestration | Exact 23-suite shell block stops on each injected failure | Executable doubles establish ordering, not hosted execution |

## Published baseline review findings repaired

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
Native CPU execution now passes the bounded corpus above. GPU and macOS lanes
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
