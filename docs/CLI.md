# Management CLI

Run `python3 b3nd12.py` from this repository. Python 3.10+, Git, and a POSIX
shell are required. Bun is optional for installation smoke checks and required
for executable Bend contracts. Production Python code uses the standard library.
Schema tests also require `python3 -m pip install -r requirements-test.txt`.

| Command | Purpose |
|---|---|
| `doctor` | Probe local prerequisites and show the pin and patch count |
| `apply TARGET` | Preflight and install the exact stack into a clean pinned checkout |
| `verify TARGET` | Compare installed paths, modes and bytes against the delivery |
| `guide [router\|program\|prove]` | Print one compact local route |
| `task implement\|prove\|diagnose` | Read content through the accepted routing table |
| `help`, `--help` | Show commands, formats and exits |
| `version`, `--version` | Show management schema version and pinned Bend version |

No arguments print a concise quick start. All commands accept `--json` and
`--human`. Non-TTY stdout defaults to JSON; terminal stdout defaults to human
text. Supplying both is an error. Format and help flags may precede or follow
the command. Put flags before `--`; everything after it is a literal operand.

`--help` or `-h` before the delimiter displays help without executing a command,
even when its spelling or operands are malformed. Conflicting format flags still
fail. After the delimiter, help spellings are literal operands. `--version` is
a command alias, not an option attached to another command.

```sh
python3 b3nd12.py doctor --json
python3 b3nd12.py apply /path/to/clean/bend --json
python3 b3nd12.py verify --human -- /path/to/bend
python3 b3nd12.py guide prove --json
python3 b3nd12.py task diagnose --json
```

Read-only aliases are `check` for `verify`, `status` for `doctor`, `-h` for help,
and `-v` for version. Read-only command spelling ignores case and dash/underscore
separators. Normalized invocations set `corrected: true`; human mode writes the
accepted semantic command array to stderr. Paths, route names and their case
remain exact. Only the exact command `apply` may install. Unknown commands,
extra operands and ambiguous formats are rejected.

## JSON v1

Each invocation prints one JSON object on stdout. JSON-mode errors leave stderr
empty; subprocess diagnostics appear in error context. The published Draft
2020-12 schema is `spec/cli-v1.schema.json`. It specifies each command's required
result fields and types and rejects undeclared result fields.

```json
{"schema":"b3nd12.cli.v1","ok":true,"command":["verify","/path/to/bend"],"corrected":false,"result":{"pin":"e5a4c4cfe980c2e4e70571562efb5197fe27b2f4","files":25,"theory_unchanged":true,"delivery":"byte-identical","checks":["pin","scope","bytes","theory","whitespace"],"target":"/path/to/bend"},"error":null,"exit_code":0}
```

`command` contains the normalized command followed by literal operands, or null
when parsing fails. Quick start uses an empty array. This array represents
meaning; it is not shell text or replay-ready argv. To replay it, insert `--`
between the command and operands and choose the format separately:

```python
import subprocess
import sys

argv = [sys.executable, "b3nd12.py", command[0], "--json", "--", *command[1:]]
subprocess.run(argv, check=True)
```

Handle the empty quick-start array separately. Do not join operands into shell
text. For example, `["verify", "-checkout"]` needs the delimiter when replayed.
Successful apply and verify results identify the resolved absolute target;
JSON escaping preserves spaces, Unicode and newline characters.

`result` is an object on success and null on failure. Error objects contain
stable `code`, `message`, `context`, `correction`, and up to two `examples`.
Human and JSON modes preserve classification and exit status. Human success goes
to stdout; errors and correction notices go to stderr.

| Result | Fields |
|---|---|
| Quick start, help | `text` |
| Guide | `route`, `text` |
| Task | `task`, `text`, `reads`, `files` |
| Version | `version`, `bend_version`, `pin` |
| Doctor | `pin`, `tools`, `patches`, `runtime_checks`, `probes` |
| Verify | `pin`, `files`, `theory_unchanged`, `delivery`, `checks`, `target` |
| Apply | Verify fields plus `log` |

