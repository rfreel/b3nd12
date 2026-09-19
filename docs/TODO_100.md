# B3ND12: 100 high-value engineering tasks

Proposal baseline: commit `1115e78b68b588b62ea5b24fc09bf06ff0c78f70`.
All boxes are open. This backlog is separate from the sealed `accretion/TODO.json`;
the existing Bend law does not certify these tasks. Reviews and passing baseline
tests do not count as implementation completion.

Priority means expected value given current evidence: P0 closes a demonstrated
defect or an acceptance boundary; P1 develops reliability or measurable utility;
P2 investigates an improvement whose benefit remains unproved. Difficulty comes
from the acceptance obligation, not a requirement to produce complicated code.
Task numbers are stable identifiers, not estimates of effort or a rigid schedule.

L means repository-local work within the existing delivery scope. C means a new
contract or behavior decision must be reviewed before implementation. X means
external tooling, credentials, hardware or a separate execution principal is
required. C and X items remain proposals until those prerequisites are resolved.
Preserve the 25 installed files, pinned checker, current law and frozen sum spec.

Each completed task needs an exact source revision, executable evidence and an
independent review. Record those in a separate completion ledger. Preserve failed
experiments and unresolved branches. Never check a box merely because its design
sounds plausible. Performance tasks follow one causal lever per experiment.

## Acceptance integrity

Evidence: `stack.py`, `accretion/program.py`, `accretion/run.py`,
`tests/program.py`; confirmed findings in `PARALLEL_TEST.md`.

- [ ] **T001 · P0 · L · Close upstream mode-verification gaps.** Refuse executable-bit drift on theory and untouched tracked files with `core.filemode=false`; ordinary installed trees still pass.
- [ ] **T002 · P0 · L · Distinguish a valid negative proof from a broken checker.** Crash, timeout, missing certificate and genuine law refusal produce distinct outcomes; a malfunction cannot satisfy the refusal control.
- [ ] **T003 · P0 · C · Require an independently approved runtime identity.** A substituted executable that prints the expected checker sentence is refused before evaluation; the approved binary passes. Record the trust source.
- [ ] **T004 · P0 · C · Execute a verified immutable compiler snapshot.** Mutate compiler files between validation and execution in a disposable fixture; the executed snapshot and receipt remain identical or evaluation stops.
- [ ] **T005 · P0 · L · Enforce evidence-directory boundaries.** Absolute, relative and symlink paths into the repository are refused before any write; valid external paths still work.
- [ ] **T006 · P0 · L · Bound every child process.** Hung Git, version-query and checker processes terminate with their descendants within declared timeouts and leave stage-specific evidence.
- [ ] **T007 · P0 · C · Enforce a whole-run resource budget.** Attempts, elapsed time, memory and output limits survive slow or noisy children; budget exhaustion preserves accepted state and records the consumed allowance.
- [ ] **T008 · P0 · L · Build an independent receipt verifier.** Reconstruct verdicts and completions from saved inputs; changed, deleted, duplicated and reordered records fail verification against a retained terminal digest. Do not import controller decision functions.
- [ ] **T009 · P0 · L · Bind the manifest to the evidence chain.** Changing toolchain, contract, source or input identity invalidates verification against a retained terminal digest. Depends on T008.
- [ ] **T010 · P0 · L · Exhaust the finite routing domain.** Enumerate all 64 semantic route tables against declared baselines; independent expectations and real Bend certificates agree for every case.

## Evidence durability and recovery

Evidence: `accretion/program.py`, `docs/FROZEN_TODO.md`, `tests/program.py`.

