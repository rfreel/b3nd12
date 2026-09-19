# Improve the next agent's environment

## Frozen contract

The executable law is accretion/LAWS.bend. For a fixed set of three tasks,
accept a candidate only when:

1. Every returned document is byte-identical to the independent expected document.
2. No task incurs more file reads than before.
3. The total number of reads strictly decreases.
4. The candidate routing table is at most 4096 bytes.

The tasks are implement, prove and diagnose. Their expected documents are
PROGRAM.md, PROVE.md and diagnostics.json from the existing agent delivery.
The law checks finite evidence about this set. It does not quantify over unseen
tasks or prove improvement for arbitrary agents.

## Execution and trust boundaries

`environment.py` resolves tasks from a data-only JSON routing table. It records
each actual read: the table, the router when a direct entry is absent, and the
selected document. There is no model-provided action count. Expected content is
read independently from the declared task-to-document oracle.

`run.py` measures baseline and candidate bytes, emits Evidence.bend into a
private temporary directory, copies the fixed law and proof template, and invokes
the pinned Bend checker. The certificate is accepted only for exit 0, exactly
`All terms check.` on stdout, and empty stderr. The proof uses conversion over
the recorded finite values. There are no unsafe annotations or proof holes.

Bend proves the predicate over those values. The Python evaluator is responsible
for producing truthful values, binding them to candidate hashes, and selecting
the correct compiler. It checks pinned kernel, Base and CLI bytes. The demo seals
its law, evaluator, proof template, upstream pin and expected documents in memory
and checks them before each promotion. The JSON report carries those hashes.

Candidate data cannot supply executable code, paths outside the declared files,
unknown tasks, duplicate task keys, or its own evidence. This restricts the
candidate interface. It is not an operating-system security boundary: a process
that can edit the controller can bypass it. Hostile-agent enforcement requires a
separate controller principal, read-only evaluator mounts, and exclusive promotion
authority. That deployment is not implemented or claimed here.

## Three rounds

The controlled baseline has an empty routing table. Each missing entry falls
back through the router. Each accepted round adds one direct entry:

| Round | Added route | Reads before | Reads after | Candidate bytes | Checker |
|---|---|---:|---:|---:|---|
| 1 | implement → PROGRAM.md | 9 | 8 | 32 | All terms check. |
| 2 | prove → PROVE.md | 8 | 7 | 55 | All terms check. |
| 3 | diagnose → diagnostics.json | 7 | 6 | 89 | All terms check. |

All task content is preserved. These rounds demonstrate admission and actual
lookup-read reduction relative to the declared fallback. They are constructed,
public tasks, not held-out agent trials. Existing `guide program` already reads
its known pack directly; the experiment does not claim superiority over that
command. A fresh-agent productivity claim remains unresolved.

The demonstration's `--promote` mode installs only its own three bounded,
predefined candidates, checks that accepted bytes still match the baseline, and
atomically replaces routes.json with the exact evaluated bytes. It refuses to
restart on a nonempty accepted table. It assumes exclusive execution; the
compare-then-replace sequence is not a concurrent compare-and-swap primitive.

## Rejections and stopping

The checker rejects unchanged data, a regression to the empty table, and a table
that sends implement to the proof pack. Schema validation rejects path escape,
unknown tasks, duplicate task keys and oversized input. Rejections do not replace
accepted routes. A separate test refuses an altered checker source.

Every task now takes two reads in this representation. There is no admitted next
round: adding more bytes, renaming a task, or resetting the baseline does not
establish a gain. A different metric, representation or workload is a new contract.

## Reproduce or evaluate

```sh
python3 accretion/run.py --bend-root /path/to/pinned/bend --bun /path/to/bun
python3 tests/accretion.py /path/to/pinned/bend /path/to/bun
python3 accretion/run.py --bend-root /path/to/pinned/bend --bun /path/to/bun --candidate candidate.json
```

The first command reproduces rounds in temporary state without changing accepted
routes. Candidate mode compares external JSON against current accepted state,
prints its evidence and checker verdict, and exits nonzero on rejection. It is
review-only; it refuses `--promote`. Arbitrary candidate promotion awaits the
separate authority boundary described above.

Reports contain exact hashes, commands, per-task reads and checker output.
Temporary book paths expire after evaluation; the fixed inputs and evidence
values are sufficient to regenerate them. No timing or GPU claim is made.

The [frozen sum example](../examples/frozen-spec-twin/) is a separate
source-level spec-twin demonstration. It does not serve as the environment
evaluator.
