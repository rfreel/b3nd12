Historical investigation: this report concerns upstream Bend 2.0.15. Referenced
raw profiles, scripts and logs are in the separately delivered evidence packet,
not this repository. It does not change the B3ND12 2.0.9 pin or certify its
performance. See IMPROVEMENT_PROGRAM.md for the active repository scope.

# Bend 2 investigation for skill authoring

## Decision

Build a version-pinned, evidence-backed Bend skill with a short entry point and task-specific references. Keep language proofs, compiler correctness, runtime behavior, and performance measurements as separate claims. Do not turn the supplied screenshot's synthesis into unconditional guarantees.

This investigation made **no production source changes**. It prepared architecture notes, measured baselines, profiles, an opportunity ranking, a checked proof example, and reusable probes. It did not produce or install a `SKILL.md`, certify the compiler, or establish a performance improvement.

**Frozen source:** `bendlang/bend` commit `31d263391762c59e735d09712e14013edd719166`, version 2.0.15, fetched September 19, 2026. HEAD moved between the earlier inquiry and this investigation; this fetched commit is the baseline. The earlier b3nd12 repair and its Bend 2.0.9 checkout are separate and unchanged.

## 1. Source and investigation coverage

Read in full at the frozen revision: root `AGENTS.md`, root `README.md`, `guide/GUIDE.md`, and `bend2/main.ts`. Inspected the test oracle and runner, benchmark protocol, cluster helper, compiler pipeline, layout and ownership machinery, native allocator and scheduler, JS event loop, channel implementation, representative effects, and the theory/formalization boundary. CPU profiles guided follow-up reading in normalization, higher-order term construction, checking, and emission. This is an architectural and performance investigation, not a line-by-line formal audit of every file, every demo, or the Lean proof development.

Primary references, all pinned:

