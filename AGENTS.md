# AGENTS

This repository is an ordered patch stack over the Bend upstream pinned in upstream.json.

Start at guide/agent/ROUTER.md. Load the smallest legal working set. Do not dump the full Bend guide into agent context unless the router explicitly escalates to it.

Hard boundary: bend2/bend.ts is theory and checker source. Ergonomics changes do not edit it.

Apply patches in patches/ numeric order. Update ranked-deepenings.html when each ranked change closes.

## Management commands

Use `python3 b3nd12.py doctor --json` to inspect prerequisites and
`python3 b3nd12.py verify TARGET --json` to inspect an installed delivery.
Only exact `apply TARGET` installs; do not reset or stash a dirty target.
JSON results use `b3nd12.cli.v1`; see docs/CLI.md for statuses and fields.
Run tests/patch_stack.py and tests/cli.py against a repository containing the
pin. Run tests/bend_contracts.py with Bun for executable behavior evidence.
Management files are not added to the installed Bend tree. Keep the declared
25-file delivery and protected theory boundary unless a separate scope change
is authorized. Read docs/VERIFICATION.md before making coverage claims.

## Environment improvement contract

Start repository work with docs/ACCRETION.md. The executable law covers only the
three-task routing workload. Use `python3 b3nd12.py task prove` for proof work;
the other task names are implement and diagnose. Propose routing data, not
executable evaluator changes.
Do not weaken accretion/LAWS.bend, replace the oracle, or reset accepted routes
to manufacture a gain. Changing the task set or cost model requires a separate
contract review. Run tests/accretion.py with the pinned checker and Bun.
A passing finite certificate is not evidence of general agent productivity.
Keep historical investigation and current acceptance evidence labeled separately.
