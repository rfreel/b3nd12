# Six-worker backlog evaluation

Source under test: `1115e78b68b588b62ea5b24fc09bf06ff0c78f70`.
Platform: Linux, Python 3.12, Bun 1.4.2, pinned Bend 2.0.9.
The task was to create 100 substantial improvement tasks and test the repository
using the maximum available subagents. Six worker slots were available beside
the coordinator. All six were observed running concurrently during the audit.

## Procedure and budget

The first wave inspected separate surfaces and supplied evidence-backed candidate
tasks. Each worker had a read-only assignment, no delegation and a limit of two
test/probe commands. After `TODO_100.md` was written, the same six workers received
a second bounded assignment: review their task ranges and run one validation.
No worker changed repository source. The coordinator owned the proposal, review
corrections, structural guard and report.

The workers shared a filesystem and inherited context. Temporary installation
tests used their existing disposable checkouts. This test did not provide
separate security principals, independently trusted evaluators, held-out jobs,
or equal-cost serial controls. No concurrency speedup or fresh-agent productivity
claim follows from the results. Wall-time and token-cost comparisons were not
collected.

## Post-list validation results

Commands were run from the repository root. For the first three suites requiring
runtime discovery, PATH began with
`/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin`.
`../bend-pinned` is the pristine pinned checkout.

| Worker | Surface and command | Observed result |
|---|---|---|
| installation_audit | `python3 tests/patch_stack.py ../bend-pinned` | Exit 0; nine ordered patches, 25-file parity and refusal controls passed |
| cli_audit | `python3 tests/cli.py ../bend-pinned` | Exit 0; CLI contracts, PTY, installation, tamper and staged-theory controls passed |
| proof_audit | `python3 tests/bend_contracts.py ../bend-pinned` | Exit 0; installed routing, diagnostics, graph, proof and interpreted/emitted-JS behavior passed |
| controller_audit | `python3 tests/program.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun` | Exit 0; three productive replay trials, nine certificates and accounting/refusal controls passed |
| evidence_audit | `python3 tests/accretion.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun` | Exit 0; three rounds, seven rejection controls, task parity and changed-checker refusal passed |
| backlog_audit | Structural inspection, then `python3 tests/backlog.py` | First run found the not-yet-written report link. After repair, exit 0; all 100 IDs, references, source paths and frozen hashes passed |

The proof worker also checked the existing frozen spec-twin during the initial
audit with the pinned checker. It exited 0 with `All terms check.`. That was a
check of the existing theorem, not a new proof for the 100-task proposal.

## Confirmed findings

Two findings were independently reproduced by the coordinator in addition to
the worker's report:

1. **Protected file mode drift escapes verification.** In a disposable correctly
   installed checkout, set `core.filemode=false` and add executable bits to
   `bend2/bend.ts`. `python3 stack.py TARGET` exits 0. Direct mode checks cover
   delivered paths; remaining upstream mode detection relies on Git's summary.
   The theory bytes remain unchanged. T001 tracks the repair.
2. **Documented global help fails after a command.**
   `python3 b3nd12.py doctor --help --json` returns exit 2 with
   `INVALID_ARGUMENTS` and `Unknown option.` despite describing help as global.
   T041 tracks parser/documentation conformance.

Other findings are source-supported gaps, not new reproduced exploits: no
independent evidence verifier, no process isolation, missing total-run resource
bounds, mutable runtime inputs, incomplete command-specific JSON schemas, and
CI omission of the complete installation/CLI/Bend suites. Their respective
tasks carry acceptance obligations and scope prerequisites.

## Review corrections

- T008 now requires a retained terminal digest when claiming detection of deleted
  evidence. A valid truncated hash chain cannot reveal its missing suffix alone.
- T038 distinguishes unauthorized binary patches from binary encoding itself.
- T050 now covers path handling alone; diagnostic storage limits remain a
  separate concern.
- T024 names controller-issued authenticated identities instead of assuming an
  unspecified signing service.
- T097 requires authenticated reviewer authority and depends on principal
  separation; merely comparing two caller-supplied identity fields is insufficient.
- The missing report link found by structural review is supplied by this file.

## Reproduce the coordinator checks

```sh
python3 tests/backlog.py
git diff --check
```

The guard checks 100 unique open task IDs, resolved task references, priority and
scope metadata, source-path existence, the proposal digest and unchanged frozen
contract/law/routes. These are structural checks, not proof that each proposed
implementation is feasible or valuable.

The coordinator's mode-drift probe uses a shared clone in a temporary directory,
runs `apply.sh`, executes `git config core.filemode false`, adds the file's three
execute bits, and invokes `python3 stack.py TARGET`. It neither edits the pinned
checkout nor changes accepted repository routes.

## Outcome and limits

All five existing acceptance suites passed in the post-list wave. The backlog
contains 100 open tasks with explicit acceptance criteria. No proposed task is
marked complete merely because a worker reviewed it or baseline tests passed.
T001 and T041 are confirmed defects still awaiting repair. Other items remain
local proposals, contract-review work or infrastructure-dependent work as marked.

The executable TODO, routing law, accepted routes, frozen sum example and
25-file delivery remain unchanged. T100 cannot run until T001–T099 have accepted
completion receipts. A new list does not authorize its own activation.