- [Repository instructions](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/AGENTS.md)
- [README and explicit limitations](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/README.md)
- [Language guide](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/guide/GUIDE.md)
- [CLI and module loader](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/bend2/main.ts)
- [Compiler and runtimes](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/bend2/comp.ts)
- [Protected checker and interpreter](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/bend2/bend.ts)
- [Formalization and its stated differences](https://github.com/bendlang/bend/blob/31d263391762c59e735d09712e14013edd719166/bend2/bend.lean)

The packet records source hashes in `source-environment.json`. The source worktree was clean after investigation. `bend2/bend.ts` was never edited.

## 2. Purpose and architecture

Bend combines an affine dependent language, executable programs, laws expressed as types, explicit proofs, and C/Metal/CUDA/JavaScript backends. Its intended workflow is to specify important properties, implement code, and check proofs against those properties. Successful checking establishes what the encoded claims and trusted components support; it cannot ensure that a user's complete intent was captured.

| Component | Role and connections | Skill consequence |
|---|---|---|
| `main.ts` | Parses CLI options; loads a Book; enforces neighboring LAWS import for PROOF; validates; rejects open obligations; interprets pure main or compiles IO to JS; emits JS/C or invokes Clang | Distinguish check, interpret, emit, build, and run. They exercise different machinery |
| `bend.ts` | Syntax, parser, import resolution, terms, normalization, equality/comparison, usage and termination checks, elaboration | Read for diagnosis. Repository instructions prohibit editing this file |
| `base.bend` | Datatypes, operations, laws, templates, and paired C/JS effect declarations | Discover actual names and signatures from this revision; do not invent library APIs |
| `comp.ts`, TypeScript portion | Builds reachable definitions; raises bodies; determines layouts; erases irrelevant arguments; tracks borrowing/sharing; emits code and tables | Compiler optimization needs an emitted-output oracle and runtime checks, beyond a source proof |
| `comp.ts`, C template | Packed words, explicit allocation/reclamation, reference counts, task rings, CPU pool, GPU execution, event loop, channels | Allocation, contention, and GPU transfer costs require backend-specific profiles |
| `comp.ts`, JS template | JS values, BigInt Nat, native strings, trampolines, a sequential runtime, effect loop and channels | JS timings cannot establish CPU-pool or GPU speedups |
| `bend2/effs/*.{c,js}` | Host effects, handle ownership, byte/text conversion, blocking or nonblocking work | Host code and failures are part of the trust and equivalence boundary |
| `bend.lean` | A model and metatheory of the core with documented mismatches and exclusions | Do not describe it as a verified implementation of the compiler/runtime |
| `gates/test.ts` | Reads `#|` goldens, checks/interprets, builds JS/native lanes, compares outputs on the cluster | Reuse its oracle; negative tests and unsupported printable values require its classification |
| `gates/perf.ts` | Runtime/checker workloads and hardware-specific reference measurements | Preserve flags, outputs, hardware provenance, cold/warm distinctions, and failure handling |

### Execution paths

`book_load` resolves paths, prevents cycles and inconsistent namespaces, loads imports, parses, and constructs the Book. It already deduplicates imports by real path within a load. `book_valid` processes declaration order and checks types and bodies, writing elaborated terms. A law's declaration and later definition are not interchangeable; prefix visibility matters.

A CLI call with no `main` checks only. A pure `main` is normalized and printed by the interpreter. An IO `main` is compiled to JS and run through the JS effect loop, even without `-o`. `-o name.js` emits JS; `-o name.c` emits C; a native output invokes Clang and may also build a GPU program. Treating the default CLI path as native execution would invalidate a benchmark.

The compiler discovers reachable definitions in `carb_book`, maintaining source/dependency summaries. `compile_book` emits repeatedly until its monotone ownership, hotness, and static-value facts stabilize. It then filters reachable segments, distinguishes host and device reachability, constructs tables, and fills the C runtime template. JS emission shares analyses but has different code and value representations.

The native runtime already uses per-lane allocation caches and class-based recycling. Shared values can incur atomic reference-count operations. CPU workers coordinate through atomics, a mutex, and condition variables. Channels have bounded buffers and park senders when full. A single event loop handles effects, with helper threads for blocking work. These mechanisms rule out blanket claims that no locks, no contention, or no backpressure exist.

An array has one source-level owner, but its runtime operations do not all avoid copies. Current `blk_half` and `blk_node` allocate and copy; recursive decomposition can copy O(n log n) words. Indexed get/set and structural decomposition need separate cost guidance. The `array_split_join` test comment still describes in-place halves; the current implementation is the authority for the cost claim.

## 3. What ran

Environment: Linux x86-64, AMD EPYC 9V74 host identification, nine visible logical CPUs, cgroup quota equivalent to eight CPUs, 20 GiB memory limit, Bun 1.4.2, Node 24.19.0. CPU topology is virtualized. There is no claim that these measurements match an M4 or GPU.

| Check | Result | Limit |
|---|---|---|
| Official `bun gates/test.ts` | BLOCKED at cluster connection | Bastion multiplex socket was denied; no official gate success |
| Local upstream `--checkup` with upstream reader/judge | **1,313/1,313 goldens matched** | Checker/interpreter/default IO lane only; native and standalone JS lanes not certified |
| Native matrix-multiply build | BLOCKED: Clang unavailable | No native runtime latency, allocation, or contention profile |
| Syscall tracing with `strace` | BLOCKED: ptrace denied | No kernel-level I/O profile |
| Four workload baselines | 30 measured observations each; no failures | Fresh process with warm page cache, not persistent service performance |
| CPU profiles | Four Bun sampled profiles | One profiled observation per workload; percentages are candidate evidence |
| Bun heap profiles | Four retained-heap snapshots | They contained no allocation trace tree or sample history |
| Allocation profiles | Two Node/V8 sampled allocation profiles | Separate host runtime; not Bun allocation percentages |
| Filesystem API profiles | Two Node probes of unchanged Bend APIs | Exclude module loading, native/FFI calls, and output-file writes |
| Spec twin | Universal equality proof passed; incorrect fast version rejected | Source-language proof, not a backend correctness theorem |
| Repeated compiler probe | 64 identical C outputs; growing retained probe state | Long-lived-process evidence, not a measured latency regression |

The aggregate `--checkup` command exits 1 because expected negative tests exist. The oracle judged all 1,313 outputs correctly; equating its exit code with an unexpected failure would be a harness bug.

Two adapter mistakes were resolved before accepting this result: a direct CLI adapter did not reproduce `--checkup`'s exit markers/reporting and merged streams incorrectly; an initial aggregate used absolute import paths that `cli_checkup` joined incorrectly. The successful run uses relative paths and the upstream `--checkup` behavior with combined output. Raw exploratory records remain labeled in the packet.

The full generated-JS lexer runtime was stopped after a 20-second pilot limit. That censored observation is not a latency percentile or throughput result. It was not repeatedly retried. Dependency installation also stopped after the package manager hit a permissions restriction; no sandbox setting was weakened.

## 4. Baseline first

One untimed warmup preceded 30 serial fresh-process runs per workload. Telemetry was disabled. No observations were removed. Latency is parent-observed elapsed time; throughput is completed jobs divided by their summed elapsed time. Peak memory is per-child Linux `wait4.ru_maxrss`, not virtual memory reservation or cumulative allocation.

| Unchanged workload | p50 ms | p95 ms | p99 ms | Jobs/s | Maximum RSS MiB |
|---|---:|---:|---:|---:|---:|
| Check `defs_12800` | 738.72 | 784.50 | 825.64 | 1.350 | 339.93 |
| Check `proofs_3200` | 1,977.61 | 2,104.89 | 2,125.75 | 0.499 | 1,036.00 |
| Emit C for `tree-matmul` | 171.85 | 191.16 | 194.35 | 5.795 | 95.29 |
| Emit JS for `lexer` | 149.12 | 162.87 | 167.97 | 6.679 | 90.89 |

Percentiles use nearest rank. **At n=30, p99 is the maximum observation and is not a reliable population-tail estimate.** These are local baselines, not speedups and not comparisons with upstream's Apple reference times.

Every repeated emitted artifact had the same hash:

- C: `a2abbdd1971ffdeaeb13a98c86e8d92b22e33ca2228bf0ab0aa3b3233fe5f756`
- JS: `0cde0d26296c96e2bfdf3a7bfc7e8e15b23389e233f65582b8f15d3a0e4fb283`

Exact argument arrays, environment, warmups, individual times, stdout, stderr, exit status, and memory appear in `baseline.json`. `measure.py` reproduces the measurement procedure.

## 5. Profile before proposing

Self-time shares are time-delta-weighted samples, not inclusive totals or fractions of all possible Bend workloads. Runtime `map` and anonymous frames remain unattributed rather than being assigned to a convenient hypothesis.

| Workload | Five largest self-time entries |
|---|---|
| Definitions | `term_check` 7.92%; `term_higher` 6.43%; `book_valid` 6.34%; `term_infer` 5.81%; unnamed frame 5.71% |
| Proofs | `term_wnf` 12.17%; `term_higher` 11.84%; `term_infer` 6.66%; `map` 6.60%; `term_check` 5.63% |
| C emission | `term_higher` 11.41%; `map` 6.99%; `term_wnf` 4.51%; anonymous frame 3.68%; `parse_lookup` 2.93% |
| JS emission | `term_wnf` 9.40%; `map` 7.03%; `term_higher` 6.95%; `ADT` 4.11%; anonymous frame 4.08% |

Exclusive samples attributed to protected `bend.ts` total 87.05% for definitions and 86.74% for proofs. For C emission, 48.21% are in `bend.ts` and 25.30% in `comp.ts`; for JS emission, 66.25% and 12.14%, respectively. Calling a kernel function from compiler code can contribute to kernel self time, so these are file attribution, not a complete phase decomposition.

Inclusive C profile attribution puts `compile_book` at 37.26% and its emission pass at 26.86%. Inclusive JS attribution puts `js_lib` at 19.40% and `carb_book` at 12.24%. Inclusive figures overlap and must not be added. The short C profile has only 413 samples; small ranks can change on repetition.

The supplemental Node allocation probe estimates 88,995,744 allocated bytes for C emission and 3,096,880,640 for the proof workload. Leading allocation sites:

| Node probe | Largest sampled allocation sites |
|---|---|
| C emission | `term_higher` 15.15%; `term_wnf` 8.33%; `Ctr` 3.95%; `map` 3.77%; `push` 3.18% |
| Proofs | `term_wnf` 15.70%; `term_higher` 14.21%; `term_infer` 10.45%; `term_compare` 5.21%; `term_check` 3.77% |

These are sampled allocation estimates including collected objects, not retained heap or exact allocation counts. They reinforce the need to separate host runtime, allocation pressure, and peak memory.

The Node C-emission I/O probe recorded four `readFileSync` calls totaling 69,607 bytes and about 0.19 ms. The program and Base were each read once; `print.c` was read twice across compiler passes. This is a repeated read, but the measured work is too small to justify a performance change here. No N+1 network issue was measured. The failed Bun preload probe recorded zero calls, so it is excluded from I/O conclusions.

## 6. Concrete retained-state finding

`comp.ts` declares `PROBES` once at module scope. `probe()` appends to it, and `probe_of()` indexes it. Neither `memo_gc()` nor the compilation-entry cache reset clears it.

A read-only counter exported from a temporary compiler copy established:

| Completed C emissions | Retained probe entries |
|---:|---:|
| 0 | 1 |
| 1 | 744 |
| 16 | 11,889 |
| 32 | 23,777 |
| 64 | 47,553 |

For this workload, count = 1 + 743 × compilations. All 64 hashes match the uninstrumented baseline. In the uninstrumented run, reported heap use after requested full GC increased from 14,660,534 bytes after the first emission to 19,947,269 after the 64th. That heap difference includes other retained state and is not wholly attributed to PROBES.

**Conclusion:** compilation retains an ever-growing probe registry in a long-lived process. **Unresolved:** safe reclamation boundaries, total user impact, and eventual latency/GC effects. The first compile took 46.75 ms and the 64th 16.89 ms, so this experiment does not demonstrate increasing latency; warmup is material.

A one-line `PROBES.length = 0` is not justified. The sentinel, probe-indexed maps, closures, type analyses, and mixed C/JS entry points must be accounted for before reuse of IDs. The future skill should ask for an A/B/A repeated-compilation test that alternates input programs and backends, checks exact outputs, and tests errors as well as successful builds.

## 7. Opportunity matrix

No optimization diff is proposed for application in this preparation task. The following ranks **future experiments**, not proven speedups. Impact is an ordinal 1–5 estimate for the named surface; confidence is 0–1 confidence in useful benefit; effort is 1–5. Score = impact × confidence / effort. These judgments are explicit and revisable, not measured percentages.

| Rank | Candidate and surface | I | C | E | Score | Admission state |
|---|---|---:|---:|---:|---:|---|
| 1 | Bound compiler probe lifetime in persistent tools | 3 | .85 | 2 | 1.28 | Retention measured; equivalence boundary unresolved |
| 2 | Replace repeated reachability scans and duplicate-name scans with indexes | 1 | .70 | 1 | .70 | Source pattern exists; material latency benefit not measured |
| 3 | Reduce layout serialization/reconstruction in C emission | 2 | .45 | 2 | .45 | Emitter is material; this particular cost needs a direct profile |
| 4 | Remove JS event-loop quadratic wait-list membership scans | 3 | .40 | 3 | .40 | Clear source mechanism; high-concurrency workload not measured |
| 5 | Reduce recursive array split/join copying | 4 | .30 | 5 | .24 | Source cost documented; native/GPU evidence and ownership proof absent |
| 6 | Reuse checked Base across independent tool requests | 3 | .30 | 5 | .18 | Existing checkup precedent; freshness and isolation risks remain |

Kernel normalization/checking dominates the checker workloads, but edits to that file are outside the repository's permitted surface. A skill must report that constraint rather than choose a lower-impact change and imply it fixes the dominant cost.

### Conditional proof obligations

These are proof sketches for possible approaches, not completed correctness proofs:

1. **Probe lifetime:** show a bijection between old and new probe IDs within each compilation, preserving equality, sentinel identity, usage counts, and emitted names. Establish that no live object from a previous compilation can be reached after reset. If either condition fails, reset is inadmissible.
2. **Indexes:** construct a first-occurrence map in original traversal order so it returns exactly the element returned by `find`. For duplicate checking, visit names in order and report the first repeated name exactly as `indexOf` does. Preserve emitted ordering and error text. Exact emitted bytes are the preferred oracle.
3. **Layouts:** a structural comparison must inspect every field currently represented by serialization, including ordering and offsets. Cache keys need immutable layouts or invalidation when `lay_pack` adjusts offsets. A hash alone is not equality; verify collisions structurally. Admit only after profiling this path.
4. **JS wait lists:** preserve each original wait object's identity, registration order, duplicate descriptors, readiness bits, timer rounding, re-parking, and the order of callbacks. An indexed single pass can remove scans, but cannot change wakeup order or collapse two waits on the same descriptor.
5. **Array views/copies:** prove disjoint ranges, one owner, exact element order, refcount behavior for boxed elements, and identical bounds/error behavior across native and GPU lanes. Zero-copy views change the representation and allocation lifetime; they are not a trivial equivalence.
6. **Base reuse:** a cached seed must be observationally equivalent to freshly loading and validating the exact Base plus effects. Invalidate on content/compiler changes; clone mutable Book state; preserve declaration visibility, errors, and module namespaces. Existing `book_seed` is evidence of one controlled use, not proof of a general persistent cache.

## 8. How the requested patterns map to this project

| Pattern | Grounded assessment |
|---|---|
| N+1 query/fetch elimination | Imports already use a real-path seen map; package files fetch concurrently. Profile cold hub loads separately. No measured N+1 bottleneck here |
| Zero-copy, buffer reuse, scatter/gather | Relevant to array halves and UTF-8 effect boundaries. Ownership, partial writes, EAGAIN, and error reporting are observable |
| Serialization costs | `lay_eq`, specialization keys, and fixed-point fact snapshots use JSON. Measure separately before replacing |
| Bounded queues/backpressure | Channels already have bounded buffers. Helper jobs and event-loop activations have different lifetimes; do not add a cap that silently drops work |
| Sharding/striped locks | Allocator already has per-lane caches, but the bank has a shared lock. Requires native contention evidence |
| Memoization/invalidation | Many compiler caches already exist. The measured probe retention makes lifecycle discipline more urgent than more caching |
| Dynamic programming | Fixed-point ownership/fork analyses could use dependency worklists. Preserve the least fixed point and deterministic emission |
| Lazy/deferred work | Compiler bodies are elaborated on demand for reachable definitions. Deferring validation would alter error behavior and needs a separate contract |
| Streaming/chunking | Could reduce source/buffer peaks, but parser spans, hashes, diagnostics, and effect boundaries constrain it; unmeasured |
| Precomputation/tables | Compiler already emits static images and lookup tables. Avoid duplicating machinery or exploding generated size |
| Index versus scan | Relevant in reachability, duplicate names, layouts, and JS wait lists; distinguish large-list workloads from small defaults |
| Binary search | Useful only for sorted numeric or timer data with preserved tie ordering; no measured admission here |
| Two-pointer/sliding window | No demonstrated core hotspot needing these techniques |
| Prefix sums | Import-span offsets repeatedly split prefixes in `book_load`; a running offset is a plausible linear alternative, but it is in protected `bend.ts` and unprofiled on import-heavy input |

## 9. Equivalence oracle and guardrails

Every future experiment should declare the input universe and its observables before editing:

- Exact successful values, stdout/stderr bytes, exit status, diagnostics and source locations.
- Proof acceptance/refusal, unresolved laws, TODO behavior, import cycles, namespace identity, and the neighboring LAWS guard.
- U32 wrapping, bounded runtime Nat, F32 rounding/signed-zero/NaN behavior, Unicode replacement rules, and array indexing.
- Affine handle ownership, file/socket operations, channel close/deadlock behavior, and observable ordering.
- Backend and build flags, immutable input hashes, compiler revision, and the precise generated-output oracle.

Use byte-identical emitted C/JS for analyses that should leave emission untouched. For an intentional emitter change, use a documented source-level relation plus differential backend execution, boundary/property cases, and emitted-code inspection. Passing tests is finite evidence, not proof for all inputs. F32 arithmetic and concurrent effects need their own contracts; algebraic reassociation or callback reordering is not automatically safe.

`benchmark_guard.py` supplies a provisional local guard: no output differences or failed runs, p50 at most 1.10× baseline, p95 at most 1.15×, peak RSS at most 1.10×. It does not gate p99 at n=30. It passed a self-comparison and rejected a deliberately doubled p50. These tolerances need calibration with unchanged controls; they do not establish an improvement and do not replace the upstream gate. Hardware identity, source/input hashes, command flags and quota also require review.

The upstream benchmark gate uses its own 1.15× hardware-specific references. `gates/_run.ts` also enforces a 30-second total gate cap. Do not raise those limits, overwrite reference pins, suppress a failing lane, or relabel a blocked platform as passed.

## 10. Assessment of the supplied skill ideas

The screenshot is a design proposal and reported prior result. Its private skill path, validator output, seven skeletons, and 1,336-test claim were not available to inspect. This checkout has 1,313 Bend test files; counts and compatibility belong to a revision.

| Supplied idea | Decision for the future skill |
|---|---|
| Spec, implementation, and executors collapse into one checker-verified artifact | **Reject as a guarantee.** Laws/proofs are checked in the language. JS and native emitters, foreign effects, and device execution remain separate trust boundaries |
| Affinity buys consistency, no GC, no contention, in-place arrays and GPU execution together | **Qualify.** Usage and termination rules support the theory; native memory uses explicit reclamation/refcounts; JS uses its host GC. Shared atomics and locks exist. Array structural operations copy |
| Write an obvious spec and fast twin, prove equality | **Keep with scope.** The included example proves equality for every Nat and rejects a wrong implementation. It does not validate arbitrary compiler diffs or foreign effects |
| Compute finite facts before proving | **Keep with bounds.** Closed reduction can discharge concrete claims; exhaustive finite enumeration requires domain completeness. Neither substitutes for a universal proof over an unbounded domain |
| Laws are durable; code and proofs can be regenerated | **Keep as workflow discipline.** Preserve the declared law and its provenance. When a request conflicts with it, expose the conflict rather than silently delivering a different feature |
| Theory/runtime/compiler references | **Keep as routed references.** Attach source revision, trust boundary, and applicability to each |
| Checked cookbook and skeletons | **Keep only after executable checks.** Each needs a positive case, a relevant failing mutation, supported lane, expected result, and source hash |
| Decision ledger from all tests | **Refine.** Map tests to distinctions, including negative tests, stale comments, and backend exclusions. Do not count tests as independent theorems |
| Ownership audit tool | **Keep as a static lens.** The packet includes a call-site census. It cannot establish hotness, dynamic operation counts, or performance |
| Interleaved speedup benchmark | **Keep.** Build once for runtime measurements; separate compilation measurements; alternate before/after/mode order; verify outputs and binary hashes |
| Generated Base API index | **Keep.** Packet includes 472 declaration starts, source lines and hash. It is navigation, not a substitute for type checking |
| Preserve every section and grow to 29 references | **Do not use size as a quality criterion.** Keep material that changes a decision, enables a probe, or prevents a known failure; consolidate duplicates |

## 11. Proposed shape of the later skill

A small entry point should ask which task is being performed and load one route:

| Route | Required content | Completion evidence |
|---|---|---|
| Program | Current syntax, Base lookup, quantities, execution modes | Program checks and correct selected-lane output |
| Prove | LAWS/PROOF boundary, live/dead distinction, induction/rewrite examples | No open obligations; positive proof and relevant failing mutation |
| Measure | Frozen inputs, hardware/toolchain, warm/cold definitions, exact commands | Raw distributions, profiles and outputs, no unsupported speedup claim |
| Optimize compiler | Emission pipeline, cache lifecycle, ordering, stable names | One lever; proof obligation; exact emission or stronger replacement oracle |
| Optimize runtime | Ownership, copying, sharing, scheduler and backend differences | Real target profiles; deterministic outputs and effect invariants |
| Effects | Paired host implementations, handles, buffering and failure behavior | Both supported host lanes checked; unsupported lanes explicit |

Store reusable objects rather than session narration: source manifest, task contract, workload manifest, golden-output set, profile interpretation, opportunity ledger, equivalence obligations, experiment verdict and reopen condition. Useful statuses are VERIFIED, REJECTED, UNRESOLVED and BLOCKED, each tied to evidence.

For this task, the next skill-writing input is ready. The remaining performance branches are explicit: native/GPU profiling is blocked; exact probe reclamation is unresolved; small scan/serialization opportunities lack a materiality measurement. No production optimization is admitted by this packet.