- [ ] **T011 · P0 · L · Define crash-consistent evidence commits.** Kill the writer between every artifact and ledger write; a fresh verifier labels each bundle complete, incomplete or invalid without false success. Depends on T008.
- [ ] **T012 · P1 · L · Retain failed observation streams.** Spawn failure, signal and timeout receipts preserve command, stage, available stdout/stderr and termination reason without inventing a checker verdict.
- [ ] **T013 · P1 · C · Resume only verified committed prefixes.** Interrupted runs retain spent attempts, prevent duplicate credit and refuse altered prefixes; a resume cannot reset the budget. Depends on T007 and T011.
- [ ] **T014 · P1 · L · Reconstruct expired proof books.** A fresh checkout rebuilds every accepted temporary book from an exported packet and the pin; regenerated inputs and certificates match.
- [ ] **T015 · P1 · L · Make summaries independently derivable.** Recompute final metrics, completed outcomes and stop reasons solely from verified records; modified summaries are rejected. Depends on T008.
- [ ] **T016 · P1 · L · Verify evidence export and import.** Round-trip bundles between clean directories while preserving hashes and references; reject path traversal, symlink escape and missing artifacts.
- [ ] **T017 · P1 · C · Version evidence formats without reinterpretation.** Old fixtures retain their original meaning; unknown major versions fail explicitly; migration preserves source receipts and supplies comparison evidence.
- [ ] **T018 · P1 · L · Bound evidence growth.** Large diagnostics and rejected candidates respect fixed storage limits with explicit truncation metadata; required reproduction inputs remain recoverable.
- [ ] **T019 · P1 · L · Test filesystem write failures.** Disk-full, permission and short-write fixtures cannot leave a summary that an independent verifier accepts as completed. Depends on T011.
- [ ] **T020 · P1 · X · Retain an authenticated terminal receipt externally.** Whole-log replacement and truncation fail against an external trusted root; original exports verify after the worker workspace is lost. Depends on T008 and T009.

## Worker authority and concurrency

Evidence: trust limits in `docs/ACCRETION.md` and `docs/FROZEN_TODO.md`;
`accretion/run.py` documents exclusive promotion rather than concurrent compare-and-swap.

- [ ] **T021 · P0 · X · Separate worker and controller principals.** Worker attempts to alter controller code, law, oracle, ledger, accepted state and credentials all fail at the operating-system boundary; legitimate proposals still work.
- [ ] **T022 · P0 · C/X · Restrict promotion to controller authority.** No worker interface can install bytes; only a controller can promote the exact evaluated candidate under a reviewed policy. Depends on T021.
- [ ] **T023 · P0 · C · Make promotion atomic under contention.** Two candidates from the same baseline yield exactly one promotion and one stale-baseline refusal; neither loses unrelated state. Depends on T022.
- [ ] **T024 · P1 · C · Make retries idempotent.** Repeated submission of the same authenticated controller-issued run/candidate identity cannot duplicate promotion or completion; changed content under a reused identity is rejected. Depends on T023.
- [ ] **T025 · P1 · C/X · Bound the worker filesystem view.** A candidate can access its declared inputs and output area only; tests attempt parent-path, symlink and shared-cache escapes. Depends on T021.
- [ ] **T026 · P1 · C/X · Constrain worker environment and network access.** Tool injection and undeclared outbound requests are refused; permitted dependencies remain reproducible. Record the allowed capabilities rather than relying on prompt text.
- [ ] **T027 · P1 · C · Define worker leases and reassignment.** Expired workers cannot complete reassigned work; delayed results preserve provenance without earning duplicate credit. Depends on T024.
- [ ] **T028 · P1 · C · Add bounded queue admission.** At the configured capacity, new work receives an explicit refusal or wait state; stress tests demonstrate bounded memory and no dropped accepted jobs.
- [ ] **T029 · P1 · C · Propagate cancellation through the worker tree.** Cancelling a run stops descendants, releases resources and leaves unfinished tasks distinguishable from failures; already accepted work remains intact.
- [ ] **T030 · P0 · C · Separate successor proposal from activation structurally.** Proposal artifacts cannot become active contracts through any worker route; activation binds a separately approved digest and authority identity. Depends on T021 and T022.

## Exact installation and verification

