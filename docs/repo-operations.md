# Repository operations

Start with `./repo status`. It combines runtime diagnostics, Git changes, fresh
verification, and the existing task journal. JSON is the stable command output.
The task authority remains `system/roadmap.json` plus `state/events.jsonl`.
The capability inventory in `system/ergonomics.json` describes interfaces and
acceptance criteria; it cannot mark tasks solved.

## Commands

| Command | Purpose |
| --- | --- |
| `./repo doctor` | Inspect versions, upstream pin, and missing prerequisites |
| `./repo setup` | Locate or install pinned Bun, acquire upstream, apply recognized overlay |
| `./repo setup --target PATH --bun PATH` | Use explicit local dependencies |
| `./repo status` | Show current work, task attention, and verification freshness |
| `./repo tasks next` | Ask the existing journal for the next admissible task |
| `./repo tasks explain A06` | Read a task's acceptance criteria and source set |
| `./repo verify --scope decision` | Run the named component checks |
| `./repo verify` | Run all required checks under a total budget |
| `./repo stress` | Run the bounded proof and mutation campaign |
| `./repo impact` | Map changed paths to checks, with a conservative full-suite fallback |
| `./repo route GATE` | Read one small working set |
| `./repo explain EVIDENCE_STALE` | Resolve a stable decision code |
| `./repo demo` | Exercise producer, gate, commit, replay, and reconciliation in disposable Git |
| `./repo inspect-manifest FILE --compare OTHER` | Compare exact evaluation bindings |
| `./repo reconcile REPOSITORY MANIFEST` | Observe an uncertain commit without granting retry |
| `./repo catalog --check` | Validate capability IDs, references, and acceptance fields |
| `./repo render` | Regenerate the capability view |
| `./repo render --check` | Reject generated-view drift |
| `./repo publish --dry-run` | Prepare a verified tree and PR body without touching the caller's index |
| `./repo publish --head BRANCH` | Open a PR for an already-pushed, matching branch through gh |
| `./repo verify-remote COMMIT_SHA` | Fetch and compare exact published and local trees |
| `./repo host OWNER/REPO` | Inspect host controls through gh without changing them |
| `./repo watch PR --budget 120` | Wait within a fixed budget for remote checks |

Focused scopes are schema, decision, executor, proof, integration, and stress.
Decision and executor currently share one test module. Running the smaller scope
does not establish complete-repository verification.

Setup writes only recognized overlay destinations. An existing target at another
revision or with unknown edits stops with an explicit error. Its local config
retains the chosen target, runtime, installed hashes, and setup phase. Interrupted
installation can resume when remaining files match either the current overlay or
the recorded previous installation. It never resets a user's checkout.

`toolchain.json` is the runtime and budget authority. The composite CI action
reads it for Bun and Python versions. Git has a declared minimum. The actual
Python patch version, platform, Git version, Bun binary hash, and upstream source
snapshot are bound into verification records.

## Repository map

| Surface | Role |
| --- | --- |
| `overlay/`, `guide/agent/`, `evals/` | Exact upstream installation inputs |
| `patches/` | Review records; not executed as patch hunks |
| `pilot/` | Repository-local Bend models and proofs |
| `admission/` | Validated immutable public API and trusted producer adapter |
| `tools/admission_gate.py` | Existing decision kernel and local bare-Git executor |
| `tools/agent_system/`, `control.py` | Existing contracts, task journal, and benchmark authority |
| `repo`, `tools/repo_cli.py` | Setup, routing, verification, and delivery operations |
| `system/ergonomics.json` | Capability-to-check inventory |
| `pilot/admission/law-catalog.json` | Formal claims, witnesses, and negative coverage |
| `.repo/` | Ignored local config, bounded run logs, and publication packets |
| `evidence/`, `experiments/*results*` | Versioned historical evidence; not automatically current |

The compiled law catalog is the formal guarantee map. It contains nine laws over
54 finite context/outcome cases. The correspondence command executes those cases
in Bend and compares real authenticated Python gate requests. This is exhaustive
for that finite decision partition, not a proof of the Python implementation or
arbitrary application behavior. Other named claims are tested or remain external
assumptions. The admission documentation names their scope.

