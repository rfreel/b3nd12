# Remaining local acceptance work

This review distinguishes executable coverage from proposed work. These findings
cover T056, T060, T085, T087, T089, T090 and T099. They do not authorize changes to
the frozen routing contract, installed file scope or language kernel.

| Task | Current evidence | Remaining acceptance boundary |
|---|---|---|
| T056 | `tests/controller_model.py` compares the real replay controller with an independent state model over every reachable outcome prefix and terminal trace within the frozen six-attempt budget. | Checker observations are simulated. The test does not exhaust arbitrary candidate bytes. Actual checker behavior has separate coverage in `tests/program.py`, `tests/routing_domain.py` and `tests/law_conjuncts.py`. |
| T060 | The sealed sum example has an exact source oracle and real checker coverage in `tests/spec_twin.py`; `tests/native_backend.py` compares a bounded corpus across interpreter, JavaScript and native CPU. | No counterexample reducer with a retained mismatch fixture exists. A passing backend corpus does not establish reduction behavior. GPU execution remains unavailable. |
| T085 | `spec/documentation-examples.json` inventories 19 fenced blocks across README, CLI, installation and evidence documentation. `tests/documentation.py` validates fingerprints and the published JSON schema example, then runs declared recipes in disposable checkouts. | Dependency acquisition is excluded. Blocks assigned to existing suites retain those suites as their execution evidence. New documents require explicit inventory expansion; this is not a claim over every historical example. |
| T087 | `tests/ci_contract.py` verifies suite ordering and failure propagation in the workflow shell block. | The workflow does not yet upload bounded failure evidence containing command, exit, source identity and diagnostics. Local orchestration checks do not establish hosted artifact retention. |
| T089 | `offline.py` installs inherited Linux x86-64 syscall denial. Actual Python, Git and Bun network attempts fail; 26 ordinary checks and the native corpus pass under the repaired guard. CI separates acquisition from prepared checks. | The guard does not isolate filesystem access, other agents, existing external helpers or promotion authority. Anonymous local IPC remains available for subprocess streams. |
| T090 | `spec/mutation-catalog.json` names controlled defect families and their detecting suites. `tests/mutation_catalog.py` runs those suites and records misses; translation tests retain their declared checker-surviving cases. | The catalog covers named injected defects, not every possible mutation. A passing family suite is evidence only for its declared fixtures. |
| T099 | The documentation inventory detects changed examples and a planted unsupported runtime-status claim; operating prose is manually reviewed. | Arbitrary capability claims do not have a complete semantic claim-to-test oracle. T099 remains open; the example inventory does not satisfy the whole criterion. |

## Controller model coverage

The differential controller test enumerates four observation classes: productive,
neutral, rejected and unresolved. It visits every prefix through six attempts and
stops extending a branch when the third productive outcome completes the workload
or an unresolved observation stops execution. Every live prefix also tests
candidate exhaustion. This covers the complete reachable tree for those four
observation classes under the frozen controller policy.

For each trace the test compares spent attempts, final read total, completed
outcomes, stop reason, successor presence and receipt verdicts. The real controller
and evidence writer run in disposable directories. The simulated checker
observations isolate state transitions; they are not Bend certificates and are
not offered to the offline evidence verifier as real runs.

```sh
python3 tests/controller_model.py /path/to/pinned/bend /path/to/bun
```

Candidate parsing, the distinction between different process failures and the
truth of emitted Bend propositions remain separate test surfaces. Exhausting this
outcome tree does not establish those properties.
