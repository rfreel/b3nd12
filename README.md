# b3nd12

Agent ergonomics overlay for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

## Agent entry point

```sh
python3 control.py status
python3 control.py next
```

[Start here](START_HERE.md) for the operating loop. The control interface binds
task completion to retained verification evidence and reopens stale conclusions.
It includes a replayable journal, bounded change queries, a dependency-aware
roadmap, and 26 metrics with separate measured values and future targets.

- [System design](docs/agent-system-design.md)
- [Implementation checklist](docs/agent-system-plan.md)
- [Long-term roadmap](docs/agent-roadmap.md)
- [Current TODO](TODO-agent-system.md)
- [Benchmark contract](docs/benchmarks.md)

The controller is local and supervised. Remote workers, signed evidence,
cross-clone coordination, and longitudinal agent trials are explicit future
tasks with acceptance gates.

## Apply

```sh
./apply.sh /path/to/clean/bend-checkout
```

The target must be exactly at the pinned commit. apply.sh installs exact full-file overlays plus additive agent files, then runs verify.sh. Verification refuses any bend2/bend.ts change.

ranked-deepenings.html is the implementation ledger. guide/agent is the compact agent surface. patches contains review-only ranked deltas.

## Repair admission and interaction pilot

The repository includes a finite Bend repair model with checked laws, an external
repair-report validator, and a reproducible four-configuration diagnostic experiment.
The pilot remains in this repository; `apply.sh` installs only the upstream overlay.

With Bun 1.2.22 and Python 3.12 available, run after applying the overlay:

```sh
./scripts/verify-supermodularity.sh /path/to/patched-bend-checkout
```

See [the pilot documentation](docs/supermodularity.md) for proof scope and commands,
and [the completion checklist](TODO-supermodularity.md) for work status.
The workflow runs these checks on pushes and pull requests. Requiring its status
for merge remains a repository-host policy, not a guarantee supplied by this code.

## Bounded proof research

The [autoresearch pilot](docs/autoresearch.md) checks proof simplifications
against fixed laws, preserves experiment evidence, and measures checking time.
Its first candidate reduces the finite model's proof case branches from 21 to
15. No speed improvement is claimed.
