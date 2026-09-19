# Autoresearch pilot

The first campaign simplifies the existing finite repair-model proofs while
holding LAWS.bend and model.bend fixed. The assistant proposes candidates; a
bounded Python runner checks them with the repository's pinned Bend compiler.
This adapts the experiment loop from https://github.com/karpathy/autoresearch.
It does not depend on that project's GPU training implementation.

## Run

With Bun 1.2.22 on PATH and the overlay applied to the pinned Bend checkout:

```sh
python3 experiments/autoresearch/run.py \
  --target /path/to/patched-bend \
  --output /path/to/new-results-directory
```

The output directory must not exist. Each run preserves a JSONL ledger, a
report with source hashes and raw diagnostics, and the selected PROOF.bend.
The runner does not edit the pilot or merge changes. The existing pilot CI
also runs the campaign and preserves its outputs as a workflow artifact.

## First result

The baseline contains 21 explicit case branches. The candidate contains 15,
a reduction of 28.6%. It combines deletion cases that do not depend on the
proposed program. All eight original laws still check with zero unsafe terms.

The five paired measurements in results/second had median checking times of
0.411 seconds for the baseline and 0.457 seconds for the candidate. This run
does not establish a speed improvement. The accepted result is a smaller proof
case split, not a faster checker or a stronger theorem.

The first runner attempt stopped because it expected compiler errors on stdout.
Bend emitted the expected missing-proof error on stderr. Both streams are now
parsed, and a regression test rejects stderr errors even alongside a stdout
success event. The failed attempt's ledger is retained under results/first.

Only one structural candidate was explored. The result is a working first
campaign, not evidence that proof simplification has been exhausted.

## Boundary

The fixed laws cover the existing finite repair model. They do not certify
external measurements, GitHub access controls, or arbitrary application code.
The runner checks compiler identity, proof signatures, imports, diagnostics,
and protected-file hashes. These checks detect accidental drift; they are not
an operating-system security boundary against a hostile worker with filesystem
access. This pilot runs supervised candidate files in one process sequence.

Before introducing an unattended worker, give it a separate filesystem and
process identity, expose only candidate submission, and keep the evaluator
and result storage outside its write access. That stage is not implemented here.
