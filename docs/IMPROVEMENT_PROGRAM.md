# B3ND12 improvement program

## Project model and scope

B3ND12 supplies agent ergonomics as nine ordered patches over Bend 2.0.9 at
`e5a4c4cfe980c2e4e70571562efb5197fe27b2f4`. Its users are agents and maintainers
who need compact guidance, stable diagnostics, proof routing, and dependency
slices. Four upstream files are modified; 21 files are added. The installed
path set is unchanged by this improvement program.

The user redirected this work from upstream Bend to B3ND12. The upstream
2.0.15 investigation remains useful evidence, but its unfinished compiler and
CLI changes are not portable patches for this pin. None is transplanted here.
The protected `bend2/bend.ts` remains unchanged. The management CLI owns
installation and verification; installed Bend retains its existing CLI.

Dependency map: `b3nd12.py` imports `stack.py`; apply delegates to `apply.sh`;
that script checks the complete stack in a temporary Git index, verifies its
result, applies ranks in order, and invokes `verify.sh`. Verification compares
installed bytes against the delivery files and checks the protected theory.
Bun, when available, supplies smoke checks. The Python tests use disposable
checkouts of a supplied local Git repository. No production service is needed.

External boundaries are Git subprocesses, filesystem permissions, an optional
Bun runtime, and upstream Bend's own foreign effects and package hub. The
management CLI does not fetch packages, reset targets, or contact a service.
The repository's HTML file is a static implementation ledger, not an app.

Build: none for the management CLI; Python 3.10+, Git, and a POSIX shell are
required. Test commands and observations appear in VERIFICATION.md. There is
no configured formatter, linter, deployment pipeline, or TypeScript build for
this repository. Native backend verification needs Clang and target hardware.

## Thirty evaluated candidates

A private search considered 100 distinct improvements across delivery integrity,
CLI use, proof guidance, diagnostics, compiler behavior, tests, documentation,
packaging, UI, security, and maintenance. These are the strongest 30 after
rejecting unsupported product expansion, duplicate interfaces, kernel edits,
and optimizations without materiality evidence. The ten selected candidates
were chosen across the full search and revised when the target changed.

V = expected value 1–5; C = confidence fraction; E = effort 1–5;
R = regression risk 1–5. Score = V × C / (E × R). These are judgments.
Maintenance is low unless stated. All admitted changes are reversible through
Git; tests use disposable targets. Dependencies are explicit below.

