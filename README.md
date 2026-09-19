# b3nd12

Agent ergonomics overlay for Bend, pinned to bendlang/bend commit e5a4c4cfe980c2e4e70571562efb5197fe27b2f4, version 2.0.9.

## Apply

```sh
./apply.sh /path/to/clean/bend-checkout
```

The target must be clean and exactly at the pinned commit. apply.sh validates the complete stack in a temporary index, applies patches in numeric order, then runs verify.sh. Verification refuses any bend2/bend.ts change.

ranked-deepenings.html is the implementation ledger. guide/agent is the compact agent surface. patches contains executable ranked deltas. overlay retains the expected contents of the four modified upstream files.

Run the installation regression test against a local Bend repository containing the pinned commit:

```sh
python3 tests/patch_stack.py /path/to/bend-checkout
```

The test uses temporary checkouts, checks direct patch application and apply.sh, compares every installed file with the existing delivery files, and rejects changes outside that file set. Bun smoke checks run through verify.sh when Bun is available.

## Management CLI

Python 3.10+, Git, and a POSIX shell are required. Bun enables installed-CLI
smoke checks and is required for the executable Bend contract test.

```sh
python3 b3nd12.py doctor
python3 b3nd12.py apply /path/to/clean/bend-checkout --json
python3 b3nd12.py verify /path/to/bend-checkout --human
python3 b3nd12.py guide prove
```

Every management command accepts `--json` and `--human`; piped output defaults
to JSON. Errors have stable codes and corrective context. See [CLI contract](docs/CLI.md)
for schemas, aliases, exit codes and compatibility. The installed Bend CLI
retains its diagnostic JSON Lines and graph behavior.

Preflight verifies the entire patch sequence and its resulting bytes before
writing. Verification compares all 25 delivery files, upstream file modes,
and both staged and working theory bytes with the pin. Use exclusive access
to the target during installation. Post-write failures are reported and leave
the target available for diagnosis; no automatic reset is performed.

Run the local acceptance checks with a Bend repository containing the pin:

```sh
python3 tests/patch_stack.py /path/to/bend-checkout
python3 tests/cli.py /path/to/bend-checkout
python3 tests/bend_contracts.py /path/to/bend-checkout
```

The last command requires Bun and exercises real installed Bend behavior,
including a valid proof, a refused proof, graph output, and emitted JavaScript.
Native/GPU execution and upstream cluster gates are not covered by these checks.

[Improvement program](docs/IMPROVEMENT_PROGRAM.md),
[verification ledger](docs/VERIFICATION.md), and
[organization proposal](PROPOSED_CODE_FILE_REORGANIZATION_PLAN.md) record the
implemented scope, evidence and remaining work. The
[upstream investigation](docs/UPSTREAM_INVESTIGATION.md) concerns Bend 2.0.15;
its measurements do not establish performance of this 2.0.9 delivery.