| Exit | Meaning | Representative codes |
|---:|---|---|
| 0 | Success | error is null |
| 1 | Resource missing | NOT_FOUND |
| 2 | Invalid or ambiguous intent | INVALID_COMMAND, INVALID_ARGUMENTS, INVALID_TARGET, INVALID_TASK, AMBIGUOUS_FORMAT |
| 3 | Configuration or prerequisite failure | WRONG_PIN, DIRTY_TARGET, MISSING_TOOL, BROKEN_TOOL, ROUTING_CONFIGURATION, GIT_FAILED, GIT_TIMEOUT, GIT_OUTPUT_LIMIT, CONFIGURATION |
| 4 | External operation limit | INSTALL_TIMEOUT, INSTALL_OUTPUT_LIMIT |
| 5 | Internal or delivery invariant failure | PATCH_SEQUENCE, FILE_SCOPE, CONTENT_MISMATCH, THEORY_CHANGED, FILE_MODE, INSTALL_FAILED, INTERNAL |

## Prerequisite probes and limits

Doctor reports each tool's discovered path and a probe with `status` and `detail`.
Statuses are `missing`, `broken`, `timeout`, `incompatible`, and `usable`. Git
must return a recognizable version; the shell must execute a printf command;
Bun must execute JavaScript that reads a Bun 1.x version. Each probe has a
two-second deadline and a 64 KiB combined stdout/stderr limit. Excess output is
reported as a broken probe. Missing or unusable Git or shell makes doctor fail.
Bun readiness controls `runtime_checks`, which is `available` or `unavailable`.

These probes establish limited operational behavior. They do not authenticate
executables or establish native, GPU, compiler-package or network readiness.
A program that deliberately spoofs probe results can pass. A usable Bun probe
does not replace the pinned-checker provenance checks in the acceptance runner.

Git operations have a 15-second deadline. The management apply subprocess has
a 90-second deadline. Both use a 1 MiB combined output limit. Exceeding a limit
terminates the subprocess group. An apply output-limit error includes truncated
`stdout` and `stderr`, `limit_bytes`, `observed_bytes`, and `target` in context.
A timeout includes captured diagnostics and the target. Neither condition rolls
back partial installation. Preserve the target for diagnosis before retrying.

## Compatibility and operational limits

`apply.sh TARGET` and `verify.sh TARGET` remain human-readable compatibility
entry points with their shell exit convention. The robot contract is provided
by `b3nd12.py`; Bend's installed diagnostic JSON Lines and graph schema remain
unchanged. Use the management entry point for stable statuses.

Installation requires exclusive access to the target while checking and writing.
The full stack and its resulting delivery are checked in a temporary index
before writes. Disk failure, concurrent mutation, or a failing post-write runtime
check can still leave the target modified. The command does not reset or delete
caller files. No transaction across filesystem writes or concurrent-install
guarantee is claimed. Installation preserves the target's real Git index.

Verification refuses extra tracked or untracked delivery changes. Ignored build
artifacts are outside the path-set check. It verifies source bytes, modes and
protected staged theory, not external toolchain trust or every backend. Read-only
management commands have no intended repository writes. Tests compare file bytes,
modes, Git control files and routing state around successful and failing calls.
Those tests use isolated repositories and do not establish safety against
concurrent writers or a malicious executable supplied through PATH.

The manager has no configuration file, authentication, pagination, or remote API.
Bun smoke commands set `BEND_NO_TELEMETRY=1`. Missing or broken Bun readiness does
not turn source verification into runtime-validation evidence.

## Accepted task routes

`task implement`, `task prove`, and `task diagnose` select content through
`accretion/routes.json`. The result's `reads` counts table/router/document loads
in the resolver; `files` records those paths. It does not count the management
wrapper's independent expected-content check.

Unknown task names return `INVALID_TASK`, exit 2, before routing data is read.
Malformed routing data, missing guide files, and content that differs from the
requested task's expected guide return `ROUTING_CONFIGURATION`, exit 3. Restore
the accepted table and declared guide files rather than changing the task name
to conceal broken routing state. The finite law is documented in ACCRETION.md.

## Contract checks

```sh
python3 -m pip install -r requirements-test.txt
python3 tests/cli_schema.py
python3 tests/cli.py /path/to/pinned/bend
python3 tests/cli_properties.py /path/to/pinned/bend
```

These tests use the full JSON Schema validator, malformed payload controls,
real terminal and pipe invocations, generated parser cases, hostile paths, and
repository snapshots. Every declared error code has human/JSON renderer parity
coverage. Some error families use controlled injection; that verifies rendering
and classification without claiming a real external outage. Separate noisy-child
checks exercise probe and installation output-limit handling.