| # | Candidate / repository evidence | Users and workflows | V/C/E/R; score | Testability, interaction, cost and decision |
|---|---|---|---|---|
| 1 | Repair malformed diff headers and missing patch content | Every installation | 5/.99/2/1; 2.48 | Exact overlay oracle; low cost; selected |
| 2 | Restore ordered installation rather than overlay copying | Stack maintainers | 5/.99/2/2; 1.24 | Direct/installer comparison; depends 1; selected |
| 3 | Preflight all ranks before target writes | Users protecting checkouts | 5/.95/2/2; 1.19 | Corrupt late patch negative test; depends 2; selected |
| 4 | Compare installed files byte for byte | Maintainers trusting verify.sh | 5/.95/2/1; 2.38 | Tampered delivery and target tests; selected |
| 5 | Check staged and working theory against pinned bytes | Proof users | 5/.99/1/1; 4.95 | Stage edit then restore worktree; depends 4; selected |
| 6 | JSON management CLI with human override | Coding agents | 4/.95/3/2; .63 | Command contracts and real PTY; depends 4; selected |
| 7 | Stable errors and conservative command aliases | Automated recovery | 4/.90/2/2; .90 | Bad syntax, exact mutation spelling; depends 6; selected |
| 8 | Run installed Bend contracts locally | Contributors without cluster | 5/.95/2/1; 2.38 | Real parser, proof, interpreter and JS; selected |
| 9 | Reject missing ranks and delivery drift before writes | Stack authors | 5/.95/2/1; 2.38 | Missing rank, valid patch/reference mismatch; depends 3–4; selected |
| 10 | Versioned CLI schema and present-state docs | Agents and maintainers | 4/.95/2/1; 1.90 | Examples and contract assertions; depends 6–8; selected |
| 11 | Universal JSON inside installed Bend | Bend script consumers | 4/.70/5/4; .14 | Breaks diagnostic JSON Lines and gate consumers; medium cost; deferred |
| 12 | Reset compiler PROBES per compilation | Persistent compiler hosts | 4/.85/3/3; .38 | Measured on 2.0.15 only; changes delivered file scope; deferred |
| 13 | Fail-closed upstream ttok invocation | Upstream maintainers | 4/.90/2/2; .90 | Counter failure fixtures possible; upstream concern; deferred |
| 14 | Check Bun.build success in installed CLI | Page authors | 4/.85/2/3; .57 | Real failed bundle test feasible; changes existing overlay behavior; deferred |
| 15 | Eliminate installer-origin shell interpolation | Bend updater users | 4/.85/3/3; .38 | Local installer needed; upstream policy interaction; deferred |
| 16 | Proof-of-work worker error cleanup | Package publishers | 3/.75/3/3; .25 | Safe worker seam/hub contract absent; deferred |
| 17 | Local full upstream checkup runner | Contributors | 4/.80/3/2; .53 | Reuse oracle, do not fake backend pass; medium cost; deferred |
| 18 | Schema validator dependency | Contract maintainers | 2/.85/2/1; .85 | Adds dependency for small schema; optional validation useful; deferred |
| 19 | Pin-aware automatic upstream migration | Stack maintainers | 3/.40/5/5; .05 | Could silently change theory/API assumptions; high cost; rejected |
| 20 | Automatic dirty-target stash/reset | Installers | 2/.30/2/5; .06 | Destructive surprise; dominated by refusal; rejected |
| 21 | Automatic rollback after runtime smoke failure | Installers | 3/.60/4/4; .11 | Concurrent/user files make deletion unsafe; report retained target; deferred |
| 22 | Serialize installers with a checkout lock | Concurrent agents | 3/.65/3/3; .22 | Lock ownership/stale recovery complexity; no observed use; deferred |
| 23 | Package release and distribution installer | New users | 3/.50/4/3; .13 | Current clone-and-run sufficient; medium cost; deferred |
| 24 | Network telemetry for failures | Maintainers | 1/.25/4/5; .01 | Privacy and service burden without need; rejected |
| 25 | Accessibility overhaul of upstream demos | Demo users | 3/.75/3/3; .25 | Browser and target proofs unavailable; different repository; deferred |
| 26 | Rebuild static ledger as interactive dashboard | Readers | 1/.35/4/2; .04 | Little value over accurate table; rejected |
| 27 | Reorganize overlay and guides | Contributors | 2/.45/4/3; .08 | Paths are public installation inputs; no demonstrated benefit; rejected |
| 28 | Cache small source reads | Installer performance | 1/.50/2/2; .13 | No measured bottleneck; invalidation burden; rejected |
| 29 | Add checked proof cookbook | Proof authors | 4/.90/3/2; .60 | Existing moves plus checked examples; needs broader version-specific cases; deferred |
| 30 | Curate upstream performance and trust-boundary evidence | Skill authors | 4/.95/1/1; 3.80 | Existing report available; retain version labels; documented |

Candidates 1–10 form the admitted program. Closely related items share code and
are not counted as independent speedups or products.

## Ten actionable plans and outcomes

1. **Patch syntax and content, 99%.** Regenerate each ranked delta against the
   prior rank using the existing overlays and additive files as the oracle.
   Files: nine patches. Check all ranks directly, then via installer; final
   bytes and modes must agree. No new installed paths. Downside: larger diffs
   because the original patch bodies were incomplete. Implemented.
2. **Ordered installation, 99%.** Apply numeric ranks in `apply.sh`; remove
   overlay-copy installation. Keep the clean/pin guards and real index untouched.
   Test wrong pin, reapplication, and independent direct application. Depends
   on 1. Compatibility: requires a clean pinned checkout as documented. Implemented.
3. **Whole-stack preflight, 95%.** Apply into a temporary index and remove that
   index on exit. Corrupt the final rank and assert no target changes. Avoid a
   reset-based rollback. Files: apply.sh and tests. Depends on 2. Implemented.
4. **Exact verifier, 95%.** Share declared delivery discovery in `stack.py` and
   compare every installed byte plus path set, modes and whitespace. Tamper one
   installed file and one delivery reference. The verifier is stricter than the
   old grep checks; deliberate target modifications now fail. Implemented.
5. **Theory guard, 99%.** Compare working and staged theory with pinned bytes.
   Stage a kernel change and restore only its working copy; verification must
   still refuse it. No kernel edits are made. Depends on 4. Implemented.
6. **Management robot mode, 95%.** Add `b3nd12.py` using the standard library.
   Commands: doctor, apply, verify, guide, help, version. JSON defaults under
   redirection; `--human` selects text. Tests cover a real PTY and pipes.
   This wraps management operations only; Bend's existing JSON stays compatible.
   Depends on 4. Implemented.