Evidence: `stack.py`, `apply.sh`, `verify.sh`, `tests/patch_stack.py` and
the declared 25-file scope in `AGENTS.md`.

- [ ] **T031 · P0 · L · Freeze the installation manifest explicitly.** Adding a file matching a discovery glob cannot silently expand delivery; exact paths, modes and roles must match the reviewed manifest.
- [ ] **T032 · P0 · C · Enforce staged-index integrity.** Specify allowed index state and reject staged non-theory drift without changing the caller's staging; fixtures cover both staged and working-tree discrepancies.
- [ ] **T033 · P1 · C · Make post-preflight installation failures recoverable.** Inject failure at every rank; produce either exact original or exact installed state under a reviewed rollback policy that preserves unrelated files.
- [ ] **T034 · P1 · C · Enforce exclusive installation.** Concurrent installers cannot interleave writes; stale-lock recovery verifies ownership and target state rather than deleting arbitrary locks.
- [ ] **T035 · P0 · L · Install only preflighted patch bytes.** Changing a patch between validation and application either causes refusal before target writes or has no effect on the sealed bytes installed.
- [ ] **T036 · P1 · L · Refuse filesystem obstructions safely.** Ignored colliding files, symlink parents and inaccessible paths cannot cause unrelated data loss; failure reports identify the obstruction and preserve caller content.
- [ ] **T037 · P1 · L · Test ambient Git configuration boundaries.** An isolated matrix of index variables, filters, attributes, ignored paths and linked worktrees has explicit supported or refused outcomes with no cross-checkout writes.
- [ ] **T038 · P1 · L · Mutation-test patch admission.** Deterministic path-escape, duplicate-rank, unauthorized binary-patch, symlink, deletion and out-of-scope fixtures are refused before writes; legal stack bytes still install.
- [ ] **T039 · P1 · L · Emit replayable installation receipts.** Bind pin, ordered patch hashes, manifest, verifier and tool identities; reproduce the same delivered tree from a receipt in a fresh nonshared checkout.
- [ ] **T040 · P1 · L · Separate static verification from runtime smoke readiness.** Hung or absent Bun has an explicit runtime status without obscuring static byte verification; scripts and JSON consumers agree on the result.

## Agent-facing CLI contracts

Evidence: `b3nd12.py`, `spec/cli-v1.schema.json`, `tests/cli.py`, `docs/CLI.md`.

- [ ] **T041 · P0 · L · Make global-help semantics consistent.** Test help before and after every command, missing operands and literal `--` paths; requesting help never starts installation and agrees with documentation.
- [ ] **T042 · P1 · L · Define command-specific result schemas.** Every success command has required fields and types; malformed command results fail validation while all existing valid outputs pass.
- [ ] **T043 · P1 · L · Enforce full schema validation in tests.** Check every success/error fixture against the published schema; deliberate violations of each declared constraint fail. Depends on T042.
- [ ] **T044 · P1 · L · Property-test parser normalization.** Generated argument cases preserve literal paths, canonicalization idempotence and exact-only mutation syntax; rejected forms perform no actions.
- [ ] **T045 · P1 · L · Prove human and JSON classification parity.** Every error family has the same semantic outcome and exit code in both modes, with the documented stdout/stderr separation.
- [ ] **T046 · P1 · L · Expand real-terminal conformance.** Exercise every read-only command and representative failures through PTYs, pipes and redirected stderr; explicit output overrides take precedence consistently.
- [ ] **T047 · P1 · C · Define bootstrap-error output.** Missing or corrupt startup configuration and import failures produce the reviewed machine-readable failure or a documented bootstrap exception; none masquerades as success.
- [ ] **T048 · P1 · L · Distinguish invalid tasks from broken routing state.** Bad user task names remain argument errors; malformed accepted tables and invalid route content become configuration or invariant errors with actionable corrections.
- [ ] **T049 · P1 · L · Prove read-only commands preserve repository state.** Snapshot files, modes, index, HEAD, configuration and routes around successful and failing invocations; the declared read-only surfaces remain unchanged.
- [ ] **T050 · P1 · L · Harden path round trips.** Unicode, newline, leading-dash, symlink and non-root inputs preserve intended identity without option injection; both output formats retain an unambiguous representation of the actual target.

