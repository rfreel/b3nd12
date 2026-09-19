# Remaining local acceptance work

This review distinguishes executable coverage from proposed work. These findings
cover T056, T060, T085, T087, T089, T090 and T099. They do not authorize changes to
the frozen routing contract, installed file scope or language kernel.

| Task | Current evidence | Remaining acceptance boundary |
|---|---|---|
| T056 | `tests/controller_model.py` compares the real replay controller with an independent state model over every reachable outcome prefix and terminal trace within the frozen six-attempt budget. | Checker observations are simulated. The test does not exhaust arbitrary candidate bytes. Actual checker behavior has separate coverage in `tests/program.py`, `tests/routing_domain.py` and `tests/law_conjuncts.py`. |
| T060 | The sealed sum example has an exact source oracle and real checker coverage in `tests/spec_twin.py`. | No backend counterexample reducer exists. A planted native or GPU mismatch cannot be called reproduced when those backends have not run. A JavaScript-only reducer would need an explicit backend label and a separate executable fixture. |
| T085 | `tests/smoke.py` runs installation in a disposable Bend clone and distinguishes absent, failing and working Bun. CLI suites exercise command examples directly. | These suites do not extract and execute every published quick start from a clean B3ND12 checkout. A complete test needs an explicit example inventory, substitution rules for placeholder paths and documented prerequisite handling. |
| T087 | `tests/ci_contract.py` verifies suite ordering and failure propagation in the workflow shell block. | The workflow does not yet upload bounded failure evidence containing command, exit, source identity and diagnostics. Local orchestration checks do not establish hosted artifact retention. |
| T089 | Test dependencies are acquired separately in CI before acceptance commands run. | No prepared acceptance run has passed under an independently enforced network-denial boundary. Disabling telemetry or replacing Python networking calls would not cover Bun, Git and other subprocesses. |
| T090 | Existing suites inject scope, parser, law, evidence-translation and accounting faults within their declared fixtures. `tests/translation.py` reports its eight mutations and surviving cases explicitly. | There is no unified catalog proving that each listed defect is killed by its designated suite. Reusing one fixture as both defect producer and expected oracle would weaken the result. |
| T099 | Current documents distinguish the finite routing experiment, delivery and backend limits. | There is no complete claim-to-test inventory with executable stale-example and unsupported-completion controls. A prose review alone does not satisfy that acceptance criterion. |

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
