# Supermodularity pilot

This pilot makes repair admission explicit and measures whether two changes help
each other. It belongs to the agent ergonomics overlay. It does not change
`bend2/bend.ts`, the language theory, or the checker.

## Six laws in this repository

| Law | Repository interpretation | Evidence needed |
| --- | --- | --- |
| Shared representation | Give admission inputs, outcomes, and interaction measurements explicit shapes. | Reject malformed inputs; check conversions where a conversion actually exists. |
| Executable evidence | Retain regression cases and their expected outcomes when admitting repairs. | A reproduced target failure, a passing repaired case, and retained prior evidence. |
| Explicit boundaries | State what repair admission consumes and what each outcome permits. | Accepted, rejected, and unresolved examples. |
| Reusable repair | A target repair must preserve previously passing cases in the declared suite. | Target resolution plus retained baseline passes; no claim about untested callers. |
| Verified composition | Check the complete admission path and its dependencies. | Local checks plus end-to-end rejection tests. |
| Measured interaction | Compare baseline, A, B, and A+B under the same evaluation. | Four scores, a declared metric and budget, and the interaction calculation. |

These are separate obligations. A typed interface does not prove that a component
implements its intended behavior. A passing example does not establish a law for
every input. A policy declaration does not establish that repository hosting
enforces it.

## Proof, measurement, and policy

**Bend proofs** establish propositions about the definitions actually imported by
the proof. The existing PROVE route requires `PROOF.bend` to import `LAWS.bend`
and excludes unsafe dependencies from trusted proof results. A proof over modeled
test outcomes cannot establish that an external test was run or that its report
is authentic.

The concrete model in `pilot/supermodularity/model.bend` has three Boolean
programs: constant false, identity, and constant true. The target input is true;
the regression input is false; the specification is identity. Only identity
satisfies both cases. Candidates also carry a retain/delete evidence choice, or
are explicitly unresolved. `LAWS.bend` states eight properties, and `PROOF.bend`
discharges them by enumerating this finite model. Negative fixtures claim that a
broken repair or evidence deletion is accepted; verification must reject them.

The model proves retained concrete cases, target correctness and regression
preservation for accepted candidates, one useful acceptance, three rejection
examples, and unresolved preservation. It does not formalize arbitrary patch
execution, the Python report validator, or all six design principles as universal
theorems.

**Executable checks** exercise implementations and reject known invalid cases.
They provide evidence within their tested scope. Keep at least one accepted case:
an implementation that rejects everything can satisfy many rejection properties
without admitting a useful repair.

**Measurements** compare concrete executions under a fixed evaluation. They need
the same cases, scoring rule, and resource budget for all four configurations.
They do not inherit universal validity from a proof of the arithmetic formula.

**Policy** determines which files may change, which checks are required, and who
may change acceptance criteria. Keep changes to the evaluation or admission rules
visible in review. A workflow file alone does not establish branch protection or
independent approval on the repository host.

## Acceptance examples

| Candidate | Required outcome | Reason |
| --- | --- | --- |
| Repair resolves its reproduced target, retains the case set and evaluation context, preserves baseline passes, and has no unresolved evidence | Accept within that declared scope | The admission obligations are met. |
| Repair leaves the reproduced target failing | Reject | The stated repair did not work. |
| Repair fixes the target but breaks a previously passing case | Reject | Target success does not discharge regression obligations. |
| Report deletes a prior case or changes the evaluation context | Reject | The before and after results no longer meet the comparison contract. |
| A required result remains unresolved | Preserve the unresolved result | Missing evidence cannot be converted to success. |
| Independent repair has no positive interaction with another change | Evaluate ordinary repair admission | Complementarity is not a prerequisite for useful repairs. |

The external gate checks supplied report consistency. It leaves its inputs
unchanged and returns hashes of the report and both snapshots. It cannot detect
forged case results or verify that supplied evidence digests name real artifacts.
Other pre-existing failures may remain: acceptance is scoped to the target and
preservation of baseline passes, not a claim that the whole suite is clean.

An unresolved result in either snapshot makes the verdict `UNRESOLVED`, even if
the later snapshot reports a pass. This conservative policy retains the earlier
gap; it does not infer that the missing evidence has been recovered.

## Reproduce the checks

From the overlay repository, with Python 3 and Bun on `PATH`:

```sh
./scripts/verify-supermodularity.sh /path/to/patched-bend-checkout
```