## Proof and backend assurance

Evidence: `accretion/LAWS.bend`, `accretion/PROOF.bend`,
`examples/frozen-spec-twin/`, `tests/bend_contracts.py`.

- [ ] **T051 · P0 · L · Challenge every acceptance-law conjunct.** Disposable books independently falsify preservation, per-task nonregression, strict gain and size; the real checker refuses each without changing the original law.
- [ ] **T052 · P1 · L · Mutation-test evidence translation.** Flip generated booleans, totals, size and field bindings; an independent oracle catches every declared mutation or reports surviving cases explicitly.
- [ ] **T053 · P1 · L · Enforce the spec-twin seal automatically.** Hash and write-set checks reject isolated changes to law, seq, pow2 and main meaning while permitting the declared sum/proof surface.
- [ ] **T054 · P1 · C · Validate transitive proof-import policy.** A reviewed parser rejects unsafe annotations, unauthorized host imports and path escape across reachable project imports; the official proof passes.
- [ ] **T055 · P1 · C · Formalize TODO accounting in a separate Bend book.** Prove bounded attempts, unique completion, dependency order and absent successor authority; preserve the existing finite routing law unchanged.
- [ ] **T056 · P1 · L · Differential-test the controller state machine.** Exhaust bounded verdict traces against an independent small model; budget, completion and stop decisions agree for every enumerated trace.
- [ ] **T057 · P1 · X · Verify the frozen example on native CPU.** A pinned native toolchain prints `2147450880`; two additional depth/index pairs agree with the sequential oracle and all frozen hashes remain intact.
- [ ] **T058 · P1 · X · Compare supported execution backends.** A sealed bounded Nat corpus agrees across interpretation, emitted JavaScript and native execution; disagreements are minimized and retained without weakening the oracle.
- [ ] **T059 · P2 · X · Validate GPU execution after proof acceptance.** Bind compiler, binary, device, backend and flags; expected output and independent discriminators agree before reporting any timing.
- [ ] **T060 · P1 · L · Retain and minimize backend counterexamples.** A planted backend-output mismatch produces a smaller reproducible failing input, exact tool identities and a regression fixture without editing the spec.

## Evidence-driven performance work

Evidence: measured verifier cost in `docs/VERIFICATION.md`, constructed-read
limits in `docs/ACCRETION.md`, and subprocess-heavy `stack.py`.

- [ ] **T061 · P1 · L · Make the management benchmark reproducible from checkout.** A versioned entry point emits raw observations, source/tool identities and commands without depending on untracked scratch scripts.
- [ ] **T062 · P1 · C · Establish timing-noise controls.** Repeated unchanged A/A trials define variability and a minimum detectable benefit before candidate timings are inspected; retain every run and exclusion rule.
- [ ] **T063 · P1 · C · Capture representative verifier CPU, allocation and I/O profiles.** Attribute the measured workload across Python and Git without treating pipe wait as Git CPU time; identify the top measured costs.
- [ ] **T064 · P2 · C · Test batched Git object reads.** Change only subprocess/object-read batching; adversarial verification verdicts stay identical and controlled direct plus end-to-end measurements establish benefit or rejection.
- [ ] **T065 · P2 · C · Test reuse of immutable tree metadata within one verification.** Remove repeated decoding only after profiling supports it; changed target contents remain visible and equivalent verdicts pass. Do not add cross-run caches.
- [ ] **T066 · P2 · C · Test bounded streaming of large Git results.** Peak memory falls on declared large inputs while every scope, mode and byte mismatch produces the same verdict; report any latency cost.
- [ ] **T067 · P1 · C · Establish cold and warm verification baselines.** Separate startup, filesystem-cache and steady-state observations with identical correctness checks; never pool incompatible populations into one speedup.
- [ ] **T068 · P1 · C · Measure concurrent verification saturation.** Sweep a bounded worker count and record throughput, tail latency, memory and failures; identify where contention outweighs concurrency.
- [ ] **T069 · P1 · C · Add statistically justified regression thresholds.** Thresholds derived from controls detect a planted material slowdown without an unacceptable false-alarm rate across clean runs. Depends on T062.
- [ ] **T070 · P1 · C · Evaluate whole-task cost after local improvements.** Include setup, retries, validation and failed candidates; distinguish a direct-lever gain from an unmeasured or negative user-visible effect.

