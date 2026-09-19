# Backlog implementation receipts

The immutable proposal is `TODO_100.md`, digest
`029cce7396b70398091b6d6238a310ca5ab3922ca07aeaec4acc9fa4f5524f6d`.
Its unchecked boxes preserve the original proposal. This separate ledger records
implementation and verification; it does not activate a new Bend contract.

## First implementation group

Four tasks have implemented changes and passing local acceptance checks. Hosted
CI execution is not included in this evidence. The other 96 tasks remain open,
subject to their declared review and infrastructure prerequisites.

| Task | Implemented source | Acceptance evidence | Remaining limit |
|---|---|---|---|
| T001 | [8e9d0cb](https://github.com/rfreel/b3nd12/commit/8e9d0cb964baca310fc910b080a8ad11c4d4f978) | Regression failed before repair; full pinned-tree mode checks refuse theory/README executable additions and main executable removal under `core.filemode=false`; restored baseline passes | Exclusive checkout access; staged non-theory content policy is separate work |
| T041 | [15f83d1](https://github.com/rfreel/b3nd12/commit/15f83d15070b3e2c31eccb92656a64107de55bb4) | Regression failed before repair; global help works before/after every command in both formats, preserves literal operands and leaves real target state untouched | `--version` remains a command alias; format conflicts remain errors |
| T005 | [e341288](https://github.com/rfreel/b3nd12/commit/e34128890a7c2b42a86eb782e961eb1ee05ffc86) | Regression created a forbidden path before repair; root, absolute, relative, nested and symlink-alias destinations are now refused before writes; external replay passes | Physical path check under cooperative execution, not protection against concurrent filesystem replacement |
| T081 | [a547a58](https://github.com/rfreel/b3nd12/commit/a547a58bbb3b0b5322225117125a83ea65460e2c) | Five real suites pass locally; exact workflow block propagates each of five injected failures and stops later suites | Failure injection uses executable doubles; hosted Actions result remains unverified |

Four implementation workers owned disjoint source/test files. Two separate
review assignments examined the finished diffs and found no blocking defects.
The coordinator then executed the integrated checks below. These reviewers share
the workspace and are not separate security principals.

## Integrated verification

Executed from the repository root. All commands exited 0:

```sh
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/patch_stack.py ../bend-pinned
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/cli.py ../bend-pinned
PATH=/workspace/scratch/907925b1ae78/tooling/node_modules/@oven/bun-linux-x64/bin:$PATH python3 tests/bend_contracts.py ../bend-pinned
python3 tests/accretion.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python3 tests/program.py ../bend-pinned ../tooling/node_modules/@oven/bun-linux-x64/bin/bun
python3 tests/backlog.py
python3 tests/ci_contract.py
python3 -m py_compile b3nd12.py stack.py accretion/program.py tests/cli.py tests/patch_stack.py tests/program.py tests/ci_contract.py tests/backlog.py
git diff --check
```

The patch suite still demonstrates both ordered installation paths matching all
25 expected files. The Bend suite still exercises the installed router, packs,
diagnostics, graph, proof import guard, proof, interpreter and emitted JavaScript.
The experiment suites preserve the original finite law and acceptance behavior.
No patch, overlay, frozen contract, accepted routing table, frozen sum file or
protected checker source changed.

## Remaining work

T002 and T008 are the next local acceptance-integrity candidates: distinguish
checker malfunction from a valid refusal, then independently verify evidence
receipts against a retained terminal digest. They remain unimplemented here.
Runtime identity approval, isolated principals, concurrent promotion and actual
fresh-agent studies retain their separate prerequisites.

No native/GPU performance, general agent productivity or parallel-review speedup
is claimed. The earlier `PARALLEL_TEST.md` records findings at its stated baseline;
the T001 and T041 defects it describes are repaired by the commits above. T100
remains blocked until every prerequisite has an accepted completion receipt.
