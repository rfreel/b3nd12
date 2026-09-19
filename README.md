# B3ND12

B3ND12 builds a more usable environment for the next Bend agent while preserving
an exact, pinned language delivery. It contains two separate mechanisms:

- **Delivery:** nine ordered patches install agent guidance and CLI ergonomics
  onto Bend 2.0.9, commit `e5a4c4cfe980c2e4e70571562efb5197fe27b2f4`.
- **Acceptance experiment:** a frozen Bend law checks whether a routing candidate
  preserves three task results, increases none of their file-read counts, reduces
  their total reads, and fits a 4 KiB budget.

The experiment establishes a finite lookup property. It does not prove that
arbitrary future agents become more capable, or that this process is isolated
from an attacker with the same filesystem permissions.

## Start with a task

Python 3.10+, Git and a POSIX shell are required. Bun is required for Bend proofs
and executable contract tests.

```sh
python3 b3nd12.py doctor --json
python3 b3nd12.py task implement
python3 b3nd12.py task prove
python3 b3nd12.py task diagnose
```

Task results contain the unchanged pack or diagnostic content, plus the actual
files read. All management commands support `--json` and `--human`. Pipes default
to JSON. See [the CLI contract](docs/CLI.md) for aliases, errors, and schemas.

## Check an environment candidate

```sh
python3 accretion/run.py --bend-root /path/to/pinned/bend --bun /path/to/bun
python3 accretion/run.py --bend-root /path/to/pinned/bend --bun /path/to/bun --candidate candidate.json
```

The first command reproduces three rounds in temporary state and tests rejected
candidates. It does not reset accepted routes. The second evaluates a candidate
against current routes and returns a nonzero exit on rejection. It never promotes
arbitrary input. [The acceptance contract](docs/ACCRETION.md) explains the law,
evidence producer, promotion limits, and observed results.

The accepted table already attains two reads per task in this representation.
An unchanged candidate fails the strict-gain condition. Improving another metric
or changing the workload requires a new reviewed contract, not a weaker proof.

[Frozen TODO replay](docs/FROZEN_TODO.md) adds an ordered outcome contract,
bounded experiments, repeated observations and evidence receipts. Its final task
produces a successor proposal without authorizing another workload. The replay
leaves accepted routes unchanged.

The [progress ledger](docs/BACKLOG_PROGRESS.md) records completed, open and blocked
work against the immutable [100-task proposal](docs/TODO_100.md). That proposal
does not replace the executable frozen contract.

## Install the pinned delivery

```sh
python3 b3nd12.py apply /path/to/clean/bend --json
python3 b3nd12.py verify /path/to/bend --human
```

`apply.sh TARGET` and `verify.sh TARGET` remain supported. Installation requires
a clean checkout at the exact pin and exclusive access while writing. The entire
stack is applied to a temporary index first and checked against all 25 delivery
files. Only then are patches applied in numeric order. Verification checks bytes,
file modes, and staged/working theory against the pin. `bend2/bend.ts` is unchanged.
Post-write failures leave the target available for diagnosis; no reset is performed.
The [installation contract](docs/INSTALLATION.md) documents the explicit manifest,
sealed patch inputs, refusal boundaries and replayable installation receipts.

Management code, acceptance experiments, and examples are not installed into Bend.
The installed CLI retains its existing diagnostic JSON Lines and graph behavior.

## Verify changes

```sh
python3 -m venv /path/outside/repository/test-venv
/path/outside/repository/test-venv/bin/pip install -r requirements-test.txt
. /path/outside/repository/test-venv/bin/activate
python3 tests/patch_stack.py /path/to/pinned/bend
python3 tests/cli.py /path/to/pinned/bend
python3 tests/bend_contracts.py /path/to/pinned/bend
python3 tests/accretion.py /path/to/pinned/bend /path/to/bun
python3 tests/program.py /path/to/pinned/bend /path/to/bun
python3 tests/backlog.py
python3 tests/ci_contract.py
```

Put Bun on PATH for the installed Bend contracts. Tests cover exact installation,
refusals, terminal and pipe output, proof checking, graph output, interpretation,
emitted JavaScript, and acceptance/rejection of routing changes. A separate native
check covers the frozen sum and a bounded Nat corpus with an explicitly supplied
Clang compiler. GPU and upstream cluster checks remain unverified.

The [workflow](.github/workflows/verify.yml) lists the complete acceptance suite;
the commands above are the core checks. [The acceptance record](docs/ACCEPTANCE_RUN.md)
identifies the tested source and coverage limits. Schema tests use the pinned
test-only dependency; the management commands use Python's standard library.
[Evidence protocol](docs/EVIDENCE_PROTOCOL.md) documents independent verification,
proof reconstruction, bounded storage and archive round trips. A retained digest
detects packet changes; it does not authenticate the measurements themselves.

On Linux x86-64, prepared checks can run with inherited network denial:
`python3 offline.py -- python3 tests/patch_stack.py /path/to/pinned/bend`.
Acquire dependencies first. The guard denies network socket creation and
connections in its process and descendants. Anonymous Unix socket pairs remain
available for local subprocess streams. Filesystem access and other agents are
not isolated.

Run the optional CPU-native corpus with
`python3 tests/native_backend.py /path/to/pinned/bend /path/to/bun /path/to/clang --output /path/outside/repository/new-native-evidence`.
The compiler must satisfy the pinned Bend prerequisites. This check records
tool identities and exact backend outputs; it makes no GPU or performance claim.

For repeatable management measurements, run
`python3 benchmarks/management.py /path/to/pinned/bend --output /path/outside/repository/new-benchmark --runs 10 --warmup 1`.
The report retains commands, raw observations, source identities, latency
percentiles, throughput and process resource counters. It makes no speedup claim.

## Repository map

| Area | Responsibility |
|---|---|
| `accretion/` | Frozen lookup law, evaluator, proof template and accepted routes |
| `b3nd12.py`, `stack.py` | Management interface and exact delivery checks |
| `patches/`, `overlay/` | Ordered changes and independent expected-byte oracle |
| `guide/agent/`, `CLAUDE.md`, `evals/` | Existing installed agent material |
| `spec/`, `tests/` | Public schemas and executable contracts |
| `examples/frozen-spec-twin/` | Sealed official sum example; law/spec/main unchanged |
| `docs/` | Current contract, verification, and labeled historical investigations |

Read [docs/INDEX.md](docs/INDEX.md) for the distinction between current evidence
and earlier candidate studies. The ranked HTML ledger records the original patch
ranks only. No source reorganization or upstream-version migration is included.