## Fresh-agent and multiagent evaluation

Evidence: `evals/`, agent packs, `docs/ACCRETION.md`, and limitations of the
six-worker test in `PARALLEL_TEST.md`. Every item in this group needs a new study
contract; access to genuinely fresh workers and cost telemetry must be verified.

- [ ] **T071 · P1 · C · Freeze representative agent tasks.** Cover implementation, proof repair, diagnosis and patch repair using objective outcomes, protected files and fixed budgets; reject tasks without an executable oracle.
- [ ] **T072 · P1 · C · Hold out evaluation tasks from optimization.** Separate development and sealed evaluation sets, record exposure, and demonstrate that candidate authors cannot read held-out answers.
- [ ] **T073 · P1 · C · Use the strongest existing routing control.** Compare direct-guide access, fallback routing and task routes on identical jobs; preserve null or negative results instead of choosing only the weakest baseline.
- [ ] **T074 · P1 · C/X · Run randomized paired fresh-agent trials.** Fix model/tool identities, rotate conditions, retain all outcomes and report correctness, elapsed time and total usage with uncertainty. Depends on T071–T073.
- [ ] **T075 · P1 · C/X · Measure history-free handoff.** A fresh worker reconstructs source, remaining budget, unresolved branches and admissible action solely from the durable packet; grade against an independent oracle.
- [ ] **T076 · P1 · C/X · Compare serial and six-worker review at equal budgets.** The same hidden defect corpus yields detection, false-positive, time and cost results; report differences without attributing them solely to worker count.
- [ ] **T077 · P1 · C/X · Measure correlated reviewer misses.** Compare shared-context and isolated-context review on hidden defects; report joint misses and uncertainty rather than counting agreement as independence.
- [ ] **T078 · P1 · C · Challenge reviewers with planted acceptance defects.** Seed wrong laws, weakened oracles, forged metrics and scope expansion in disposable fixtures; score detection and false accusations separately.
- [ ] **T079 · P1 · C · Test instruction injection through repository data.** Untrusted comments and evidence text cannot redirect workers into changing protected state; legitimate task outputs remain correct under the same fixtures.
- [ ] **T080 · P1 · C/X · Account for all agent experiment costs.** Bind worker identities to retries, cancelled work, tool calls and usage; no successful-run-only cost reporting. Reconcile totals against available provider records.

## CI and reproducibility

Evidence: `.github/workflows/verify.yml`, five existing acceptance suites,
supported-platform assumptions and skipped checks in `docs/VERIFICATION.md`.

