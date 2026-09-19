# Start here

```sh
python3 control.py status
python3 control.py next
```

The first command reports established state. The second identifies the next
ready task and its smallest working set. Read `control.py explain TASK` before
acting. If a task is already RUNNING, continue or release it before starting
another. A roadmap item is not evidence that its implementation exists.

## Working sequence

1. Read status and save its head hash.
2. Inspect the task contract and listed files. Check its reopen condition and
   available capabilities. `doctor --target PATH` checks a Bend checkout.
3. State one hypothesis or concrete deliverable. Choose the smallest useful probe.
4. Record RUNNING with a stable request ID and the observed head.
5. Make the scoped change and run `verify TASK --run-id UNIQUE_ID`.
6. Inspect the retained evidence. Record SOLVED only if it establishes the task's
   acceptance criterion. Verification alone does not change task state.
7. Read the next action. Preserve a failure's reason and reopen condition if blocked.

All commands above use the prefix `python3 control.py`. For exact flags, run
`python3 control.py --help` or the subcommand's `--help`.

```sh
python3 control.py transition A01 RUNNING --request start-A01 --head HEAD_HASH --reason 'Inspect contract validation'
python3 control.py verify A01 --run-id A01-check-1
python3 control.py transition A01 SOLVED --request finish-A01 --head NEW_HEAD_HASH --reason 'Acceptance checks passed' --evidence evidence/agent-system/runs/A01-check-1.json
```

The example IDs are illustrative. Read current state; do not replay the example
against an already completed task. A retry uses the same request ID and exact
payload. A revised decision uses a new request ID. A stale-head error requires
reading state again, not repeatedly forcing the previous decision.

## Read less

`changes --since HEAD_HASH --limit 20` returns a bounded delta and a continuation
cursor. `status --full` exposes all tasks when the compact packet's attention
count exceeds the eight displayed items. `explain TASK` gives the contract.
`metrics` gives units, collection methods, and 30-day and 90-day targets.

Route Bend questions through `guide/agent/ROUTER.md`. The control design is in
`docs/agent-system-design.md`; the implementation checklist is in
`docs/agent-system-plan.md`; future work is detailed in `docs/agent-roadmap.md`.

## Trust and stopping

The trusted operator owns this local interface. Hashes detect accidental drift;
they do not authenticate a hostile worker. No external worker, paid model
session, signing service, or automatic merge is active.

Stop a line of investigation when another observation cannot change the action
within the declared scope. Stop execution when its budget expires. Mark missing
evidence as unresolved. Reopen solved work when its source or evidence changes.
Never interpret STALE as a historical failure: it means the old evidence no
longer establishes the current state.