The target is the pinned upstream checkout after this overlay has been applied.
The verifier checks the upstream pin and checker boundary, checks the Bend proof,
and runs the Python tests. Consult the script for the complete current gate.
The pilot lives in this repository rather than being an upstream language change.

Run the report and interaction regression checks independently with:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Validate a supplied repair report with:

```sh
python3 tools/repair_gate.py REPORT.json
```

The report contains `schema_version: 1`, `target_case`, and `before` and `after`
snapshots. Each snapshot has `context` with `suite_sha256`, `config_sha256`, and
`environment_sha256`, plus a nonempty `cases` array. Each case has `id`, `status`,
and `evidence_sha256`. Digests are lowercase SHA256 strings; statuses are `PASS`,
`FAIL`, or `UNRESOLVED`. The tests contain executable report examples.

Exit status is 0 for acceptance, 1 for rejection or unresolved evidence, and 2
for an invalid report. JSON output includes the verdict and reasons.

## Interaction calculation

For a fixed evaluation with higher-is-better score `V`:

```text
interaction = V(A+B) + V(baseline) - V(A) - V(B)
```

A positive value supports complementarity for that pair under that evaluation.
Zero means additive effects. A negative value means overlap or interference;
the combination may still be useful if its total result is good.

The combined configuration must define how A and B compose. If applying A then B
differs from applying B then A, preserve that distinction and test the relevant
orders separately. Do not silently treat an ordered patch sequence as a set.

One positive result does not establish supermodularity of the whole project.
That stronger property concerns marginal effects across the relevant states and
combinations. Finite evaluation cases support only the recorded scope.

## Concrete repository repair

The original verifier compared the checker file with the Git index. A staged
checker modification therefore passed its guard. The repaired verifier requires
the pinned upstream revision and compares the working tree with that revision,
including staged changes.

`experiments/checker_repair.py` runs the original and repaired verifiers in an
isolated clone. The clean overlay and unstaged-modification probes pass before
and after. The staged-modification rejection probe fails before and passes after.
The resulting report is accepted by the external repair gate. Raw outputs,
source fingerprints, and the decision are in
`experiments/checker_repair.results.json`.

```sh
python3 experiments/checker_repair.py \
  --target /path/to/patched-bend-checkout \
  --output /tmp/checker-repair.json
```

The integrated verifier also checks two false acceptance proofs and a transitive
unsafe import. The unsafe fixture compiles, but reports one unsafe term; the same
zero-unsafe gate used for the real proof rejects that result.

## Verification record

The combined local verification completed with exit status 0 using Bun 1.2.22
and Python 3.12. Eight Bend laws checked with zero unsafe terms, both false proofs
were rejected, the unsafe-import check behaved as intended, and all 17 Python
tests passed without skips. A separate read-only reviewer also ran the combined
verification successfully. This record covers the pilot, not the upstream
cluster performance or GPU gates.

The remaining evidence-driven candidates are recorded in
`docs/supermodularity-next.md`; they are not implied results of this pilot.

## Recorded interaction

The included CLI experiment uses one task: obtain the missing-import repair hint
for an empty `PROOF.bend` beside `LAWS.bend`. Change A enables JSON diagnostics;
change B uses diagnostic explanation lookup through `--why`. Each arm has the
same maximum budget of two calls per case and 20 seconds per call. The score
records whether the task obtains the required hint. This is an integration probe,
not a measurement of developer productivity or proof-solving success.

```sh
python3 experiments/diagnostic_interaction.py \
  --runtime bun \
  --main /path/to/patched-bend-checkout/bend2/main.ts \
  --output experiments/diagnostic_interaction.results.json
```

The experiment records process outputs, exit codes, call and byte counts, and
source identities. Preserve a zero or negative interaction result; the experiment
does not need to demonstrate complementarity to be useful.

The recorded run in `experiments/diagnostic_interaction.results.json` scored 1 in
all four configurations, giving interaction 0. The baseline already supplied the
required hint. This run demonstrates no marginal success gain from either change
or their combination on this case.

To evaluate a separate four-record array with the same exact-arithmetic checker:

```sh
python3 tools/interaction.py records.json
```

Use the executable examples in `tests/test_interaction.py` for the record shape.
The evaluator checks comparison metadata and supplied scores; it does not attest
the underlying observations.

## Extension rule

Add another law when a concrete failure requires it. Supply its substantive
predicate, an accepted example, a rejected counterexample, and a reproducible
check. Keep unresolved obligations explicit. Stop extending the pilot when no
remaining distinction changes admission or a supported performance claim.