- [ ] **T081 · P0 · L · Run every existing acceptance suite in CI.** Patch-stack, CLI, Bend, accretion and TODO suites run against the exact pin; deliberately failing each suite makes the job fail.
- [ ] **T082 · P1 · C/X · Pin the CI execution environment.** Record immutable action identities, Bun/Python/Git versions and runner image; reproduce acceptance on two clean workers without an implicit latest-version upgrade.
- [ ] **T083 · P1 · X · Establish Linux/macOS conformance.** Supported Python/Git versions, executable modes, PTYs and paths with spaces produce equivalent documented results on both operating systems.
- [ ] **T084 · P1 · L · Remove shared-clone assumptions from one acceptance lane.** A fresh nonshared clone installs and verifies without local object-store access; evidence identifies the acquisition source and exact commit.
- [ ] **T085 · P1 · L · Test clean-checkout documentation commands.** Execute declared quick starts and examples in disposable environments; detect missing prerequisites and stale flags without changing user repositories.
- [ ] **T086 · P1 · L · Add runtime-readiness probes to doctor.** Broken, nonexecuting and incompatible tools are distinguished from usable tools; reported readiness predicts which validation commands can actually run.
- [ ] **T087 · P1 · L · Publish bounded CI evidence on failures.** Failed jobs retain exact command, exit, source identity and diagnostic artifacts within storage limits; secrets and unrelated environment values are excluded.
- [ ] **T088 · P1 · C/X · Verify downloaded toolchain provenance.** Record approved origins and digests; altered downloads fail before execution, and unavailable provenance is reported rather than silently trusted.
- [ ] **T089 · P1 · L · Detect unexpected network dependence.** A prepared offline acceptance run passes without provider calls; dependency acquisition is a separately reported phase with explicit required access.
- [ ] **T090 · P1 · L · Test the tests with controlled mutations.** A catalog of known scope, oracle, parser, proof and accounting defects is detected by the relevant suites; report missed mutations and repair weak oracles.

## Governance, handoff and successor quality

Evidence: repository scope rules, historical/current document separation,
`accretion/TODO.json`, successor output and current absence of a general scheduler.

- [ ] **T091 · P1 · C · Define typed task outcomes and completion receipts.** Task IDs bind objective, oracle, dependencies, budget and source; evidence cannot be reassigned to a different task with a similar title.
- [ ] **T092 · P1 · C · Validate dependency graphs before admission.** Cycles, missing prerequisites and impossible budgets are refused; independent tasks remain schedulable without inventing completion states.
- [ ] **T093 · P1 · C · Prevent duplicate value credit across tasks.** Shared improvements and repeated evidence have one declared benefit attribution; overlapping tasks cannot multiply the same measured gain.
- [ ] **T094 · P1 · C · Preserve unresolved branches with executable reopen conditions.** Each unresolved outcome names the missing discriminator and trigger; scheduler tests neither silently close it nor retry it without changed evidence.
- [ ] **T095 · P1 · C · Re-rank work from accepted evidence.** A measured bottleneck change updates candidate ordering while frozen objectives and acceptance tests remain unchanged; dominated candidates retain rejection reasons.
- [ ] **T096 · P1 · C · Prove prior capabilities survive later accepted changes.** Re-run the protected capability corpus before advancement; a new local gain cannot mask regression on an earlier completed outcome.
- [ ] **T097 · P1 · C/X · Separate reviewer authority from candidate authorship.** The controller authenticates distinct author and reviewer identities; self-review cannot authorize a task requiring independent acceptance. Reject missing, forged and conflicting identities. Depends on T021.
- [ ] **T098 · P1 · C · Test rollback of an accepted improvement.** A reviewed rollback restores the prior source and capability results, preserves the original evidence and prevents reversed gains from remaining credited.
- [ ] **T099 · P1 · L · Keep operating documentation synchronized with verified behavior.** Map every capability claim to a current test and limit; intentionally stale examples and unsupported completion claims are caught during review.
- [ ] **T100 · P1 · C · Generate the next measurable improvement list last.** Only after T001–T099 have accepted completion receipts, produce a deduplicated successor proposal with each item's baseline, falsifier, oracle, budget, dependency and parent digest. An empty supported frontier produces exhaustion. Generation never activates the proposal.

T100 is blocked while any earlier item is open. If scope or infrastructure makes
the full list infeasible, record that fact and request a separately reviewed
revision; do not weaken completion criteria or silently treat deferral as success.
The text digest in `TODO_100.sha256` identifies this proposal version. It is a
change detector, not an external authority or permission to activate the list.
