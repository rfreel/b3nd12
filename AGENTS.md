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
