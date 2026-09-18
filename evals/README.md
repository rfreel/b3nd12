# Eval sidecars

A sidecar stores residue from an eval run. It is not a second source of truth for the Bend program.

Naming
`evals/name.bend` may have `evals/name.sidecar.json`.

Write only facts produced by a run or by an explicit comparison:
- stable diagnostic ids
- graph roots actually inspected
- proof moves actually tried
- residual goals or distinctions still open
- irreversible boundaries discovered
- evidence locations
- the cheapest next discriminator
- a concrete reopen trigger

Never convert an unresolved distinction into a decision to make the file look complete.

Status meanings
SOLVED: target closed by the current evidence.
ROBUST: target remains closed under the recorded relevant perturbations.
BRANCHED: materially different live outcomes remain.
UNRESOLVED: a distinction can change the result and has not been discriminated.
BLOCKED: the next discriminator cannot currently be executed.