## Evidence and recovery

Verification retains each step's command, exit, duration, output hash, timeout,
and truncation state. Source hashes before and after must agree. Unexpected skips
and empty suites fail. A local pointer identifies the latest run; older runs are
not overwritten. Source, runtime, upstream, or log changes make a conclusion
stale. Record authenticity still assumes a trusted local controller.

An interrupted run retains its completed steps and RUNNING or INTERRUPTED state.
`./repo status` points to re-verification. It does not automatically replay a
possibly consequential command. The admission reconciler is read-only and never
authorizes retry from the absence of a marker.

To retain a reproduced command failure:

```sh
./repo capture --law pilot/admission/LAWS.bend --expected-exit 1 --contains BND110 CASE_ID -- bun upstream/bend2/main.ts pilot/admission/negative/pending_accepted.bend --json
```

The command requires both the expected exit and diagnostic, records source and
law identities, and refuses to overwrite an existing case. Confirming the output
does not establish that its semantic interpretation is correct; review that
connection before promoting the case into a required regression.

Mutation probes use named faults, checked source anchors, and a specified failed
test. Thirteen mutation results plus the complete 1,024-case decision partition
define the current stopping rule. Concurrent commits are exercised over eight
bounded races. There are no scheduled workers, paid model calls, or automatic
retries. Total verification and per-step limits are in toolchain.json; a failed
step stops the aggregate run before the maximum failure cap is reached.

New bulky logs remain in .repo or CI artifacts. Existing committed evidence is
preserved as history. Retain a small source-bound summary and minimal reproducer
in Git when it changes future checks; avoid copying every run into the source.

## Publication and host controls

Publication requires fresh complete local evidence. The temporary index includes
the worktree's publishable content without staging the real index. Review that
content before publishing. The CLI opens a PR through gh for a matching pushed
branch. When gh is unavailable, `publish --dry-run` supplies the tree, parent,
body file, and connected-GitHub operation sequence. The controlling session
performs those calls, then runs verify-remote against the resulting exact commit.

The watcher stops at its budget and reports pending checks without retrying them.
CI completion, merge, and deployment are separate outcomes. The host inspection
command is read-only; absence of access is unresolved, not proof that protection
exists. Workflow files alone cannot prevent direct or privileged writes.

Three CI jobs remain: the full repository job checks the integrated behavior and
retains bounded raw evidence; the ranked-overlay job exercises legacy CLI probes;
the agent-system job checks journal consistency and records its benchmark. They
share toolchain versions and support merge-group events. Required status checks
and authorized check sources need host configuration outside these files.

## Policy changes

Identify changes to laws, their imports, checkers, workflows, toolchain, evidence
producers, or authority as evaluation changes. Validate the proposal under the
currently adopted authority, show the old and new obligations, retain permitted
and forbidden witnesses, and rerun correspondence and negative checks. Do not
let proposed policy authorize its own installation. The journal's existing
roadmap is frozen once history exists; use its reviewed migration procedure
instead of editing history. No new policy-administration endpoint is enabled.

## Open boundaries

| Boundary | Consequence | Next probe and reopen trigger |
| --- | --- | --- |
| Producer isolation | A compromised trusted producer can sign a false claim | Deploy a producer without worker access to credentials, then attempt cross-boundary writes |
| Public-key verification | HMAC verification also holds signing authority | Add a public-key adapter if verifier compromise is in scope |
| Host enforcement | Direct writes can bypass the local gate | Inspect real rules, expected check sources, and bypass actors before merge automation |
| Live revocation | Policy snapshots are fixed during an invocation | Introduce a serialized authority store before concurrent policy rotation |
| Worker budgets | Local campaign bounds do not govern distributed workers | Add delegated budget accounting before remote worker scheduling |
| Crash durability | Lost acknowledgement tests do not establish power-loss behavior | Test actual storage failure before claiming durable external effects |
| Release provenance | Approved source is not a verified published artifact | Add build and release attestations before deployment integration |

These are external or future integrations, not completed controls. The ergonomic
commands expose their status and preserve uncertainty rather than invent access.