7. **Error and alias contract, 90%.** Return stable code, message, context,
   correction and examples. Normalize only management read commands. Require
   exact `apply`; never normalize target paths. Reject ambiguous formats.
   Test aliases, extra operands, dash paths, and equal human/JSON status.
   Depends on 6. Implemented.
8. **Executable Bend contracts, 95%.** Use disposable 2.0.9 checkouts and actual
   Bun execution for routes, diagnostics, graph, proof import guard, valid proof,
   pure execution and generated JS. Files: tests/bend_contracts.py. No mocks.
   Native and GPU behavior remain outside this test's claim. Implemented.
9. **Preflight delivery integrity, 95%.** Require ranks 1–9 and compare the
   temporary index with all 25 expected files before applying. A valid but
   mismatched stack must fail without writes. Files: stack.py/apply.sh/tests.
   Requires Python before installation; no third-party runtime dependency.
   Depends on 3–4. Implemented.
10. **Documentation and schema, 95%.** Describe verified behavior in README,
    AGENTS, docs/CLI.md and spec/cli-v1.schema.json. Record limitations,
    coverage and failed experiments. Manual prose review; no automated prose
    substitution. Keep investigation status separate from rank completion.
    Depends on 6–8. Implemented.

## Premortem and revised decisions

| Failure after six months | Revision | Disposition |
|---|---|---|
| A 2.0.15 fix is applied to the 2.0.9 stack | Keep pin and exact 25-file oracle; retain upstream work as evidence | Compiler/installed-CLI changes deferred |
| JSON default breaks existing Bend consumers | Place new contract at management boundary; preserve installed Bend | Robot plan revised |
| A malformed final patch leaves earlier ranks installed | Whole-stack index preflight before any writes | Retained |
| Verification passes because a keyword remains | Compare exact expected bytes, paths and modes | Revised |
| Staged kernel edit escapes worktree-only diff | Compare both states with immutable pin | Retained |
| Typo causes unwanted installation | Only exact apply mutates; paths remain literal | Retained |
| Runtime smoke fails after writes | Report failure and preserve target; no destructive automatic reset | Rollback deferred |
| Two installers race after preflight | Document exclusive checkout ownership; no concurrency guarantee | Locking deferred |
| Native/GPU coverage is inferred from JS pass | Separate lanes in coverage matrix | Retained |
| Repository rearrangement breaks patch paths | No file moves; explicit no-move proposal | Reorganization rejected |
| Tests silently skip Bun | Runtime contract command fails clearly when Bun is absent | Revised |
| Machine-readable failure lacks debug context | Capture installer stderr and stable error context | Retained |

## Stub and placeholder audit

- Malformed unified-diff headers and omitted delivery bodies: production defect,
  repaired. The ordered installer had previously stopped at rank 1.
- Old keyword-only verify checks: incomplete verification, replaced by exact
  delivery checks.
- BND102: intentional reserved policy class. Upstream allows `@unsafe`; no new
  theory policy is invented.
- TODO in diagnostic messages: legitimate reporting of incomplete user proofs,
  not a production stub.
- `_template.sidecar.json`: intentional example/template, retained.
- Rank 10 no-change record: intentional theory boundary, retained.
- Existing proof move snippets: instructional fragments; not all are standalone
  proofs. The runtime test supplies a complete positive and negative example.
- Upstream bundler, worker cleanup and update concerns: unresolved production
  reliability opportunities in an adjacent versioned surface; not silently
  marked repaired here.
- Controlled malformed patches and corrupted checkouts in tests: legitimate
  failure injection, never production adapters.

## Performance and UI decisions

No performance change is admitted in the pinned delivery. The prior 2.0.15
report includes CPU, allocation and I/O evidence and 30-run latency, throughput
and RSS distributions. It cannot serve as a before/after baseline for 2.0.9.
The compiler PROBES finding remains version-specific and unresolved for this
stack. Extra exact verification does more integrity work; no speedup is claimed.
Runtime counters, cache rewrites, lock changes, array views and serialization
changes are deferred until the pin and oracle support a controlled experiment.

The static HTML ledger receives only accurate status text. Visual redesign has
no supported high-value journey here. No accessibility or rendered-browser
validation is claimed; graphical Bend demos are outside this repository.

## Remaining branches

Deferred: universal installed-Bend robot mode, compiler lifetime migration,
upstream bundler/update fixes, richer proof cookbook, concurrent installer lock,
and automatic post-write rollback. Reopen with a separately approved delivery
scope, version-specific oracle, and representative tests. Blocked: native/GPU
execution, upstream cluster gates and release-service integration. Rejected:
automatic dirty-target reset, telemetry, broad reorganization, and speculative
performance work. The push record is reported after the verified commits exist.
