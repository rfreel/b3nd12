# Management CLI

Run `python3 b3nd12.py` from this repository. Python 3.10+, Git, and a POSIX
shell are required. Bun is optional for installation smoke checks and required
for `tests/bend_contracts.py`. There are no third-party Python dependencies.

| Command | Purpose |
|---|---|
| `doctor` | Show the pinned revision, patch count, and local tools |
| `apply TARGET` | Preflight and install the exact stack into a clean pinned checkout |
| `verify TARGET` | Compare installed paths and bytes against the delivery |
| `guide [router\|program\|prove]` | Print one compact local route |
| `help`, `--help` | Show commands, formats and exits |
| `version`, `--version` | Show management schema version and pinned Bend version |

No arguments print a concise quick start. All commands accept `--json` and
`--human`. Non-TTY stdout defaults to JSON; terminal stdout defaults to human
text. Supplying both is an error. Options may precede or follow the command.
Use `--` before a literal target that begins with a dash.

Examples:

```sh
python3 b3nd12.py doctor --json
python3 b3nd12.py apply /path/to/clean/bend --json
python3 b3nd12.py verify /path/to/bend --human
python3 b3nd12.py guide prove --json
```

Read-only aliases are `check` for `verify`, `status` for `doctor`, `-h` for help,
and `-v` for version. Read-only command spelling ignores case and dash/underscore
separators. Normalized invocations return their canonical argument array and
`corrected: true`; human mode writes the accepted array to stderr. Paths, route
names and their case remain exact. Only the exact command `apply` may install.
Unknown commands, extra operands and ambiguous formats are rejected.

## JSON v1

Each invocation prints one JSON object on stdout. JSON-mode errors leave stderr
empty; subprocess diagnostics appear in error context. The schema is
`spec/cli-v1.schema.json`.

```json
{"schema":"b3nd12.cli.v1","ok":true,"command":["verify","/path/to/bend"],"corrected":false,"result":{"pin":"e5a4c4cfe980c2e4e70571562efb5197fe27b2f4","files":25,"theory_unchanged":true,"delivery":"byte-identical","checks":["pin","scope","bytes","theory","whitespace"],"target":"/path/to/bend"},"error":null,"exit_code":0}
```

`command` is the accepted argument array, or null when parsing fails. Quick start
uses an empty array. `result` is an object on success and null on failure. Error
objects contain stable `code`, `message`, `context`, `correction`, and up to two
`examples`. Human and JSON modes return the same classification and status.
Human success goes to stdout; errors and correction notices go to stderr.

Result fields by command: help/quick start provide `text`; guide adds `route`;
version provides `version`, `bend_version`, and `pin`; doctor provides `pin`,
`tools`, `patches`, and `runtime_checks`; verify provides the fields shown above;
apply adds its installation `log`. The schema permits future result fields.

| Exit | Meaning | Representative codes |
|---:|---|---|
| 0 | Success | error is null |
| 1 | Resource missing | NOT_FOUND |
| 2 | Invalid or ambiguous intent | INVALID_COMMAND, INVALID_ARGUMENTS, INVALID_TARGET, AMBIGUOUS_FORMAT |
| 3 | Configuration | WRONG_PIN, DIRTY_TARGET, MISSING_TOOL, GIT_FAILED, CONFIGURATION |
| 4 | External service failure | Reserved; management commands do not contact services |
| 5 | Internal or delivery invariant failure | PATCH_SEQUENCE, FILE_SCOPE, CONTENT_MISMATCH, THEORY_CHANGED, FILE_MODE, INSTALL_FAILED, INTERNAL |

## Compatibility and operational limits

`apply.sh TARGET` and `verify.sh TARGET` remain human-readable compatibility
entry points with their existing shell exit convention. The robot contract is
provided by `b3nd12.py`; it does not change Bend's installed `--json` diagnostic
JSON Lines or graph schema. Use the management entry point for stable statuses.

Installation requires exclusive access to the target while checking and writing.
The full stack and its resulting delivery are checked in a temporary index
before writes. Disk failure, concurrent mutation, or a failing post-write runtime
check can still leave the target modified; the command reports failure and does
not reset or delete files. Preserve that target for diagnosis. No transaction
across filesystem writes or concurrent-install guarantee is claimed.

Verification deliberately refuses extra tracked or untracked delivery changes.
Ignored build artifacts are outside the path-set check. It verifies source bytes
and the protected staged theory, not external toolchain trust or every backend.
Installation does not modify the target's real Git index.

The manager has no configuration file, authentication, pagination, or remote API.
Bun smoke commands set `BEND_NO_TELEMETRY=1`. A missing Bun is reported by doctor;
it does not turn source verification into a claim of runtime validation.
