# Frozen outcomes and bounded experiments

`accretion/program.py` runs a repository-only replay of the existing routing
experiment. It uses the existing resolver, byte oracle, Bend law and pinned
checker. It never installs routes or activates a successor contract.

The frozen contract is `accretion/TODO.json`. Its ordered outcomes are total
file-read counts of at most 8, 7 and 6 across the three declared tasks. The final
task is to produce a successor proposal. All earlier outcomes must pass first.
Dependencies follow that order; completion is recorded once per outcome.

The starting empty table is an explicit experimental baseline. Current installed
routes remain untouched and already reach six reads. Replaying this experiment
does not count as a new improvement to the accepted environment.

## Run

Review the contract and retain its digest outside the candidate's write access.
The current contract digest is:

```text
8e0074c4bddb7a8de684d11d7a2db93021c013bd290d2fe8378dff941fb1c40b
```

```sh
python3 accretion/program.py \
  --contract-sha256 8e0074c4bddb7a8de684d11d7a2db93021c013bd290d2fe8378dff941fb1c40b \
  --bend-root /path/to/pinned/bend --bun /path/to/bun \
  --output /path/outside/repository/new-evidence-directory
```

The resolved output destination must be outside the repository, including when
reached through a relative path or a symlink alias. Repository-contained outputs
are refused before directories are created. This checks physical containment;
it does not isolate concurrent filesystem changes by another process.

An existing output directory is refused. Output is JSON; exit 0 means all
outcomes and the successor task completed. Exit 1 means refusal, unresolved
evidence, an exhausted trial budget, or an incomplete candidate queue. An
interrupted run has no successful summary and is not resumable.

By default the controller measures current reads and chooses a missing route
with the highest read count, breaking ties by task name. Each route has the same
one-read benefit and implementation effort. Selection is recalculated after
each trial. The remaining opportunities are finite and exhaustible.

Use repeated `--candidate FILE` arguments to supply up to six candidate tables
instead. Input files contain routing data only. Supplied verdicts, paths outside
the task set and bundled route changes are refused. Candidate files are read
once with a 4097-byte cap; the saved buffer is the evaluated buffer.

## Experiment and acceptance

Each attempt changes at most one route and consumes one of six trial slots,
including malformed and neutral attempts. Valid candidates receive three paired
baseline/candidate observations through the real resolver and checker. The
instrument counts logical file reads; it does not estimate timing, allocations,
physical I/O or fresh-agent productivity. Repetition tests deterministic
agreement; it is not a statistical latency experiment.

The proof sketch for a direct route is that it selects the same document while
omitting the fallback router read. Each observation also checks all three output
documents against the frozen expected bytes and checks per-task nonregression.
The unchanged candidate is tested before any trial as a refusal control.

| Verdict | State effect |
|---|---|
| PRODUCTIVE | Three consistent observations pass the Bend law; advance the experimental baseline and record newly met outcomes |
| NEUTRAL | No read reduction; keep the previous baseline and preserve the receipt |
| REJECTED | Schema, single-lever rule, content or per-task cost fails; preserve the receipt without completion credit |
| UNKNOWN | Observations disagree or the checker cannot establish a claimed gain; preserve evidence and stop |

`LAND-DE-RISK` is not admitted by this contract. Risk reduction alone cannot
satisfy its frozen strict-gain law. No verdict authorizes installation.

## Evidence and successor

Each run saves the contract, evaluator input snapshots, source and runtime
identifiers, initial control, per-pass before/candidate bytes, repeated raw
observations, receipts, final state and summary. The append-only JSON Lines
ledger links records by hashes and binds verdicts to receipt hashes. Failed
attempts remain visible. Hash links detect edits relative to a retained digest;
they do not authenticate an author or prevent replacement of the entire log.

The final task writes `successor.json` only after all three outcomes complete.
For this representation its result is `exhausted`, with no proposed candidates:
every task already reads only the table and its document. The proposal names
its parent contract, carries the final measurements, and records
`activation: not_authorized`. A different workload or representation requires
a separately reviewed contract. The runner has no activation operation.

Bend checks the original finite improvement predicate. TODO accounting, budget
enforcement and record production are Python controller responsibilities, not
additional Bend theorems. The supplied contract digest and frozen input hashes
detect drift under cooperative execution. They do not isolate an agent sharing
the controller's filesystem permissions. Deployment under separate credentials
and a fresh-agent productivity study remain outside this implementation.

## Verification

```sh
python3 tests/program.py /path/to/pinned/bend /path/to/bun
```

The test runs three productive trials with nine real certificates and checks
seal refusal, evidence-directory reuse, receipt hashes, six-attempt exhaustion,
neutral trials, malformed inputs, bundled levers, duplicate completion,
regression, unresolved checker output, successor gating and unchanged routes.
The missing-certificate case uses a controlled process double; productive
trials use the actual pinned Bend checker.
