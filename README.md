# b3nd12

Agent ergonomics overlay for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

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
